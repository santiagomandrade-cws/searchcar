import httpx
from datetime import datetime
from scrapers.base import BaseScraper, CarListing

ML_API = "https://api.mercadolibre.com/sites/MLB/search"
ML_CATEGORY = "MLB1744"  # Carros e Caminhonetes

_ESTADOS = {
    "AC": "BR-AC", "AL": "BR-AL", "AP": "BR-AP", "AM": "BR-AM", "BA": "BR-BA",
    "CE": "BR-CE", "DF": "BR-DF", "ES": "BR-ES", "GO": "BR-GO", "MA": "BR-MA",
    "MT": "BR-MT", "MS": "BR-MS", "MG": "BR-MG", "PA": "BR-PA", "PB": "BR-PB",
    "PR": "BR-PR", "PE": "BR-PE", "PI": "BR-PI", "RJ": "BR-RJ", "RN": "BR-RN",
    "RS": "BR-RS", "RO": "BR-RO", "RR": "BR-RR", "SC": "BR-SC", "SP": "BR-SP",
    "SE": "BR-SE", "TO": "BR-TO",
}


class MercadoLivreScraper(BaseScraper):
    async def buscar(self) -> list[CarListing]:
        query = f"{self.marca} {self.modelo}".strip()
        params: dict = {"category": ML_CATEGORY, "q": query, "limit": 48}

        if self.preco_max:
            params["price"] = f"*-{int(self.preco_max)}"
        if self.regiao and self.regiao.upper() in _ESTADOS:
            params["state"] = _ESTADOS[self.regiao.upper()]

        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(ML_API, params=params)
            r.raise_for_status()
            data = r.json()

        results = []
        for item in data.get("results", []):
            attrs = {a["id"]: a.get("value_name") for a in item.get("attributes", [])}

            km = _int(attrs.get("VEHICLE_MILEAGE"))
            if self.km_max and km and km > self.km_max:
                continue

            ano = _int(attrs.get("VEHICLE_YEAR"))
            if self.ano_min and ano and ano < self.ano_min:
                continue
            if self.ano_max and ano and ano > self.ano_max:
                continue

            addr = item.get("seller_address", {})
            cidade = addr.get("city", {}).get("name")
            estado = addr.get("state", {}).get("id", "").replace("BR-", "") or None
            thumb = (item.get("thumbnail") or "").replace("http://", "https://")

            results.append(CarListing(
                titulo=item.get("title", ""),
                preco=item.get("price"),
                ano=ano,
                marca=self.marca,
                modelo=self.modelo,
                km=km,
                cor=attrs.get("COLOR"),
                cidade=cidade,
                estado=estado,
                url=item.get("permalink", ""),
                fonte="MercadoLivre",
                imagem=thumb or None,
                publicado_em=_date(item.get("date_created")),
            ))

        return results


def _int(s) -> int | None:
    if s is None:
        return None
    try:
        return int("".join(filter(str.isdigit, str(s))))
    except ValueError:
        return None


def _date(s) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).replace(tzinfo=None)
    except (ValueError, AttributeError):
        return None
