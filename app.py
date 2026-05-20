import asyncio
import json
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from scrapers.webmotors import WebMotorsScraper
from scrapers.olx import OLXScraper
from scrapers.icarros import ICarrosScraper
from scrapers.mercadolivre import MercadoLivreScraper

app = FastAPI(title="SearchCar")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/buscar")
async def buscar(
    marca: str = Query(""),
    modelo: str = Query(""),
    ano_min: int = Query(None),
    ano_max: int = Query(None),
    preco_max: float = Query(None),
    fontes: str = Query("webmotors,olx,icarros,mercadolivre"),
):
    fontes_selecionadas = [f.strip().lower() for f in fontes.split(",")]

    scrapers = []
    kwargs = dict(marca=marca, modelo=modelo, ano_min=ano_min, ano_max=ano_max, preco_max=preco_max)

    if "webmotors" in fontes_selecionadas:
        scrapers.append(WebMotorsScraper(**kwargs))
    if "olx" in fontes_selecionadas:
        scrapers.append(OLXScraper(**kwargs))
    if "icarros" in fontes_selecionadas:
        scrapers.append(ICarrosScraper(**kwargs))
    if "mercadolivre" in fontes_selecionadas:
        scrapers.append(MercadoLivreScraper(**kwargs))

    resultados_brutos = await asyncio.gather(*[s.buscar() for s in scrapers], return_exceptions=True)

    todos = []
    erros = []
    for i, resultado in enumerate(resultados_brutos):
        fonte = scrapers[i].__class__.__name__.replace("Scraper", "")
        if isinstance(resultado, Exception):
            erros.append({"fonte": fonte, "erro": str(resultado)})
        else:
            todos.extend([vars(r) for r in resultado])

    # Ordenar por preço
    todos.sort(key=lambda x: x.get("preco") or float("inf"))

    # Salvar resultado
    arquivo = DATA_DIR / f"busca_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    arquivo.write_text(json.dumps({"parametros": dict(marca=marca, modelo=modelo), "resultados": todos}, ensure_ascii=False, indent=2), encoding="utf-8")

    return JSONResponse({"resultados": todos, "total": len(todos), "erros": erros})


@app.get("/historico")
async def historico():
    arquivos = sorted(DATA_DIR.glob("busca_*.json"), reverse=True)[:10]
    historico = []
    for arq in arquivos:
        data = json.loads(arq.read_text(encoding="utf-8"))
        historico.append({
            "arquivo": arq.name,
            "parametros": data.get("parametros", {}),
            "total": len(data.get("resultados", [])),
        })
    return JSONResponse(historico)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
