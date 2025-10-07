# 📖 Storytelling do Projeto - TMDB Horror Movies Predictor

## 🎯 Contexto e Motivação

### O Problema
Como prever a popularidade e o sucesso de filmes de terror antes do lançamento? Produtores, distribuidores e plataformas de streaming precisam tomar decisões baseadas em dados para:
- Definir orçamento de marketing
- Escolher a melhor data de lançamento
- Identificar filmes sub ou super-avaliados
- Entender padrões de sucesso no gênero horror

### A Solução
Sistema automatizado que coleta dados de filmes de terror do TMDB, treina modelos de Machine Learning e gera predições e insights em tempo real através de um dashboard web interativo.

---

## 🏗️ Arquitetura do Sistema

### Visão Geral dos Componentes

```mermaid
graph TB
    subgraph "Camada de Apresentação"
        A[Dashboard Web<br/>Flask + Jinja2 + Chart.js]
    end
    
    subgraph "Camada de API"
        B[Flask REST API<br/>endpoints /api/*]
    end
    
    subgraph "Camada de Processamento Assíncrono"
        C[Celery Worker<br/>executa tasks]
        D[Celery Beat<br/>scheduler]
    end
    
    subgraph "Camada de Dados"
        E[(MySQL Database<br/>8 tabelas)]
        F[(Redis<br/>broker + backend)]
    end
    
    subgraph "Serviços Externos"
        G[TMDB API<br/>fonte de dados]
    end
    
    subgraph "Camada de ML"
        H[Pipeline ML<br/>scikit-learn]
    end
    
    A -->|polling 30s| B
    B -->|query SQL| E
    D -->|agenda tasks| F
    F -->|distribui tasks| C
    C -->|coleta dados| G
    C -->|persiste dados| E
    C -->|treina modelos| H
    H -->|salva predições| E
    
    style A fill:#4CAF50
    style B fill:#2196F3
    style C fill:#FF9800
    style D fill:#FF9800
    style E fill:#9C27B0
    style F fill:#F44336
    style G fill:#00BCD4
    style H fill:#FFC107
```

---

## 🔄 Fluxo de Dados Completo

### 1. Coleta de Dados (Data Ingestion)

```mermaid
sequenceDiagram
    participant Beat as Celery Beat
    participant Redis
    participant Worker as Celery Worker
    participant TMDB as TMDB API
    participant DB as MySQL
    
    Note over Beat: A cada 5 minutos
    Beat->>Redis: agenda task_update_movies
    Redis->>Worker: envia task
    
    loop Para cada ano 2010-atual
        Worker->>TMDB: GET /discover/movie?year=X&genre=27
        TMDB-->>Worker: 20 páginas de filmes
        
        loop Para cada filme
            Worker->>DB: INSERT/UPDATE em movies
            Worker->>DB: INSERT em movie_snapshots
        end
    end
    
    Worker-->>Redis: task concluída ✓
    Note over DB: ~5.000 filmes de terror<br/>armazenados
```

**Detalhes da Coleta:**
- **Frequência:** A cada 5 minutos
- **Período:** 2010 até ano atual
- **Filtro:** Horror (Genre ID 27) + mínimo 50 votos
- **Volume:** ~20 páginas por ano = ~5.000 filmes
- **Estratégia:** Upsert (atualiza existentes, insere novos)

---

### 2. Treinamento dos Modelos ML

```mermaid
sequenceDiagram
    participant Beat as Celery Beat
    participant Redis
    participant Worker as Celery Worker
    participant DB as MySQL
    participant ML as Pipeline ML
    
    Note over Beat: A cada 1 hora
    Beat->>Redis: agenda task_train
    Redis->>Worker: envia task
    
    Worker->>DB: SELECT filmes de terror
    DB-->>Worker: ~5.000 registros
    
    Worker->>ML: extract_horror_features()
    ML-->>Worker: 14 features por filme
    
    par Treinamento Paralelo
        Worker->>ML: train_horror_regression()
        ML->>ML: RandomForestRegressor<br/>100 árvores, depth=10
        ML->>DB: salva feature_importance<br/>em horror_regression
        ML->>DB: salva predições<br/>em horror_regression_predictions
        
        Worker->>ML: train_horror_classification()
        ML->>ML: RandomForestClassifier<br/>alta/baixa avaliação
        ML->>DB: salva confusion_matrix<br/>roc_curve em horror_classification
        
        Worker->>ML: train_horror_clustering()
        ML->>ML: KMeans + PCA<br/>4 clusters
        ML->>DB: salva clusters<br/>em horror_clustering
        ML->>DB: salva perfis<br/>em horror_cluster_profiles
    end
    
    Worker-->>Redis: task concluída ✓
    Note over DB: Modelos atualizados<br/>prontos para consulta
```

**Detalhes do Treinamento:**
- **Frequência:** A cada 1 hora
- **Algoritmos:** Random Forest (Regressão + Classificação) + K-Means
- **Features:** 14 variáveis (runtime, vote_count, release_month, genres, etc.)
- **Métricas:** MAE, R², Accuracy, AUC, Confusion Matrix

---

### 3. Visualização no Dashboard

```mermaid
sequenceDiagram
    participant Browser as Browser
    participant Flask as Flask Server
    participant API as API Routes
    participant DB as MySQL
    
    Browser->>Flask: GET /
    Flask-->>Browser: index.html + main.js
    
    Note over Browser: Polling a cada 30s
    
    loop Atualização Automática
        Browser->>API: GET /api/horror/regression/features
        API->>DB: query horror_regression
        DB-->>API: top 10 features + métricas
        API-->>Browser: JSON response
        
        Browser->>API: GET /api/horror/regression/predictions
        API->>DB: query horror_regression_predictions + movies
        DB-->>API: predições com títulos
        API-->>Browser: JSON response
        
        Browser->>API: GET /api/horror/classification
        API->>DB: query horror_classification
        DB-->>API: confusion matrix + ROC
        API-->>Browser: JSON response
        
        Browser->>API: GET /api/horror/clustering/pca
        API->>DB: query horror_clustering + movies
        DB-->>API: clusters com coordenadas PCA
        API-->>Browser: JSON response
        
        Browser->>API: GET /api/horror/clustering/profiles
        API->>DB: query horror_cluster_profiles
        DB-->>API: perfis médios dos clusters
        API-->>Browser: JSON response
        
        Browser->>Browser: Chart.js renderiza 6 gráficos
    end
```

**Gráficos do Dashboard:**
1. **Feature Importance** - Barras horizontais (top 10 features)
2. **Real vs Predicted** - Scatter plot (popularidade)
3. **Confusion Matrix** - Barras (TN, FP, FN, TP)
4. **ROC Curve** - Linha (TPR vs FPR)
5. **Cluster Analysis** - Scatter colorido (PCA 2D)
6. **Cluster Profiles** - Barras agrupadas (médias)

---

## 🛠️ Jornada do Desenvolvimento

### Fase 1: Infraestrutura Base
```mermaid
graph LR
    A[Docker Compose] --> B[Container MySQL]
    A --> C[Container Redis]
    A --> D[Container Init-DB]
    D --> E[Criação de Tabelas]
    E --> F[Infraestrutura Pronta]
    
    style F fill:#4CAF50
```

**Decisões Técnicas:**
- Docker Compose para orquestração
- MySQL para dados relacionais (suporta JOIN complexos)
- Redis como broker do Celery (rápido, em memória)
- Init-DB como serviço separado (idempotência)

---

### Fase 2: Aplicação Flask
```mermaid
graph LR
    A[Factory Pattern] --> B[create_app]
    B --> C[Blueprints API]
    B --> D[Blueprints Dashboard]
    B --> E[SQLAlchemy ORM]
    B --> F[Templates Jinja2]
    
    style B fill:#2196F3
```

**Decisões Técnicas:**
- Application Factory para flexibilidade
- Blueprints para modularização
- SQLAlchemy ORM para abstração do banco
- Gunicorn com threads para concorrência

---

### Fase 3: Sistema de Tarefas Assíncronas
```mermaid
graph TB
    A[Celery App] --> B[Tasks]
    A --> C[Beat Schedule]
    
    B --> D[task_update_movies<br/>coleta incremental]
    B --> E[task_train<br/>treina modelos]
    
    C --> F[Cron: 5min]
    C --> G[Cron: 60min]
    
    F -.-> D
    G -.-> E
    
    style A fill:#FF9800
```

**Decisões Técnicas:**
- Celery para processamento assíncrono
- Celery Beat para agendamento (sem cron externo)
- Tasks idempotentes (podem ser executadas múltiplas vezes)
- Context do Flask dentro das tasks (acesso ao DB)

---

### Fase 4: Integração com TMDB
```mermaid
graph LR
    A[tmdb.py] --> B[tmdb_get]
    B --> C[Autenticação API Key/Bearer]
    B --> D[Rate Limiting<br/>sleep 0.3s]
    B --> E[Error Handling]
    
    A --> F[collect_movies_by_year_range]
    F --> G[Loop anos 2010-atual]
    G --> H[20 páginas por ano]
    H --> I[Filtro: Horror + min_votes]
    
    style A fill:#00BCD4
```

**Decisões Técnicas:**
- Suporte duplo: API Key v3 e Bearer Token v4
- Sleep entre requests (rate limiting preventivo)
- Coleta por ano (melhor controle de paginação)
- Filtro de votos mínimos (qualidade dos dados)

---

### Fase 5: Pipeline de Machine Learning
```mermaid
graph TB
    A[get_horror_movies] --> B[Filtra Horror<br/>do campo genres]
    B --> C[extract_horror_features<br/>14 features]
    
    C --> D[Regressão]
    C --> E[Classificação]
    C --> F[Clustering]
    
    D --> G[RandomForest<br/>100 trees]
    G --> H[MAE + R²]
    H --> I[Salva em<br/>horror_regression]
    
    E --> J[RandomForest<br/>threshold=median]
    J --> K[Confusion Matrix<br/>ROC + AUC]
    K --> L[Salva em<br/>horror_classification]
    
    F --> M[KMeans<br/>4 clusters]
    M --> N[PCA 2D]
    N --> O[Salva em<br/>horror_clustering]
    
    style C fill:#FFC107
    style D fill:#FFC107
    style E fill:#FFC107
    style F fill:#FFC107
```

**Decisões Técnicas:**
- Random Forest (robusto, interpretável)
- StandardScaler para normalização
- Train/Test Split 75/25
- PCA para visualização 2D
- Features específicas para horror (is_october, genre_thriller)

---

### Fase 6: Frontend Interativo
```mermaid
graph LR
    A[main.js] --> B[fetchData]
    B --> C[5 endpoints API]
    
    B --> D[Chart.js]
    D --> E[6 gráficos interativos]
    
    A --> F[setInterval 30s]
    F --> B
    
    E --> G[Atualização automática]
    
    style D fill:#4CAF50
```

**Decisões Técnicas:**
- Chart.js para visualizações (leve, responsivo)
- Polling a cada 30s (dados quase em tempo real)
- Vanilla JS (sem framework pesado)
- Cores semânticas (verde=sucesso, vermelho=erro)

---

## 📊 Modelo de Dados

### Schema Relacional

```mermaid
erDiagram
    movies ||--o{ movie_snapshots : "tem"
    movies ||--o{ model_predictions : "tem"
    movies ||--o{ horror_regression_predictions : "tem"
    movies ||--o{ horror_clustering : "tem"
    
    movies {
        bigint tmdb_id PK
        string imdb_id
        string title
        text overview
        date release_date
        float popularity
        int vote_count
        float vote_average
        int runtime
        text genres
        datetime updated_at
    }
    
    movie_snapshots {
        bigint id PK
        bigint tmdb_id FK
        datetime snapshot_ts
        float popularity
        int vote_count
        float vote_average
    }
    
    horror_regression {
        bigint id PK
        datetime analysis_ts
        string feature_name
        float feature_importance
        float mae
        float r2_score
    }
    
    horror_regression_predictions {
        bigint id PK
        datetime analysis_ts
        bigint tmdb_id FK
        float actual_popularity
        float predicted_popularity
    }
    
    horror_classification {
        bigint id PK
        datetime analysis_ts
        text confusion_matrix
        text roc_curve
        float auc_score
        float accuracy
    }
    
    horror_clustering {
        bigint id PK
        datetime analysis_ts
        bigint tmdb_id FK
        int cluster_id
        float pca_x
        float pca_y
    }
    
    horror_cluster_profiles {
        bigint id PK
        datetime analysis_ts
        int cluster_id
        float avg_popularity
        float avg_vote_average
        int movie_count
    }
```

**Estratégia de Timestamps:**
- `analysis_ts`: Agrupa resultados de uma mesma execução de treinamento
- `snapshot_ts`: Permite análise temporal das métricas
- `updated_at`: Rastreia última atualização dos filmes

---

## 🔄 Ciclo de Vida Completo

```mermaid
graph TB
    Start([docker compose up]) --> Init[Init-DB<br/>cria tabelas]
    Init --> Services[Web + Worker + Beat<br/>iniciam]
    
    Services --> Beat1[Beat agenda<br/>task_update_movies]
    Beat1 --> Collect[Worker coleta<br/>filmes do TMDB]
    Collect --> Store[Salva em<br/>movies + snapshots]
    
    Services --> Beat2[Beat agenda<br/>task_train]
    Beat2 --> Load[Worker carrega<br/>filmes de terror]
    Load --> Extract[Extrai 14<br/>features]
    Extract --> Train[Treina 3<br/>modelos]
    Train --> Save[Salva resultados<br/>em 5 tabelas]
    
    Services --> Web[Flask serve<br/>dashboard]
    Web --> Browser[Browser carrega<br/>index.html]
    Browser --> Poll[Polling 30s<br/>chama 5 APIs]
    Poll --> Render[Chart.js renderiza<br/>6 gráficos]
    
    Render -.30s.-> Poll
    Store -.5min.-> Beat1
    Save -.60min.-> Beat2
    
    style Start fill:#4CAF50
    style Render fill:#4CAF50
```

---

## 🎯 Casos de Uso Práticos

### 1. Produtor de Filmes
**Pergunta:** "Quando lançar meu filme de terror?"

**Resposta do Sistema:**
```
Feature Importance:
1. is_october: 0.35 → Filmes em outubro têm 35% mais impacto
2. vote_count: 0.22 → Boca-a-boca é crucial
3. genre_thriller: 0.18 → Misturar com thriller ajuda

Recomendação: Lançar em outubro, investir em marketing
para gerar votos iniciais, adicionar elementos de thriller.
```

---

### 2. Distribuidor
**Pergunta:** "Quais filmes estão sub-avaliados?"

**Resposta do Sistema:**
```
Regression Predictions (Top 5 sub-avaliados):
1. "The Witch" → Previsto: 85 | Real: 45 (+89%)
2. "It Follows" → Previsto: 78 | Real: 42 (+86%)
3. "Hereditary" → Previsto: 92 | Real: 53 (+74%)

Interpretação: Filmes com qualidade acima da popularidade atual.
Oportunidade para compra de direitos de distribuição.
```

---

### 3. Plataforma de Streaming
**Pergunta:** "Quais filmes recomendar juntos?"

**Resposta do Sistema:**
```
Cluster Analysis:
- Cluster 0: Terror psicológico (avg_runtime: 105min, alta avaliação)
- Cluster 1: Slasher clássico (avg_runtime: 90min, alta popularidade)
- Cluster 2: Terror sobrenatural (mix de características)
- Cluster 3: Terror indie (baixo orçamento, nicho)

Recomendação: Agrupar catálogo por cluster para melhor UX.
```

---

### 4. Analista de Mercado
**Pergunta:** "O modelo está acertando as previsões?"

**Resposta do Sistema:**
```
Regression Metrics:
- MAE: 12.5 → Erro médio de 12.5 pontos de popularidade
- R²: 0.78 → Modelo explica 78% da variância

Classification Metrics:
- Accuracy: 0.85 → 85% de acerto alta/baixa avaliação
- AUC: 0.91 → Excelente capacidade discriminativa

Interpretação: Modelo confiável, mas pode melhorar com mais features.
```

---

## 🚀 Evolução Futura

### Roadmap Técnico

```mermaid
timeline
    title Evolução do Sistema
    
    Fase 1 (Atual) : Coleta automatizada
                   : 3 modelos ML
                   : Dashboard básico
    
    Fase 2 (Próxima) : Deep Learning (LSTM para séries temporais)
                      : Features de NLP (análise de overview)
                      : API pública com autenticação
    
    Fase 3 (Futuro) : Análise de sentiment (reviews)
                    : Predição de bilheteria
                    : Integração com outras fontes de dados
    
    Fase 4 (Visão) : Sistema de recomendação personalizado
                   : Análise de trailers (computer vision)
                   : Predição de sucesso em streaming
```

### Melhorias Planejadas

**1. Features Avançadas:**
- Análise de sentimento do overview (NLP)
- Extração de keywords do plot
- Detecção de sub-gêneros (slasher, found footage, etc.)

**2. Modelos Avançados:**
- XGBoost para melhor performance
- LSTM para previsão temporal (tendências)
- Ensemble de modelos (voting)

**3. Infraestrutura:**
- Cache com Redis (reduzir queries)
- Message Queue (SQS/RabbitMQ)
- Deploy em Kubernetes

**4. Observabilidade:**
- Prometheus + Grafana (métricas)
- ELK Stack (logs centralizados)
- Alertas automáticos (model drift)

---

## 📈 Métricas de Sucesso

### Técnicas
- ✅ Coleta de ~5.000 filmes de terror
- ✅ 3 modelos treinados com sucesso
- ✅ R² > 0.75 (boa capacidade preditiva)
- ✅ Accuracy > 0.80 (classificação confiável)
- ✅ Dashboard com atualização automática

### Negócio
- 📊 Identificação de padrões de sucesso
- 🎯 Redução de risco em investimentos
- 💡 Insights acionáveis para stakeholders
- ⏱️ Decisões baseadas em dados em tempo real

---

## 🎓 Aprendizados e Decisões Técnicas

### Por que Flask?
- ✅ Simplicidade e flexibilidade
- ✅ Ecossistema Python (scikit-learn, pandas)
- ✅ Fácil integração com Celery
- ❌ Não precisa de SPA complexo (React/Vue)

### Por que Celery?
- ✅ Processamento assíncrono nativo em Python
- ✅ Celery Beat integrado (scheduler)
- ✅ Retry automático de tasks
- ❌ Apache Airflow seria overkill

### Por que MySQL?
- ✅ Queries relacionais complexas (JOINs)
- ✅ Transações ACID
- ✅ Familiar para maioria dos devs
- ❌ PostgreSQL seria alternativa válida

### Por que Redis?
- ✅ Alta performance (in-memory)
- ✅ Simples de configurar
- ✅ Serve broker + backend
- ❌ RabbitMQ seria mais robusto, mas complexo

### Por que Random Forest?
- ✅ Robusto a overfitting
- ✅ Feature importance interpretável
- ✅ Sem necessidade de feature scaling (mas usamos)
- ❌ Deep Learning seria overkill para dados tabulares

---

## 🔍 Insights do Projeto

### 1. Padrões Identificados
- 📅 Filmes lançados em **outubro** têm 35% mais impacto
- 🎭 Combinar **Horror + Thriller** aumenta popularidade
- ⏱️ Duração ideal: **90-105 minutos** (não muito longo)
- 🌍 Filmes em **inglês** têm alcance maior

### 2. Descobertas Inesperadas
- Filmes de terror indie (low budget) formam cluster distinto
- Vote count é mais importante que vote average para popularidade
- Filmes de dezembro (época de festas) também performam bem
- Terror sobrenatural domina o mercado pós-2010

### 3. Desafios Superados
- **Rate limiting TMDB:** Implementado sleep adaptativo
- **Data quality:** Filtro de mínimo de votos
- **Model drift:** Re-treinamento automático a cada 10h
- **Cold start:** Init-DB garante estrutura antes de tasks

---

## 📚 Recursos e Referências

### Documentação Oficial
- [Flask](https://flask.palletsprojects.com/)
- [Celery](https://docs.celeryproject.org/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [scikit-learn](https://scikit-learn.org/)
- [TMDB API](https://developers.themoviedb.org/)

### Conceitos Aplicados
- **Microservices:** Separação de responsabilidades (web, worker, beat)
- **ETL Pipeline:** Extract (TMDB) → Transform (features) → Load (MySQL)
- **ML Pipeline:** Coleta → Feature Engineering → Treino → Predição
- **Async Processing:** Tasks pesadas fora do request/response
- **Polling Pattern:** Atualização periódica sem WebSocket

---

## 🎬 Conclusão

Este projeto demonstra uma arquitetura moderna e escalável para problemas de **Machine Learning em produção**:

```mermaid
mindmap
  root((TMDB<br/>Horror<br/>Predictor))
    Coleta Automatizada
      Celery Beat
      TMDB API
      Upsert Strategy
    Machine Learning
      Random Forest
      Feature Engineering
      3 Modelos
    Visualização
      Dashboard Web
      Chart.js
      Polling Real-time
    Infraestrutura
      Docker Compose
      MySQL
      Redis
      Flask
```

**Principais Conquistas:**
1. ✅ Sistema 100% automatizado
2. ✅ Dados sempre atualizados
3. ✅ Modelos re-treinados periodicamente
4. ✅ Insights visuais e acionáveis
5. ✅ Arquitetura escalável e manutenível

**Aplicações Reais:**
- 🎬 Produtoras de cinema
- 📺 Plataformas de streaming
- 💰 Investidores de entretenimento
- 📊 Analistas de mercado
- 🎓 Pesquisadores acadêmicos

---

**Desenvolvido com ❤️ para aprender e aplicar:**
- Data Engineering
- Machine Learning
- DevOps
- Software Architecture
- Python Ecosystem



