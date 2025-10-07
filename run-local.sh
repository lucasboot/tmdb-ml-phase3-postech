#!/bin/bash

echo "🐳 TMDB ML - Modo Local (Postgres + Redis no Docker)"
echo "=================================================="
echo ""

if [ ! -f .env ]; then
    echo "⚠️  Arquivo .env não encontrado!"
    echo ""
    echo "Escolha uma opção:"
    echo "1) Criar .env para MODO NUVEM (Neon + Upstash)"
    echo "2) Criar .env para MODO LOCAL (Docker)"
    echo ""
    read -p "Opção [1/2]: " choice
    
    if [ "$choice" = "1" ]; then
        cp env.sample .env
        echo "✅ Arquivo .env criado a partir de env.sample"
        echo "📝 EDITE o .env e adicione suas credenciais do Neon e Upstash"
        exit 1
    elif [ "$choice" = "2" ]; then
        cp env.local.sample .env
        echo "✅ Arquivo .env criado a partir de env.local.sample"
        echo "📝 EDITE o .env e adicione sua TMDB_API_KEY"
        exit 1
    else
        echo "❌ Opção inválida"
        exit 1
    fi
fi

if ! grep -q "redis://redis:6379" .env; then
    echo "⚠️  Seu .env parece estar configurado para MODO NUVEM"
    echo ""
    echo "Para rodar LOCAL, o Redis deve ser: redis://redis:6379/0"
    echo "DATABASE_URL deve apontar para: postgresql+psycopg2://app:app123@postgres:5432/movies"
    echo ""
    read -p "Continuar mesmo assim? [s/N]: " confirm
    if [ "$confirm" != "s" ] && [ "$confirm" != "S" ]; then
        echo "❌ Abortado. Ajuste seu .env primeiro."
        exit 1
    fi
fi

echo "🚀 Subindo containers no modo LOCAL..."
echo ""

docker compose -f docker-compose.yml -f docker-compose.local.yml "$@"

