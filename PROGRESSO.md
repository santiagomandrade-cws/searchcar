# Progresso do SearchCar

## O que é

Aplicação pessoal para encontrar oportunidades de compra de carros para revenda. Busca anúncios em múltiplos sites, calcula um score de oportunidade e exibe ordenado pelo melhor negócio.

## Stack

- **Backend**: Python + FastAPI (async)
- **Banco**: Supabase PostgreSQL (free tier) via SQLAlchemy async + asyncpg
- **Hospedagem**: Railway
- **Repositório**: https://github.com/santiagomandrade-cws/searchcar
- **Frontend**: HTML + CSS + JS vanilla (mobile-first, sem framework, sem build step)

## Como rodar local

```bash
# 1. Configurar .env com a URL do Supabase (senha com @ deve ser %40)
# DATABASE_URL=postgresql://postgres.xxx:senha%40123@aws-1-us-east-2.pooler.supabase.com:5432/postgres

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Subir o servidor
python -m uvicorn app:app --port 8000

# 4. Acessar
# http://localhost:8000
```

## Concluído ✅

- `database.py` — conexão async Supabase, SSL configurado, tabelas criadas automaticamente no boot
- `models.py` — tabelas `configuracoes_busca` e `anuncios`
- `services/fipe.py` — consulta tabela FIPE gratuita (parallelum.com.br), cache em memória
- `services/scoring.py` — engine de score 0–100 com 4 pesos configuráveis (FIPE, KM, tempo, cor)
- `routers/config.py` — CRUD de configurações de busca
- `routers/busca.py` — executa buscas, salva no banco, endpoint FIPE, favoritos
- Scrapers: MercadoLivre (API REST), WebMotors (API interna), OLX (`__NEXT_DATA__`), iCarros (HTML)
- `templates/index.html` — SPA com 3 abas, badge de score colorido, sliders de peso, favoritos
- `railway.toml` — config de deploy automático
- `DEPLOY.md` — passo a passo completo de deploy

## Pendente 🔜

1. **Railway** — estava instável em 2026-05-19; retomar deploy quando estabilizar
   - Conectar repo GitHub no Railway → adicionar variável `DATABASE_URL`
2. **OLX bloqueando** — retorna 403 mesmo com headers de browser real
   - Próxima tentativa: API interna do app mobile OLX (sem custo extra)
   - Se falhar: manter OLX desabilitado, usar ML + WebMotors + iCarros
3. **WebMotors e iCarros** — não testados ainda
4. **MercadoLivre** — fonte principal garantida (API oficial)

## Problemas resolvidos

| Problema | Solução |
|----------|---------|
| SSL do Supabase | `ssl.create_default_context()` com `CERT_NONE` em `database.py` |
| Senha com `@` na URL | Codificar `@` como `%40` no `.env` |
| OLX retorna 403 | Headers completos de browser real; mensagem clara no front |

## Decisões importantes

- **Playwright removido** — consome 300–400MB RAM; Railway Hobby (512MB) não suporta; Railway Pro custa $20/mês
- **SQLite descartado** — Railway filesystem é efêmero; Supabase é o banco
- **Deduplicação por URL** — busca atualiza anúncio existente em vez de duplicar
- **Score FIPE** — 30% de desconto = pontuação máxima nesse critério
