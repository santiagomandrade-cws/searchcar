import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import ConfiguracaoBusca

router = APIRouter(prefix="/configs", tags=["configs"])


class ConfigInput(BaseModel):
    nome: str
    marca: str
    modelo: str
    ano_min: int | None = None
    ano_max: int | None = None
    regiao: str | None = None
    preco_max: float | None = None
    km_max: int | None = None
    cores_preferidas: list[str] = []
    horas_max_anuncio: int | None = None
    preco_fipe: float | None = None
    peso_fipe: int = 10
    peso_km: int = 5
    peso_tempo: int = 5
    peso_cor: int = 3
    fontes: str = "webmotors,olx,icarros,mercadolivre"


@router.get("")
async def listar_configs(db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(ConfiguracaoBusca).where(ConfiguracaoBusca.ativa == True))
    return [_to_dict(c) for c in r.scalars().all()]


@router.post("")
async def criar_config(data: ConfigInput, db: AsyncSession = Depends(get_db)):
    config = ConfiguracaoBusca(**_from_input(data))
    db.add(config)
    await db.commit()
    await db.refresh(config)
    return _to_dict(config)


@router.put("/{config_id}")
async def atualizar_config(config_id: int, data: ConfigInput, db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(ConfiguracaoBusca).where(ConfiguracaoBusca.id == config_id))
    config = r.scalar_one_or_none()
    if not config:
        raise HTTPException(404, "Configuração não encontrada")
    for k, v in _from_input(data).items():
        setattr(config, k, v)
    await db.commit()
    await db.refresh(config)
    return _to_dict(config)


@router.delete("/{config_id}")
async def deletar_config(config_id: int, db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(ConfiguracaoBusca).where(ConfiguracaoBusca.id == config_id))
    config = r.scalar_one_or_none()
    if not config:
        raise HTTPException(404, "Configuração não encontrada")
    config.ativa = False
    await db.commit()
    return {"ok": True}


def _from_input(data: ConfigInput) -> dict:
    d = data.model_dump()
    d["cores_preferidas"] = json.dumps(d["cores_preferidas"]) if d["cores_preferidas"] else None
    return d


def _to_dict(c: ConfiguracaoBusca) -> dict:
    return {
        "id": c.id,
        "nome": c.nome,
        "marca": c.marca,
        "modelo": c.modelo,
        "ano_min": c.ano_min,
        "ano_max": c.ano_max,
        "regiao": c.regiao,
        "preco_max": c.preco_max,
        "km_max": c.km_max,
        "cores_preferidas": c.cores_lista(),
        "horas_max_anuncio": c.horas_max_anuncio,
        "preco_fipe": c.preco_fipe,
        "peso_fipe": c.peso_fipe,
        "peso_km": c.peso_km,
        "peso_tempo": c.peso_tempo,
        "peso_cor": c.peso_cor,
        "fontes": c.fontes,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }
