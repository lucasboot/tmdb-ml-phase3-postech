# TMDB Horror Movies Predictor - Flask + Celery + PostgreSQL

Sistema de predição de popularidade e notas para filmes de terror/horror usando machine learning.

> ⚡ **Quick Start:** Veja [QUICK_START.md](QUICK_START.md) para começar rapidamente!

## 🚀 Opções de Deploy

Este projeto suporta **duas formas de execução**:

| Característica | 🌐 Nuvem (Padrão) | 🐳 Local (Dev) |
|---|---|---|
| **PostgreSQL** | Neon (gerenciado) | Docker container |
| **Redis** | Upstash (gerenciado) | Docker container |
| **Configuração** | `.env` com URLs remotas | `.env` com URLs locais |
| **Comando** | `docker compose up` | `docker compose -f docker-compose.yml -f docker-compose.local.yml up` |
| **Melhor para** | Produção, demos, acesso remoto | Desenvolvimento local, testes offline |

## Stack

- **Flask** - API REST + Dashboard web com Jinja2 e Chart.js
- **Celery + Celery Beat** - Agendamento automático de coleta diária
- **PostgreSQL** - Banco de dados relacional (Neon por padrão, ou local via Docker)
- **Redis** - Broker/backend do Celery (Upstash por padrão, ou local via Docker)
- **SQLAlchemy** - ORM para persistência
- **Scikit-learn** - Pipeline de machine learning com regressão linear para prever popularidade e notas de filmes de terror/horror

## Estrutura
```
project/
  docker-compose.yml           # Orquestração base (web, worker, beat)
  docker-compose.local.yml     # Adiciona postgres + redis locais
  env.sample                   # Template para Nuvem
  env.local.sample             # Template para Local
  run-local.sh                 # Helper para modo local
  requirements.txt             # Dependências Python
  web/
    Dockerfile
    app/
      __init__.py              # Factory do Flask
      config.py                # Configurações
      celery_app.py            # Tasks do Celery
      db.py                    # Inicialização do SQLAlchemy
      models.py                # Modelos de dados
      tmdb.py                  # Cliente TMDB API
      ml.py                    # Pipeline de ML
      routes/
        api.py                 # Endpoints da API
        dashboard.py           # Rotas do dashboard
      templates/
        base.html
        index.html
      static/
        main.js                # Chart.js + polling
```

## Setup

Este projeto oferece **duas opções de configuração**:

### Opção 1: Serviços em Nuvem (Padrão - Recomendado)

Usa **Neon** (PostgreSQL) e **Upstash** (Redis) como serviços gerenciados em nuvem. As chaves para uso estão no arquivo enviado junto do projeto.

**Vantagens:**
- ✅ Sem necessidade de rodar banco/redis localmente
- ✅ Acesso remoto de qualquer lugar
- ✅ Backups automáticos
- ✅ Alta disponibilidade

**1.1. Configurar variáveis de ambiente:**

```bash
cp env.sample .env
```

**1.2. Editar o arquivo `.env` com suas credenciais:**

```bash
TMDB_API_KEY=sua_chave_tmdb_aqui

DATABASE_URL=postgresql+psycopg2://user:pass@seu-projeto.neon.tech/neondb?sslmode=require

REDIS_URL=rediss://default:sua_senha@seu-endpoint.upstash.io:6379

FLASK_ENV=development
SECRET_KEY=dev-secret-change-in-production
POLL_INTERVAL_MS=30000
```

**Como obter as credenciais:**
- **TMDB API Key:** https://www.themoviedb.org/settings/api (v3 ou v4 Bearer Token)
- **Neon (Postgres):** https://console.neon.tech - Crie um projeto e copie a connection string
- **Upstash (Redis):** https://console.upstash.com - Crie um database Redis e copie a URL TLS

**1.3. Subir os containers:**

```bash
docker compose up --build
```

**1.4. Acessar o dashboard:**

Abra o navegador em: **http://localhost:8000/**

---

### Opção 2: Ambiente Local com Docker (Desenvolvimento)

Usa **PostgreSQL** e **Redis** rodando localmente em containers Docker.

**Vantagens:**
- ✅ Sem dependência de serviços externos
- ✅ Desenvolvimento offline
- ✅ Controle total do ambiente

**2.1. Configurar variáveis de ambiente:**

```bash
cp env.local.sample .env
```

**2.2. Editar o arquivo `.env` (já vem pré-configurado):**

```bash
TMDB_API_KEY=COLOQUE_SUA_API_KEY_OU_BEARER_TOKEN_AQUI

DATABASE_URL=postgresql+psycopg2://app:app123@postgres:5432/movies

REDIS_URL=redis://redis:6379/0

FLASK_ENV=development
SECRET_KEY=dev-secret
POLL_INTERVAL_MS=30000
```

> Apenas adicione sua chave da API do TMDB.

**2.3. Subir os containers com o compose local:**

**Opção A - Script helper (recomendado):**
```bash
./run-local.sh up --build
```

**Opção B - Comando manual:**
```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml up --build
```

Isso irá iniciar:
- PostgreSQL local (porta 5432)
- Redis local (porta 6379)
- Flask web server (porta 8000)
- Celery worker
- Celery beat (scheduler)

**2.4. Acessar o dashboard:**

Abra o navegador em: **http://localhost:8000/**

**2.5. Persistência de dados:**

Os dados ficam salvos nos volumes Docker:
- `postgres_data` - Dados do PostgreSQL
- `redis_data` - Dados do Redis

Para limpar os dados locais:
```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml down -v
```

---

### Configuração da API do TMDB

**API Key v3** (Recomendado - mais simples):
```bash
TMDB_API_KEY=986cf68636f510a990bb3355085ac547
```

---


## Endpoints da API

- `GET /health` - Health check
- `GET /api/health` - Health check da API
- `GET /api/summary` - Top 10 filmes mais populares
- `GET /api/predictions` - Top 20 predições de popularidade e nota média

## Como Funciona

1. **Coleta de Dados (diária):**
   - Celery Beat coleta filmes de terror/horror de 2010 em diante
   - ~5.000 filmes únicos do TMDB
   - Armazena em PostgreSQL

2. **Treinamento ML (a cada hora):**
   - Treina modelos de Regressão Linear (popularidade e nota)
   - Gera predições atualizadas

3. **Dashboard (atualização automática):**
   - Visualiza top 10 filmes populares
   - Compara predições vs valores reais

## Machine Learning

> 📖 **Documentação completa sobre modelos, métricas e casos de uso:** [ML_INSIGHTS.md](ML_INSIGHTS.md) ou [ARCHITECTURE.md](ARCHITECTURE.md)

O sistema usa modelos de Regressão Linear para prever popularidade e nota de filmes de terror baseado em características como:
- Duração, votos, ano/mês de lançamento
- Gêneros combinados (thriller, sci-fi, etc)
- Sazonalidade (verão, halloween, feriados)

## Primeiro Ingest de Dados

**Importante:** Se você estiver rodando tudo localmente pela primeira vez, o primeiro ingest de dados precisa ser chamado manualmente. Este processo **demora bastante** (1-2 horas), pois coleta ~5.000 filmes de terror desde 2010:

```bash
docker compose exec worker celery -A web.app.celery_app call app.celery_app.task_initial_ingest
```

Após isso, as coletas serão automáticas (1x por dia via Celery Beat).

## Executar Tasks Manualmente

Coleta de filmes:
```bash
docker compose exec worker celery -A app.celery_app.celery call app.celery_app.task_ingest
```

Treinamento ML:
```bash
docker compose exec worker celery -A app.celery_app.celery call app.celery_app.task_train
```

## Banco de Dados

### Tabelas:
- `movies` - Dados dos filmes
- `movie_snapshots` - Histórico de métricas
- `model_predictions` - Predições ML

### Acessar PostgreSQL:

**Modo Local:**
```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml exec postgres psql -U app -d movies
```

**Modo Nuvem (Neon):**
- Console: https://console.neon.tech
- Ou use a connection string do `.env`

## Logs

**Modo Nuvem:**
```bash
docker compose logs -f [worker|beat|web]
```

**Modo Local:**
```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml logs -f [worker|beat|web]
```

## Troubleshooting

### Banco de dados
- **Nuvem:** Verifique connection string no `.env` (deve incluir `?sslmode=require`)
- **Local:** Aguarde healthcheck do PostgreSQL (~20s)

### Redis
- **Nuvem:** URL deve usar `rediss://` (TLS)
- **Local:** URL deve ser `redis://redis:6379/0`

### Dashboard vazio
Execute o ingest inicial manualmente (demora algumas horas) ou utilize o banco disponibilizado já povoado.
```
docker compose exec worker celery -A web.app.celery_app call app.celery_app.task_initial_ingest
```
