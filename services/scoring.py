from datetime import datetime


def calcular_score(
    preco: float | None,
    preco_fipe: float | None,
    km: int | None,
    km_max: int | None,
    publicado_em: datetime | None,
    horas_max: int | None,
    cor: str | None,
    cores_preferidas: list[str],
    peso_fipe: int,
    peso_km: int,
    peso_tempo: int,
    peso_cor: int,
) -> tuple[float, float | None]:
    """Retorna (score 0-100, desconto_fipe_pct)."""
    score = 0.0
    max_score = 0.0
    desconto_fipe_pct = None

    if peso_fipe > 0 and preco and preco_fipe and preco_fipe > 0:
        desconto = (preco_fipe - preco) / preco_fipe * 100
        desconto_fipe_pct = round(desconto, 1)
        pts = min(max(desconto / 30 * 100, 0), 100)  # 30% desconto = pontuação máxima
        score += pts * peso_fipe
        max_score += 100 * peso_fipe

    if peso_km > 0 and km is not None and km_max and km_max > 0:
        pts = max((1 - km / km_max) * 100, 0) if km <= km_max else 0
        score += pts * peso_km
        max_score += 100 * peso_km

    if peso_tempo > 0 and publicado_em and horas_max and horas_max > 0:
        horas = (datetime.utcnow() - publicado_em).total_seconds() / 3600
        pts = max((1 - horas / horas_max) * 100, 0) if horas <= horas_max else 0
        score += pts * peso_tempo
        max_score += 100 * peso_tempo

    if peso_cor > 0 and cores_preferidas:
        cor_lower = (cor or "").lower()
        match = any(c.lower() in cor_lower or cor_lower in c.lower() for c in cores_preferidas if c)
        score += (100.0 if match else 0.0) * peso_cor
        max_score += 100 * peso_cor

    final = round(score / max_score * 100, 1) if max_score > 0 else 0.0
    return final, desconto_fipe_pct
