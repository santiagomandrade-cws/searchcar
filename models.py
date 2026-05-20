import json
from datetime import datetime
from sqlalchemy import String, Float, Integer, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


class ConfiguracaoBusca(Base):
    __tablename__ = "configuracoes_busca"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(100))
    marca: Mapped[str] = mapped_column(String(50))
    modelo: Mapped[str] = mapped_column(String(100))
    ano_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ano_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    regiao: Mapped[str | None] = mapped_column(String(10), nullable=True)
    preco_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    km_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cores_preferidas: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list
    horas_max_anuncio: Mapped[int | None] = mapped_column(Integer, nullable=True)
    preco_fipe: Mapped[float | None] = mapped_column(Float, nullable=True)
    peso_fipe: Mapped[int] = mapped_column(Integer, default=10)
    peso_km: Mapped[int] = mapped_column(Integer, default=5)
    peso_tempo: Mapped[int] = mapped_column(Integer, default=5)
    peso_cor: Mapped[int] = mapped_column(Integer, default=3)
    fontes: Mapped[str] = mapped_column(String(100), default="webmotors,olx,icarros,mercadolivre")
    ativa: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def cores_lista(self) -> list[str]:
        if not self.cores_preferidas:
            return []
        try:
            return json.loads(self.cores_preferidas)
        except Exception:
            return []


class Anuncio(Base):
    __tablename__ = "anuncios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    busca_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    titulo: Mapped[str] = mapped_column(String(200))
    preco: Mapped[float | None] = mapped_column(Float, nullable=True)
    ano: Mapped[int | None] = mapped_column(Integer, nullable=True)
    marca: Mapped[str] = mapped_column(String(50))
    modelo: Mapped[str] = mapped_column(String(100))
    km: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cor: Mapped[str | None] = mapped_column(String(50), nullable=True)
    cidade: Mapped[str | None] = mapped_column(String(100), nullable=True)
    estado: Mapped[str | None] = mapped_column(String(10), nullable=True)
    url: Mapped[str] = mapped_column(Text)
    fonte: Mapped[str] = mapped_column(String(30))
    imagem: Mapped[str | None] = mapped_column(Text, nullable=True)
    publicado_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    preco_fipe: Mapped[float | None] = mapped_column(Float, nullable=True)
    desconto_fipe_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    favorito: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
