# Como fazer o deploy do SearchCar

## 1. Supabase (banco de dados grátis)

1. Acesse https://supabase.com e crie uma conta
2. Clique em **New Project**
3. Escolha nome, região (South America - São Paulo) e senha do banco
4. Aguarde o projeto inicializar (~2 min)
5. Vá em **Settings → Database → Connection string**
6. Selecione **Session mode** e copie a URL
7. Cole no arquivo `.env` na raiz do projeto:
   ```
   DATABASE_URL=postgresql://postgres.[PROJECT]:[PASSWORD]@aws-0-sa-east-1.pooler.supabase.com:5432/postgres
   ```

As tabelas são criadas **automaticamente** na primeira vez que o app iniciar.

---

## 2. GitHub (repositório grátis)

```bash
git remote add origin https://github.com/SEU_USUARIO/SearchCar.git
git branch -M main
git push -u origin main
```

---

## 3. Railway (hospedagem grátis)

1. Acesse https://railway.app
2. Clique em **New Project → Deploy from GitHub repo**
3. Selecione o repositório SearchCar
4. Railway detecta automaticamente o `railway.toml`
5. Vá em **Variables** e adicione:
   - `DATABASE_URL` = (a string de conexão do Supabase)
6. Aguarde o deploy (~3 min)
7. Clique em **Settings → Networking → Generate Domain**
8. Acesse pelo domínio gerado — funciona no celular e no notebook

---

## Fluxo de uso

1. Acesse a URL do Railway no celular ou notebook
2. Tab **Config** → **+** → crie uma busca (ex: HB20, SP, km até 80k)
3. Tab **Buscar** → toque em **Executar busca**
4. Tab **Resultados** → carros ordenados por score ⭐
5. Toque em ☆ para favoritar os melhores

## Pontuação (score 0–100)

Cada anúncio recebe uma nota baseada nos pesos que você configurou:
- **💰 Desconto FIPE**: quanto mais barato que a tabela, mais pontos
- **🛣️ KM baixa**: quilometragem abaixo do limite definido
- **🕐 Publicado recentemente**: quanto mais novo o anúncio, mais pontos
- **🎨 Cor preferida**: match com as cores selecionadas
