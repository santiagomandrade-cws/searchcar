import httpx
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper, CarListing

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "pt-BR,pt;q=0.9",
}

_SELECTORS_CARD = ["li.anuncio", "article.card-anuncio", "div[class*='resultado']", "li[class*='anuncio']"]
_SELECTORS_TITULO = ["h2", "h3", ".titulo", "[class*='titulo']", "[class*='title']"]
_SELECTORS_PRECO = [".preco", "[class*='preco']", "[class*='price']", "[class*='valor']"]
_SELECTORS_KM = [".km", "[class*='km']", "[class*='quilometragem']"]
_SELECTORS_LOCAL = [".cidade", "[class*='cidade']", "[class*='local']"]
_SELECTORS_ANO = [".ano", "[class*='ano']", "[class*='year']"]


class ICarrosScraper(BaseScraper):
    _URL = "https://www.icarros.com.br/ache/listaanuncios.jsp"

    async def buscar(self) -> list[CarListing]:
        params: dict = {"sop": "lis_99-ord_1-pag_1"}
        if self.marca:
            params["mar_id"] = self.marca
        if self.modelo:
            params["mod_id"] = self.modelo
        if self.preco_max:
            params["precoate"] = int(self.preco_max)
        if self.ano_min:
            params["anofab"] = self.ano_min
        if self.ano_max:
            params["anofabate"] = self.ano_max
        if self.km_max:
            params["kmate"] = self.km_max
        if self.regiao:
            params["uf"] = self.regiao.upper()

        async with httpx.AsyncClient(timeout=25, headers=_HEADERS, follow_redirects=True) as client:
            r = await client.get(self._URL, params=params)
            r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        cards = []
        for sel in _SELECTORS_CARD:
            cards = soup.select(sel)
            if cards:
                break

        results = []
        for card in cards[:24]:
            try:
                titulo = _text(card, _SELECTORS_TITULO)
                if not titulo:
                    continue

                preco = _preco(_text(card, _SELECTORS_PRECO))
                km = _int(_text(card, _SELECTORS_KM))
                ano = _int(_text(card, _SELECTORS_ANO))
                cidade = _text(card, _SELECTORS_LOCAL)

                if self.preco_max and preco and preco > self.preco_max:
                    continue
                if self.km_max and km and km > self.km_max:
                    continue
                if self.ano_min and ano and ano < self.ano_min:
                    continue
                if self.ano_max and ano and ano > self.ano_max:
                    continue

                link = card.select_one("a[href]")
                url = link.get("href", "") if link else ""
                if url and not url.startswith("http"):
                    url = "https://www.icarros.com.br" + url

                img = card.select_one("img[src], img[data-src]")
                imagem = (img.get("src") or img.get("data-src")) if img else None

                results.append(CarListing(
                    titulo=titulo,
                    preco=preco,
                    ano=ano,
                    marca=self.marca,
                    modelo=self.modelo,
                    km=km,
                    cor=None,
                    cidade=cidade,
                    estado=self.regiao,
                    url=url,
                    fonte="iCarros",
                    imagem=imagem,
                    publicado_em=None,
                ))
            except Exception:
                continue

        return results


def _text(card, selectors: list) -> str | None:
    for sel in selectors:
        el = card.select_one(sel)
        if el:
            return el.get_text(strip=True)
    return None


def _preco(s: str | None) -> float | None:
    if not s:
        return None
    try:
        return float(s.replace("R$", "").replace(".", "").replace(",", ".").replace(" ", "").strip())
    except ValueError:
        return None


def _int(s: str | None) -> int | None:
    if not s:
        return None
    d = "".join(filter(str.isdigit, s))
    return int(d) if d else None
