# TMDB Horror Movies Predictor - Flask + Celery + MySQL

Sistema de predição de popularidade e notas para filmes de terror/horror usando machine learning.

## Stack

- **Flask** - API REST + Dashboard web com Jinja2 e Chart.js
- **Celery + Celery Beat** - Agendamento automático de coleta diária
- **MySQL** - Banco de dados relacional (via Docker)
- **Redis** - Broker/backend do Celery
- **SQLAlchemy** - ORM para persistência
- **Scikit-learn** - Pipeline de machine learning com regressão linear para prever popularidade e notas de filmes de terror/horror

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

⚠️ **Nota:** O Celery Beat executará a primeira coleta automática em até 24h. O dashboard só exibirá dados após a coleta ser concluída (~1-2 horas de execução).

## Endpoints da API

- `GET /health` - Health check
- `GET /api/health` - Health check da API
- `GET /api/summary` - Top 10 filmes mais populares
- `GET /api/predictions` - Top 20 predições de popularidade e nota média

## Fluxo de Funcionamento

1. **Coleta de Filmes de Terror/Horror (1x por dia):**
   - Celery Beat agenda `task_ingest` diariamente
   - Coleta filmes de terror/horror de 2010 até o ano atual
   - Usa endpoint `/discover/movie` do TMDB com filtro de gênero (Horror = ID 27)
   - Filtra filmes com pelo menos 10 votos
   - 20 páginas por ano (~300-400 filmes/ano)
   - Total estimado: ~5.000 filmes de terror
   - Armazena em MySQL (tabelas `movies` e `movie_snapshots`)
   - Faz upsert: atualiza filmes existentes e adiciona novos

2. **Treinamento ML (a cada hora):**
   - Celery Beat agenda `task_train` a cada 1 hora
   - Extrai features dos filmes de terror coletados
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

## Coleta Automática de Dados

O sistema coleta automaticamente **filmes de terror/horror de 2010 em diante** diariamente via Celery Beat.

### Características da Coleta:
- **Gênero:** Horror (TMDB Genre ID: 27)
- **Período:** 2010 até ano atual (~16 anos)
- **Frequência:** 1x por dia (24 horas)
- **Volume:** ~5.000 filmes de terror únicos + atualizações
- **Filtros:** Filmes com pelo menos 10 votos
- **Estratégia:** Percorre ano por ano (2010 até atual)
- **Páginas por ano:** 20 páginas (~300-400 filmes/ano)
- **Upsert automático:** Atualiza existentes, insere novos
- **Tempo de execução:** ~1-2 horas por coleta completa

### Dados Coletados:
- Metadados: título, título original, overview, idioma
- Métricas: popularidade, vote_count, vote_average
- Detalhes: runtime, gêneros, release_date
- Imagens: poster_path, backdrop_path
- IDs: tmdb_id, imdb_id

### Por que Filmes de Terror?

Foco em um nicho específico permite:
- ✅ Modelos mais precisos e especializados
- ✅ Coleta mais rápida e eficiente
- ✅ Melhor compreensão de padrões do gênero
- ✅ Predições mais relevantes para produtores/distribuidores

### Customização

Para ajustar a coleta, edite `web/app/tmdb.py` na função `collect_movies_by_year_range`:

```python
def collect_movies_by_year_range(
    start_year=2010,
    end_year=None,
    max_pages_per_year=20,
    sleep_per_call=0.3
):
    ...
    data = tmdb_get("/discover/movie", {
        "primary_release_year": year,
        "with_genres": 27,  # 27 = Horror
        ...
    })
```

## Machine Learning

> 📖 **Para documentação completa sobre ML, casos de uso, interpretação de métricas e roadmap:** Veja [ML_INSIGHTS.md](ML_INSIGHTS.md)

### O que o modelo prevê?

Os modelos realizam **predição baseada em características** de filmes de terror/horror. Eles aprendem a relação entre as features de um filme de terror e sua popularidade/nota.

**Tipo de predição:** Regressão baseada em features do filme  
**Objetivo:** Estimar popularidade e nota média que um filme de terror DEVERIA ter baseado em suas características  
**Nicho:** Especializado em filmes de terror/horror (2010+)  
**Período:** Valores atuais (não é série temporal)

### Como funciona?

1. O modelo é treinado com ~5.000 filmes de terror coletados do TMDB (2010-atual)
2. Aprende padrões: "Filmes de terror lançados em outubro tendem a ter popularidade X"
3. Para cada filme, compara o valor **previsto** (baseado nas features) vs **real** (do TMDB)
4. Útil para identificar:
   - Filmes de terror sub-avaliados (previsão > realidade)
   - Filmes de terror super-avaliados (previsão < realidade)
   - Padrões de sucesso para o gênero horror
   - Melhores épocas de lançamento para terror

### Features Utilizadas

Features extraídas para treinar os modelos especializados em terror:

- **runtime** - Duração do filme (minutos)
- **vote_count** - Quantidade de votos recebidos
- **release_year** - Ano de lançamento (2010+)
- **release_month** - Mês de lançamento (outubro é importante para terror!)
- **is_summer** - Lançado no verão [Jun-Ago] (0 ou 1)
- **is_holiday** - Lançado em Halloween/Natal [Out-Dez] (0 ou 1)
- **genre_thriller** - Também é thriller (terror + thriller é comum)
- **genre_drama** - Também é drama
- **genre_scifi** - Também é sci-fi (terror sci-fi)
- **genre_count** - Total de gêneros do filme
- **is_english** - Filme em inglês (0 ou 1)

**Observação:** Todos os filmes já são de terror/horror por definição, então features como `genre_horror` são sempre 1.

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

## Análise de Machine Learning - Filmes de Terror

O sistema implementa três modelos de ML especializados em filmes de terror/horror usando dados do TMDB (2010+):

### 1. Regressão - Predição de Popularidade

**Objetivo:** Prever a popularidade de filmes de terror baseado em suas características.

**Algoritmo:** Random Forest Regressor
- `n_estimators=100` - 100 árvores de decisão
- `max_depth=10` - Profundidade máxima de 10 níveis
- `random_state=42` - Seed para reprodutibilidade

**Features Utilizadas:**

| Feature | Descrição | Tipo |
|---------|-----------|------|
| `runtime` | Duração do filme em minutos | Numérico |
| `vote_count` | Quantidade total de votos | Numérico |
| `release_year` | Ano de lançamento (2010+) | Numérico |
| `release_month` | Mês de lançamento (1-12) | Numérico |
| `release_decade` | Década de lançamento | Numérico |
| `is_october` | Lançado em outubro (Halloween) | Binário (0/1) |
| `is_summer` | Lançado no verão (Jun-Ago) | Binário (0/1) |
| `is_holiday` | Lançado em Nov-Dez | Binário (0/1) |
| `genre_count` | Número total de gêneros | Numérico |
| `genre_thriller` | Também é Thriller | Binário (0/1) |
| `genre_mystery` | Também é Mystery | Binário (0/1) |
| `genre_scifi` | Também é Sci-Fi | Binário (0/1) |
| `genre_fantasy` | Também é Fantasy | Binário (0/1) |
| `is_english` | Idioma inglês | Binário (0/1) |

**Pré-processamento:**
- StandardScaler: Normaliza todas as features para média 0 e desvio padrão 1
- Train/Test Split: 75% treino, 25% teste (random_state=42)

**Métricas:**
- **MAE (Mean Absolute Error):** Erro médio absoluto das predições
- **R² Score:** Coeficiente de determinação (0-1, quanto maior melhor)

### 2. Classificação - Avaliação Alta/Baixa

**Objetivo:** Classificar filmes de terror como "alta avaliação" ou "baixa avaliação".

**Critério:** Filmes com `vote_average` acima da mediana = Alta avaliação (1), caso contrário Baixa (0)

**Algoritmo:** Random Forest Classifier
- Mesmas configurações do regressor
- Stratified split para balancear classes

**Métricas:**
- **Confusion Matrix:** Matriz de confusão (TN, FP, FN, TP)
- **Accuracy:** Acurácia geral do classificador
- **ROC Curve:** Curva ROC (TPR vs FPR)
- **AUC Score:** Área sob a curva ROC (0-1)

### 3. Clustering - Agrupamento de Filmes Similares

**Objetivo:** Agrupar filmes de terror com características similares.

**Algoritmo:** K-Means Clustering
- `n_clusters`: min(4, n_filmes/10), mínimo de 2
- `n_init=10`: 10 inicializações diferentes
- PCA com 2 componentes para visualização 2D

**Perfis de Cluster:**
- Popularidade média
- Avaliação média
- Duração média
- Contagem de votos média
- Quantidade de filmes no cluster

### Dashboard - Visualizações dos Modelos

O dashboard apresenta **6 gráficos interativos** (Chart.js) atualizados automaticamente:

#### Plot 1: Importância das Features (Regressão)
- **Tipo:** Gráfico de barras horizontal
- **Dados:** Top 10 features mais importantes para prever popularidade
- **Interpretação:** Mostra quais características mais influenciam a popularidade de filmes de terror
- **Exemplo:** Se `vote_count` tem alta importância, significa que filmes com mais votos tendem a ser mais populares

#### Plot 2: Real vs Previsto (Regressão)
- **Tipo:** Gráfico de dispersão (scatter plot)
- **Dados:** Popularidade real (eixo x) vs Popularidade prevista (eixo y)
- **Diagonal de referência:** Linha tracejada onde real = previsto
- **Interpretação:** 
  - Pontos próximos à diagonal = boa predição
  - Pontos acima da diagonal = modelo superestimou
  - Pontos abaixo da diagonal = modelo subestimou
- **Ajuste automático de escala:** Foca na região onde estão 90% dos filmes, ignorando outliers extremos

#### Plot 3: Matriz de Confusão (Classificação)
- **Tipo:** Gráfico de barras
- **Dados:** TN, FP, FN, TP da classificação alta/baixa avaliação
- **Interpretação:**
  - **TN (True Negative):** Baixa→Baixa (acerto)
  - **FP (False Positive):** Baixa→Alta (erro tipo I)
  - **FN (False Negative):** Alta→Baixa (erro tipo II)
  - **TP (True Positive):** Alta→Alta (acerto)
- **Cores:** Verde (TN/TP) = acertos, Vermelho/Laranja (FP/FN) = erros

#### Plot 4: Curva ROC (Classificação)
- **Tipo:** Gráfico de linha
- **Dados:** Taxa de Verdadeiros Positivos (TPR) vs Taxa de Falsos Positivos (FPR)
- **Linha diagonal:** Classificador aleatório (baseline)
- **Área sob a curva (AUC):** Medida de qualidade do classificador
- **Interpretação:**
  - AUC = 1.0 → Classificador perfeito
  - AUC = 0.5 → Classificador aleatório
  - Quanto mais a curva se afasta da diagonal, melhor

#### Plot 5: Análise de Clusters (PCA 2D)
- **Tipo:** Gráfico de dispersão colorido por cluster
- **Dados:** Filmes projetados em 2 dimensões (PCA)
- **Cores:** Cada cluster tem uma cor diferente
- **Interpretação:** 
  - Filmes próximos têm características similares
  - Clusters bem separados indicam grupos distintos de filmes de terror
  - Exemplos: "Terror clássico", "Terror slasher", "Terror psicológico", etc.

#### Plot 6: Perfis dos Clusters
- **Tipo:** Gráfico de barras agrupadas (múltiplos eixos Y)
- **Dados:** Médias de popularidade, avaliação e duração por cluster
- **Interpretação:**
  - Identifica padrões: "Cluster 2 tem filmes curtos e bem avaliados"
  - Ajuda a caracterizar cada grupo de filmes
  - Útil para entender audiência e tendências do gênero terror

### Casos de Uso

1. **Produtores:** Identificar features que aumentam popularidade de filmes de terror
2. **Distribuidores:** Encontrar melhor época para lançar filmes de terror (outubro?)
3. **Plataformas de streaming:** Recomendar filmes similares (clusters)
4. **Analistas:** Identificar filmes sub/super-avaliados pelo mercado
5. **Investidores:** Prever ROI baseado em características do filme

### Atualização dos Modelos

Os modelos são retreinados **a cada 1 hora** automaticamente via Celery Beat:
```bash
docker compose exec worker celery -A app.celery_app.celery call app.celery_app.task_train_horror
```

Isso garante que as predições sempre refletem os dados mais recentes do TMDB.
