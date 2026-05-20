import httpx

FIPE_BASE = "https://parallelum.com.br/fipe/api/v1/carros"

_cache: dict = {}


async def buscar_preco_fipe(marca: str, modelo: str, ano: int | None = None) -> float | None:
    key = f"{marca}|{modelo}|{ano}"
    if key in _cache:
        return _cache[key]

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{FIPE_BASE}/marcas")
            if r.status_code != 200:
                return None
            marca_id = _match(r.json(), marca)
            if not marca_id:
                return None

            r = await client.get(f"{FIPE_BASE}/marcas/{marca_id}/modelos")
            if r.status_code != 200:
                return None
            modelo_id = _match(r.json().get("modelos", []), modelo)
            if not modelo_id:
                return None

            r = await client.get(f"{FIPE_BASE}/marcas/{marca_id}/modelos/{modelo_id}/anos")
            if r.status_code != 200:
                return None
            ano_codigo = _match_ano(r.json(), ano)
            if not ano_codigo:
                return None

            r = await client.get(f"{FIPE_BASE}/marcas/{marca_id}/modelos/{modelo_id}/anos/{ano_codigo}")
            if r.status_code != 200:
                return None

            preco = _parse_preco(r.json().get("Valor", ""))
            _cache[key] = preco
            return preco
    except Exception:
        return None


def _match(items: list, nome: str) -> str | None:
    alvo = nome.lower().strip()
    for item in items:
        item_nome = item.get("nome", "").lower()
        if alvo == item_nome or alvo in item_nome or item_nome in alvo:
            return str(item.get("codigo", ""))
    return None


def _match_ano(anos: list, alvo: int | None) -> str | None:
    if not anos:
        return None
    if not alvo:
        return anos[0]["codigo"]
    for a in anos:
        try:
            if int(a["codigo"].split("-")[0]) == alvo:
                return a["codigo"]
        except (ValueError, IndexError):
            pass
    return anos[0]["codigo"]


def _parse_preco(s: str) -> float | None:
    try:
        return float(s.replace("R$", "").replace(".", "").replace(",", ".").strip())
    except (ValueError, AttributeError):
        return None
