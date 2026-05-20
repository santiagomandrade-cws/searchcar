import httpx
from scrapers.base import BaseScraper, CarListing

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.webmotors.com.br/carros/estoque",
    "Origin": "https://www.webmotors.com.br",
}


class WebMotorsScraper(BaseScraper):
    _API = "https://www.webmotors.com.br/api/search/car"

    async def buscar(self) -> list[CarListing]:
        partes = ["carros", "estoque"]
        if self.marca:
            partes.append(self.marca.lower().replace(" ", "-"))
        if self.modelo:
            partes.append(self.modelo.lower().replace(" ", "-"))
        search_url = "https://www.webmotors.com.br/" + "/".join(partes) + "/"

        params: dict = {
            "url": search_url,
            "actualPage": 1,
            "displayPerPage": 24,
            "order": 1,
            "showMenu": "true",
            "showCount": "true",
            "showBreadCrumb": "true",
            "testAB": "false",
            "returnFacets": "false",
        }
        if self.preco_max:
            params["priceMax"] = int(self.preco_max)
        if self.ano_min:
            params["yearMin"] = self.ano_min
        if self.ano_max:
            params["yearMax"] = self.ano_max
        if self.km_max:
            params["mileageMax"] = self.km_max
        if self.regiao:
            params["state"] = self.regiao.upper()

        async with httpx.AsyncClient(timeout=20, headers=_HEADERS, follow_redirects=True) as client:
            r = await client.get(self._API, params=params)
            r.raise_for_status()
            data = r.json()

        results = []
        for item in data.get("SearchResults", []):
            spec = item.get("Specification", {})
            preco = item.get("Prices", {}).get("Price")
            km = spec.get("Mileage")
            ano = spec.get("YearFabrication")

            if self.preco_max and preco and preco > self.preco_max:
                continue
            if self.km_max and km and km > self.km_max:
                continue
            if self.ano_min and ano and ano < self.ano_min:
                continue
            if self.ano_max and ano and ano > self.ano_max:
                continue

            imgs = item.get("Images", [])
            imagem = imgs[0].get("Link") if imgs else None
            uid = item.get("UniqueId", "")
            url = f"https://www.webmotors.com.br/comprar/{uid}" if uid else ""

            results.append(CarListing(
                titulo=spec.get("Title", ""),
                preco=preco,
                ano=ano,
                marca=self.marca,
                modelo=self.modelo,
                km=km,
                cor=spec.get("Color"),
                cidade=item.get("City"),
                estado=item.get("State"),
                url=url,
                fonte="WebMotors",
                imagem=imagem,
                publicado_em=None,
            ))

        return results
