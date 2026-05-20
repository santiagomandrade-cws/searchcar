import httpx
from bs4 import BeautifulSoup
from .base import BaseScraper, CarListing


class MercadoLivreScraper(BaseScraper):
    BASE_URL = "https://carros.mercadolivre.com.br"

    async def buscar(self) -> list[CarListing]:
        query = f"{self.marca} {self.modelo}".strip()
        url = f"{self.BASE_URL}/{query.replace(' ', '-').lower()}_Desde_1_NoIndex_True"

        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        resultados = []

        for card in soup.select("li.ui-search-layout__item")[:20]:
            try:
                titulo_el = card.select_one("h2") or card.select_one(".ui-search-item__title")
                preco_el = card.select_one(".price-tag-amount") or card.select_one("[class*='price']")
                link_el = card.select_one("a[href]")
                img_el = card.select_one("img[src]") or card.select_one("img[data-src]")
                local_el = card.select_one(".ui-search-item__location")

                titulo = titulo_el.get_text(strip=True) if titulo_el else "—"
                preco_txt = preco_el.get_text(strip=True).replace("R$", "").replace(".", "").replace(",", ".").strip() if preco_el else None
                preco = float(preco_txt) if preco_txt and preco_txt.replace(".", "").isdigit() else None
                img_src = img_el.get("src") or img_el.get("data-src") if img_el else None

                resultados.append(CarListing(
                    titulo=titulo,
                    preco=preco,
                    ano=None,
                    marca=self.marca,
                    modelo=self.modelo,
                    km=None,
                    cidade=local_el.get_text(strip=True) if local_el else None,
                    url=link_el["href"] if link_el else "",
                    fonte="MercadoLivre",
                    imagem=img_src,
                ))
            except Exception:
                continue

        return resultados
