import httpx
import json
import re
from datetime import datetime
from scrapers.base import BaseScraper, CarListing

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9",
}

_ESTADOS = {
    "AC": "acre", "AL": "alagoas", "AP": "amapa", "AM": "amazonas", "BA": "bahia",
    "CE": "ceara", "DF": "distritofederal", "ES": "espiritosanto", "GO": "goias",
    "MA": "maranhao", "MT": "matogrosso", "MS": "matogrossodosul", "MG": "minasgerais",
    "PA": "para", "PB": "paraiba", "PR": "parana", "PE": "pernambuco", "PI": "piaui",
    "RJ": "riodejaneiro", "RN": "riograndedonorte", "RS": "riograndedosul",
    "RO": "rondonia", "RR": "roraima", "SC": "santacatarina", "SP": "saopaulo",
    "SE": "sergipe", "TO": "tocantins",
}

_BASE = "https://www.olx.com.br/autos-e-pecas/carros-vans-e-utilitarios"


class OLXScraper(BaseScraper):
    async def buscar(self) -> list[CarListing]:
        query = f"{self.marca} {self.modelo}".strip()
        uf = (self.regiao or "").upper()
        url = f"{_BASE}/estado-{_ESTADOS[uf]}" if uf in _ESTADOS else _BASE

        params: dict = {"q": query}
        if self.preco_max:
            params["pe"] = int(self.preco_max)

        async with httpx.AsyncClient(timeout=25, headers=_HEADERS, follow_redirects=True) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            html = r.text

        m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.DOTALL)
        if not m:
            return []

        try:
            data = json.loads(m.group(1))
        except json.JSONDecodeError:
            return []

        ads = data.get("props", {}).get("pageProps", {}).get("ads", [])
        results = []

        for ad in ads[:24]:
            try:
                preco = _preco(str(ad.get("price", "") or ""))
                if self.preco_max and preco and preco > self.preco_max:
                    continue

                props = {p.get("name", ""): p.get("value", "") for p in ad.get("properties", [])}
                km = _int(props.get("mileage") or props.get("km") or "")
                if self.km_max and km and km > self.km_max:
                    continue

                ano = _int(props.get("regdate") or props.get("ano") or "")
                if self.ano_min and ano and ano < self.ano_min:
                    continue
                if self.ano_max and ano and ano > self.ano_max:
                    continue

                loc = ad.get("locationDetails") or {}
                cidade = loc.get("municipality") or loc.get("city")
                estado = loc.get("uf") or loc.get("state")

                imgs = ad.get("images") or []
                imagem = None
                if imgs:
                    imagem = imgs[0] if isinstance(imgs[0], str) else imgs[0].get("original")

                pub = None
                raw = ad.get("listTime") or ad.get("date")
                if raw:
                    try:
                        pub = datetime.fromtimestamp(int(raw))
                    except (ValueError, TypeError):
                        pass

                results.append(CarListing(
                    titulo=ad.get("title", ""),
                    preco=preco,
                    ano=ano,
                    marca=self.marca,
                    modelo=self.modelo,
                    km=km,
                    cor=props.get("colour") or props.get("cor"),
                    cidade=cidade,
                    estado=estado,
                    url=ad.get("url", ""),
                    fonte="OLX",
                    imagem=imagem,
                    publicado_em=pub,
                ))
            except Exception:
                continue

        return results


def _preco(s: str) -> float | None:
    try:
        return float(s.replace("R$", "").replace(".", "").replace(",", ".").strip())
    except (ValueError, AttributeError):
        return None


def _int(s) -> int | None:
    if not s:
        return None
    d = "".join(filter(str.isdigit, str(s)))
    return int(d) if d else None
