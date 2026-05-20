from dataclasses import dataclass
from typing import Optional


@dataclass
class CarListing:
    titulo: str
    preco: Optional[float]
    ano: Optional[int]
    marca: str
    modelo: str
    km: Optional[int]
    cidade: Optional[str]
    url: str
    fonte: str
    imagem: Optional[str] = None


class BaseScraper:
    def __init__(self, marca: str = "", modelo: str = "", ano_min: int = None, ano_max: int = None, preco_max: float = None):
        self.marca = marca
        self.modelo = modelo
        self.ano_min = ano_min
        self.ano_max = ano_max
        self.preco_max = preco_max

    async def buscar(self) -> list[CarListing]:
        raise NotImplementedError
