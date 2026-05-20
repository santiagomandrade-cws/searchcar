import asyncio
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from database import get_db
from models import ConfiguracaoBusca, Anuncio
from scrapers.mercadolivre import MercadoLivreScraper
from scrapers.olx import OLXScraper
from scrapers.icarros import ICarrosScraper
from scrapers.webmotors import WebMotorsScraper
from services.fipe import buscar_preco_fipe
from services.scoring import calcular_score

router = APIRouter(prefix="/busca", tags=["busca"])

SCRAPERS = {
    "mercadolivre": MercadoLivreScraper,
    "olx": OLXScraper,
    "icarros": ICarrosScraper,
    "webmotors": WebMotorsScraper,
}


@router.post("/executar/{busca_id}")
async def executar_busca(busca_id: int, db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(ConfiguracaoBusca).where(ConfiguracaoBusca.id == busca_id))
    config = r.scalar_one_or_none()
    if not config:
        raise HTTPException(404, "Configuração não encontrada")

    fontes = [f.strip() for f in config.fontes.split(",")]
    kwargs = dict(
        marca=config.marca,
        modelo=config.modelo,
        ano_min=config.ano_min,
        ano_max=config.ano_max,
        preco_max=config.preco_max,
        km_max=config.km_max,
        regiao=config.regiao,
    )

    scrapers = [SCRAPERS[f](**kwargs) for f in fontes if f in SCRAPERS]
    tarefas = [asyncio.wait_for(s.buscar(), timeout=25) for s in scrapers]
    brutos = await asyncio.gather(*tarefas, return_exceptions=True)

    erros = []
    listings = []
    for i, res in enumerate(brutos):
        nome = scrapers[i].__class__.__name__.replace("Scraper", "")
        if isinstance(res, Exception):
            erros.append({"fonte": nome, "erro": str(res)})
        else:
            listings.extend(res)

    cores = config.cores_lista()
    salvos = []

    for lst in listings:
        preco_fipe = config.preco_fipe or await buscar_preco_fipe(lst.marca, lst.modelo, lst.ano)
        score, desconto = calcular_score(
            preco=lst.preco,
            preco_fipe=preco_fipe,
            km=lst.km,
            km_max=config.km_max,
            publicado_em=lst.publicado_em,
            horas_max=config.horas_max_anuncio,
            cor=lst.cor,
            cores_preferidas=cores,
            peso_fipe=config.peso_fipe,
            peso_km=config.peso_km,
            peso_tempo=config.peso_tempo,
            peso_cor=config.peso_cor,
        )

        ex = await db.execute(select(Anuncio).where(Anuncio.url == lst.url))
        anuncio = ex.scalar_one_or_none()

        if anuncio:
            anuncio.preco = lst.preco
            anuncio.score = score
            anuncio.desconto_fipe_pct = desconto
            anuncio.preco_fipe = preco_fipe
            anuncio.busca_id = busca_id
        else:
            anuncio = Anuncio(
                busca_id=busca_id,
                titulo=lst.titulo,
                preco=lst.preco,
                ano=lst.ano,
                marca=lst.marca,
                modelo=lst.modelo,
                km=lst.km,
                cor=lst.cor,
                cidade=lst.cidade,
                estado=lst.estado,
                url=lst.url,
                fonte=lst.fonte,
                imagem=lst.imagem,
                publicado_em=lst.publicado_em,
                preco_fipe=preco_fipe,
                desconto_fipe_pct=desconto,
                score=score,
            )
            db.add(anuncio)

        salvos.append(anuncio)

    await db.commit()
    for a in salvos:
        await db.refresh(a)

    resultado = sorted([_to_dict(a) for a in salvos], key=lambda x: x.get("score") or 0, reverse=True)
    return {"resultados": resultado, "total": len(resultado), "erros": erros}


@router.get("/anuncios")
async def listar_anuncios(
    busca_id: int = Query(None),
    fonte: str = Query(None),
    favorito: bool = Query(None),
    score_min: float = Query(None),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Anuncio)
    if busca_id is not None:
        stmt = stmt.where(Anuncio.busca_id == busca_id)
    if fonte:
        stmt = stmt.where(Anuncio.fonte == fonte)
    if favorito is not None:
        stmt = stmt.where(Anuncio.favorito == favorito)
    if score_min is not None:
        stmt = stmt.where(Anuncio.score >= score_min)
    stmt = stmt.order_by(Anuncio.score.desc().nullslast(), Anuncio.created_at.desc())

    r = await db.execute(stmt)
    return [_to_dict(a) for a in r.scalars().all()]


@router.put("/anuncios/{anuncio_id}/favorito")
async def toggle_favorito(anuncio_id: int, db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(Anuncio).where(Anuncio.id == anuncio_id))
    anuncio = r.scalar_one_or_none()
    if not anuncio:
        raise HTTPException(404, "Anúncio não encontrado")
    anuncio.favorito = not anuncio.favorito
    await db.commit()
    return {"favorito": anuncio.favorito}


@router.delete("/anuncios")
async def limpar_anuncios(busca_id: int = Query(None), db: AsyncSession = Depends(get_db)):
    stmt = delete(Anuncio).where(Anuncio.favorito == False)
    if busca_id is not None:
        stmt = stmt.where(Anuncio.busca_id == busca_id)
    await db.execute(stmt)
    await db.commit()
    return {"ok": True}


@router.get("/fipe")
async def consultar_fipe(marca: str, modelo: str, ano: int = Query(None)):
    preco = await buscar_preco_fipe(marca, modelo, ano)
    return {"preco_fipe": preco}


def _to_dict(a: Anuncio) -> dict:
    return {
        "id": a.id,
        "busca_id": a.busca_id,
        "titulo": a.titulo,
        "preco": a.preco,
        "ano": a.ano,
        "marca": a.marca,
        "modelo": a.modelo,
        "km": a.km,
        "cor": a.cor,
        "cidade": a.cidade,
        "estado": a.estado,
        "url": a.url,
        "fonte": a.fonte,
        "imagem": a.imagem,
        "publicado_em": a.publicado_em.isoformat() if a.publicado_em else None,
        "preco_fipe": a.preco_fipe,
        "desconto_fipe_pct": a.desconto_fipe_pct,
        "score": a.score,
        "favorito": a.favorito,
        "created_at": a.created_at.isoformat() if a.created_at else None,
    }
