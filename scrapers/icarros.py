import httpx
from bs4 import BeautifulSoup
from .base import BaseScraper, CarListing


class ICarrosScraper(BaseScraper):
    BASE_URL = "https://www.icarros.com.br/ache/listaanuncios.jsp"

    async def buscar(self) -> list[CarListing]:
        params = {"sop": "lis_99-ord_1-pag_1"}
        if self.marca:
            params["marca"] = self.marca
        if self.modelo:
            params["modelo"] = self.modelo
        if self.preco_max:
            params["precoate"] = int(self.preco_max)
        if self.ano_min:
            params["anofab"] = self.ano_min

        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            resp = await client.get(self.BASE_URL, params=params, headers=headers)
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        resultados = []

        for card in soup.select("li.anuncio")[:20]:
            try:
                titulo_el = card.select_one("h2") or card.select_one(".titulo")
                preco_el = card.select_one(".preco") or card.select_one("[class*='preco']")
                link_el = card.select_one("a[href]")
                img_el = card.select_one("img[src]")
                km_el = card.select_one(".km") or card.select_one("[class*='km']")
                local_el = card.select_one(".cidade") or card.select_one("[class*='cidade']")

                titulo = titulo_el.get_text(strip=True) if titulo_el else "—"
                preco_txt = preco_el.get_text(strip=True).replace("R$", "").replace(".", "").replace(",", ".").strip() if preco_el else None
                preco = float(preco_txt) if preco_txt and preco_txt.replace(".", "").isdigit() else None
                km_txt = km_el.get_text(strip=True).replace(".", "").replace("km", "").strip() if km_el else None
                km = int(km_txt) if km_txt and km_txt.isdigit() else None
                url = link_el["href"] if link_el else ""
                if url and not url.startswith("http"):
                    url = "https://www.icarros.com.br" + url

                resultados.append(CarListing(
                    titulo=titulo,
                    preco=preco,
                    ano=None,
                    marca=self.marca,
                    modelo=self.modelo,
                    km=km,
                    cidade=local_el.get_text(strip=True) if local_el else None,
                    url=url,
                    fonte="iCarros",
                    imagem=img_el["src"] if img_el else None,
                ))
            except Exception:
                continue

        return resultados
