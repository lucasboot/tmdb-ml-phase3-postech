# Como Obter Credenciais do TMDB

## Opção 1: API Key v3 (Recomendado)

1. Acesse: https://www.themoviedb.org/settings/api
2. Faça login (ou crie uma conta gratuita)
3. Clique em "Request an API Key"
4. Preencha o formulário (pode usar dados de teste)
5. Copie a **API Key (v3 auth)** - será algo como: `986cf68636f510a990bb3355085ac547`
6. Cole no arquivo `.env`:

```bash
TMDB_API_KEY=986cf68636f510a990bb3355085ac547
```

## Opção 2: Bearer Token v4

1. Acesse: https://www.themoviedb.org/settings/api
2. Copie o **API Read Access Token (v4 auth)** - será um JWT longo começando com `eyJhbGci...`
3. Cole no arquivo `.env`:

```bash
TMDB_API_KEY=eyJhbGciOiJIUzI1NiJ9...
```

## Verificar se está funcionando

Após configurar, reinicie os containers:

```bash
docker compose restart worker beat
```

Verifique os logs:
```bash
docker compose logs -f worker
```

Você deve ver a task rodando sem erros 401.
