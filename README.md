# TMDB Dashboard - Flask + Celery + MySQL

Sistema de dashboard alimentado por machine learning com dados do TMDB coletados a cada 2 minutos.

## Stack

- **Flask** - API REST + Dashboard web com Jinja2 e Chart.js
- **Celery + Celery Beat** - Agendamento automático de tarefas (coleta TMDB a cada 2 min)
- **MySQL** - Banco de dados relacional (via Docker)
- **Redis** - Broker/backend do Celery
- **SQLAlchemy** - ORM para persistência
- **Scikit-learn** - Pipeline de machine learning com regressão linear para prever popularidade e notas

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

## Deploy na Vercel

Deseja publicar o dashboard como Function na Vercel com versionamento
automático por commit? Siga o passo a passo em
[docs/DEPLOY_VERCEL.md](docs/DEPLOY_VERCEL.md).

## Endpoints da API

- `GET /health` - Health check
- `GET /api/health` - Health check da API
- `GET /api/summary` - Top 10 filmes mais populares
- `GET /api/predictions` - Top 20 predições de popularidade e nota média

## Fluxo de Funcionamento

1. **Coleta (a cada 2 min):**
   - Celery Beat agenda `task_ingest`
   - Busca 2 páginas de filmes populares do TMDB (40 filmes)
   - Armazena em MySQL (tabelas `movies` e `movie_snapshots`)

2. **Treinamento ML (a cada 15 min):**
   - Celery Beat agenda `task_train`
   - Extrai features dos filmes coletados
   - Treina 2 modelos de Regressão Linear (popularidade e nota)
   - Calcula métricas (MAE, R²)
   - Gera predições para todos os filmes
   - Salva em `model_predictions`

3. **Dashboard (polling 30s):**
   - Busca `/api/summary` (Top 10 mais populares)
   - Busca `/api/predictions` (Top 20 predições do modelo)
   - Chart.js renderiza:
     - Gráfico de barras: Top 10 filmes populares
     - Gráfico de linha: Popularidade prevista vs real
     - Gráfico de linha: Nota média prevista vs real
     - Tabela: Detalhes das predições

## Machine Learning

> 📖 **Para documentação completa sobre ML, casos de uso, interpretação de métricas e roadmap:** Veja [ML_INSIGHTS.md](ML_INSIGHTS.md)

### O que o modelo prevê?

Os modelos realizam **predição baseada em características** (não é previsão temporal). Eles aprendem a relação entre as features de um filme e sua popularidade/nota atual.

**Tipo de predição:** Regressão baseada em features do filme  
**Objetivo:** Estimar popularidade e nota média que um filme DEVERIA ter baseado em suas características  
**Período:** Valores atuais (não é série temporal)  
**NÃO prevê:** Evolução futura (série temporal) - isso está no roadmap

### Como funciona?

1. O modelo é treinado com os filmes já coletados do TMDB
2. Aprende padrões: "Filmes de ação no verão tendem a ter popularidade X"
3. Para cada filme, compara o valor **previsto** (baseado nas features) vs **real** (do TMDB)
4. Útil para identificar:
   - Filmes sub-avaliados (previsão > realidade)
   - Filmes super-avaliados (previsão < realidade)
   - Padrões de sucesso por gênero, época, etc.

### Features Utilizadas

- **runtime** - Duração do filme (minutos)
- **vote_count** - Quantidade de votos recebidos
- **release_year** - Ano de lançamento
- **release_month** - Mês de lançamento (1-12)
- **is_summer** - Lançado no verão [Jun-Ago] (0 ou 1)
- **is_holiday** - Lançado em temporada de festas [Nov-Dez] (0 ou 1)
- **genre_action** - É filme de ação (0 ou 1)
- **genre_adventure** - É filme de aventura (0 ou 1)
- **genre_comedy** - É comédia (0 ou 1)
- **genre_drama** - É drama (0 ou 1)
- **genre_scifi** - É ficção científica (0 ou 1)
- **genre_thriller** - É thriller (0 ou 1)
- **genre_count** - Total de gêneros do filme
- **is_english** - Filme em inglês (0 ou 1)

### Modelos

Dois modelos de **Regressão Linear** são treinados independentemente:

1. **Modelo de Popularidade** - Prevê o índice de popularidade (0-1000+)
   - Quanto maior, mais popular o filme
   - Baseado em views, buscas, engajamento no TMDB

2. **Modelo de Nota Média** - Prevê a avaliação média (0-10)
   - Nota dada pelos usuários do TMDB
   - Representa a qualidade percebida

### Métricas de Avaliação

- **MAE (Mean Absolute Error)** - Erro médio absoluto das predições
  - Quanto menor, melhor
  - Ex: MAE=50 na popularidade significa erro médio de 50 pontos
  
- **R² Score** - Coeficiente de determinação (0-1)
  - Quanto mais próximo de 1, melhor o ajuste
  - Mostra % da variância explicada pelo modelo

### Exemplo Prático

**Filme:** "Avatar: The Way of Water"
- **Features:** Action, Adventure, Sci-Fi, 192 min, Inglês, Dezembro (holiday season)
- **Previsão do modelo:** Popularidade = 850, Nota = 7.8
- **Valor real TMDB:** Popularidade = 900, Nota = 7.6
- **Interpretação:** Modelo acertou bem! Filme de ação/sci-fi no fim de ano tende a ser popular

## Executar tasks manualmente

Para testar a coleta sem esperar o agendamento:

```bash
docker compose exec worker celery -A app.celery_app.celery call app.celery_app.task_ingest
```

Para treinar os modelos de ML imediatamente:

```bash
docker compose exec worker celery -A app.celery_app.celery call app.celery_app.task_train
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



TO DO:
- aumentar amostra local
- mais modelos de ML
- deploy vercel
- tempo real?