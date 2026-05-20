import httpx
from bs4 import BeautifulSoup
from .base import BaseScraper, CarListing


class WebMotorsScraper(BaseScraper):
    BASE_URL = "https://www.webmotors.com.br/carros/estoque"

    async def buscar(self) -> list[CarListing]:
        params = {}
        if self.marca:
            params["marca1"] = self.marca.upper()
        if self.modelo:
            params["modelo1"] = self.modelo.upper()
        if self.ano_min:
            params["ano1"] = self.ano_min
        if self.ano_max:
            params["ano2"] = self.ano_max
        if self.preco_max:
            params["preco2"] = int(self.preco_max)

        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            resp = await client.get(self.BASE_URL, params=params, headers=headers)
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        resultados = []

        for card in soup.select("div[class*='card-advertisement']")[:20]:
            try:
                titulo_el = card.select_one("[class*='title']")
                preco_el = card.select_one("[class*='price']")
                link_el = card.select_one("a[href]")
                img_el = card.select_one("img[src]")

                titulo = titulo_el.get_text(strip=True) if titulo_el else "—"
                preco_txt = preco_el.get_text(strip=True).replace("R$", "").replace(".", "").replace(",", ".").strip() if preco_el else None
                preco = float(preco_txt) if preco_txt and preco_txt.replace(".", "").isdigit() else None
                url = link_el["href"] if link_el else ""
                if url and not url.startswith("http"):
                    url = "https://www.webmotors.com.br" + url

                resultados.append(CarListing(
                    titulo=titulo,
                    preco=preco,
                    ano=None,
                    marca=self.marca,
                    modelo=self.modelo,
                    km=None,
                    cidade=None,
                    url=url,
                    fonte="WebMotors",
                    imagem=img_el["src"] if img_el else None,
                ))
            except Exception:
                continue

        return resultados
