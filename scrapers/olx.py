import httpx
from bs4 import BeautifulSoup
from .base import BaseScraper, CarListing


class OLXScraper(BaseScraper):
    BASE_URL = "https://www.olx.com.br/autos-e-pecas/carros-vans-e-utilitarios"

    async def buscar(self) -> list[CarListing]:
        query = f"{self.marca} {self.modelo}".strip()
        params = {"q": query}
        if self.preco_max:
            params["pe"] = int(self.preco_max)

        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            resp = await client.get(self.BASE_URL, params=params, headers=headers)
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        resultados = []

        for card in soup.select("li[data-lurker-detail='main_ad']")[:20]:
            try:
                titulo_el = card.select_one("h2")
                preco_el = card.select_one("p[class*='price']") or card.select_one("[class*='Price']")
                link_el = card.select_one("a[href]")
                img_el = card.select_one("img[src]")
                local_el = card.select_one("[class*='location']") or card.select_one("p[class*='Location']")

                titulo = titulo_el.get_text(strip=True) if titulo_el else "—"
                preco_txt = preco_el.get_text(strip=True).replace("R$", "").replace(".", "").replace(",", ".").strip() if preco_el else None
                preco = float(preco_txt) if preco_txt and preco_txt.replace(".", "").isdigit() else None
                url = link_el["href"] if link_el else ""
                cidade = local_el.get_text(strip=True) if local_el else None

                resultados.append(CarListing(
                    titulo=titulo,
                    preco=preco,
                    ano=None,
                    marca=self.marca,
                    modelo=self.modelo,
                    km=None,
                    cidade=cidade,
                    url=url,
                    fonte="OLX",
                    imagem=img_el["src"] if img_el else None,
                ))
            except Exception:
                continue

        return resultados
