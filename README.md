# TMDB Dashboard - Flask + Celery + MySQL

Sistema de dashboard alimentado por machine learning com dados do TMDB coletados a cada 2 minutos.

## Stack

- **Flask** - API REST + Dashboard web com Jinja2 e Chart.js
- **Celery + Celery Beat** - Agendamento automático de tarefas (coleta TMDB a cada 2 min)
- **MySQL** - Banco de dados relacional (via Docker)
- **Redis** - Broker/backend do Celery
- **SQLAlchemy** - ORM para persistência
- **Scikit-learn** - Pipeline de machine learning para previsão de popularidade

## Estrutura

```
project/
  docker-compose.yml      # Orquestração dos containers
  .env                    # Variáveis de ambiente
  requirements.txt        # Dependências Python
  web/
    Dockerfile
    app/
      __init__.py         # Factory do Flask
      config.py           # Configurações
      celery_app.py       # Tasks do Celery
      db.py               # Inicialização do SQLAlchemy
      models.py           # Modelos de dados
      tmdb.py             # Cliente TMDB API
      ml.py               # Pipeline de ML
      routes/
        api.py            # Endpoints da API
        dashboard.py      # Rotas do dashboard
      templates/
        base.html
        index.html
      static/
        main.js           # Chart.js + polling
```

## Setup

### 1. Configurar variáveis de ambiente

Copie o arquivo de exemplo e adicione sua chave da API do TMDB:

```bash
cp env.sample .env
```

Depois edite o arquivo `.env` e adicione sua chave:

**Opção A - API Key v3** (Recomendado - mais simples):
```bash
TMDB_API_KEY=986cf68636f510a990bb3355085ac547
```

**Opção B - Bearer Token v4**:
```bash
TMDB_API_KEY=eyJhbGciOiJIUzI1NiJ9...
```

> O código detecta automaticamente qual tipo você está usando.

### 2. Subir os containers

```bash
docker compose up --build
```

Isso irá iniciar:
- MySQL (acesso interno entre containers)
- Redis (acesso interno entre containers)
- Flask web server (porta 8000)
- Celery worker
- Celery beat (scheduler)

### 3. Acessar o dashboard

Abra o navegador em: **http://localhost:8000/**

O dashboard atualiza automaticamente a cada 30 segundos via polling.

## Endpoints da API

- `GET /health` - Health check
- `GET /api/health` - Health check da API
- `GET /api/summary` - Top 10 filmes mais populares

## Como funciona

1. **Celery Beat** agenda a task `task_ingest` para rodar a cada 2 minutos
2. A task coleta 2 páginas de filmes populares do TMDB
3. Os dados são armazenados no MySQL (tabelas `movies` e `movie_snapshots`)
4. A cada 15 minutos, a task `task_train` treina um modelo de ML (LogisticRegression)
5. O dashboard faz polling do endpoint `/api/summary` a cada 30s
6. Chart.js renderiza o gráfico de barras com os Top 10 filmes

## Executar task manualmente

Para testar a coleta sem esperar o agendamento:

```bash
docker compose exec worker celery -A app.celery_app.celery call app.celery_app.task_ingest
```

## Banco de dados

### Tabelas criadas automaticamente:

- `movies` - Dados dos filmes
- `movie_snapshots` - Snapshots históricos de métricas
- `model_predictions` - Predições do modelo de ML

### Acessar MySQL diretamente

```bash
docker compose exec mysql mysql -u app -papp123 movies
```

Para expor MySQL e Redis no host (caso precise acessar de fora), adicione no `docker-compose.yml`:
```yaml
mysql:
  ports:
    - "3306:3306"
redis:
  ports:
    - "6379:6379"
```

## Ajustes

### Alterar frequência de coleta

Edite `web/app/celery_app.py`:

```python
"fetch-tmdb-every-2-min": {
    "task": "app.celery_app.task_ingest",
    "schedule": 120.0,  # segundos
},
```

### Alterar intervalo de polling do dashboard

Edite `.env`:

```
POLL_INTERVAL_MS=30000
```

### Coletar mais páginas do TMDB

Edite `web/app/celery_app.py` na task `task_ingest`:

```python
res = collect_popular_pages(pages=5)  # aumentar número de páginas
```

## Persistência

Os dados do MySQL são persistidos no volume Docker `mysql_data`, mesmo após reiniciar os containers.

## Logs

Ver logs de todos os serviços:
```bash
docker compose logs -f
```

Ver logs específicos:
```bash
docker compose logs -f worker
docker compose logs -f beat
docker compose logs -f web
```

## Troubleshooting

### "MySQL server has gone away"
Verifique o healthcheck do MySQL no `docker-compose.yml`. O web/worker só iniciam após MySQL estar saudável.

### Rate limit TMDB
Ajuste o `sleep_per_call` em `collect_popular_pages()` no arquivo `tmdb.py`.

### Dashboard vazio
A primeira coleta demora até 2 minutos. Execute manualmente a task para popular imediatamente.
