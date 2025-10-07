# 🚀 Quick Start - TMDB ML Project

## 📌 Escolha seu modo de execução

### 🌐 MODO 1: Nuvem (Neon + Upstash) - Recomendado para Produção

```bash
cp env.sample .env
```

Edite `.env` e configure:
- `TMDB_API_KEY` - https://www.themoviedb.org/settings/api
- `DATABASE_URL` - https://console.neon.tech (PostgreSQL)
- `REDIS_URL` - https://console.upstash.com (Redis)

```bash
docker compose up --build
```

**✅ Acesse:** http://localhost:8000

---

### 🐳 MODO 2: Local (Docker) - Recomendado para Desenvolvimento

```bash
cp env.local.sample .env
```

Edite `.env` e configure apenas:
- `TMDB_API_KEY` - https://www.themoviedb.org/settings/api

```bash
./run-local.sh up --build
```

**✅ Acesse:** http://localhost:8000

---

## 📚 Próximos Passos

1. **Executar coleta manual** (opcional):
   ```bash
   docker compose exec worker celery -A app.celery_app.celery call app.celery_app.task_ingest
   ```

2. **Treinar modelo ML** (opcional):
   ```bash
   docker compose exec worker celery -A app.celery_app.celery call app.celery_app.task_train
   ```

3. **Ver logs:**
   ```bash
   docker compose logs -f web
   ```

---

## 📖 Documentação Completa

- **[README.md](README.md)** - Documentação principal
- **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Guia detalhado de setup
- **[CHANGELOG_LOCAL_SETUP.md](CHANGELOG_LOCAL_SETUP.md)** - O que mudou nesta atualização

---

## ⚡ Comandos Mais Usados

### Modo Nuvem
```bash
docker compose up -d              # Subir em background
docker compose logs -f web        # Ver logs do web
docker compose down               # Parar tudo
```

### Modo Local
```bash
./run-local.sh up -d             # Subir em background
./run-local.sh logs -f web       # Ver logs do web
./run-local.sh down -v           # Parar e limpar volumes
```

---

**🎉 Pronto para começar!**

