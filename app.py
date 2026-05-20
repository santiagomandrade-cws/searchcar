from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from database import criar_tabelas
from routers import config as config_router
from routers import busca as busca_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await criar_tabelas()
    yield


app = FastAPI(title="SearchCar", lifespan=lifespan)
templates = Jinja2Templates(directory="templates")

app.include_router(config_router.router)
app.include_router(busca_router.router)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
