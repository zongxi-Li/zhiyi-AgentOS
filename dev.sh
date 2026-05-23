#!/usr/bin/env bash
# 知弈 Docker 开发环境 - Linux/macOS
set -e

ACTION="${1:-up}"

if docker compose version >/dev/null 2>&1; then
  COMPOSE=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE=(docker-compose)
else
  echo "Docker Compose is required. Install Docker Desktop or the docker compose plugin."
  exit 1
fi

case "$ACTION" in
  up)
    echo "Starting development environment..."
    "${COMPOSE[@]}" up -d --build
    echo ""
    echo "Services starting..."
    echo "  Frontend : http://localhost:3000"
    echo "  Backend  : http://localhost:8080"
    echo "  AI       : http://localhost:8000"
    echo "  Postgres : localhost:5432"
    echo "  Redis    : localhost:6379"
    echo ""
    echo "Use './dev.sh logs' to view logs"
    ;;
  down)
    echo "Stopping development environment..."
    "${COMPOSE[@]}" down
    ;;
  build)
    echo "Building all services..."
    "${COMPOSE[@]}" build --no-cache
    ;;
  restart)
    echo "Restarting development environment..."
    "${COMPOSE[@]}" down
    "${COMPOSE[@]}" up -d --build
    ;;
  logs)
    "${COMPOSE[@]}" logs -f --tail=100
    ;;
  clean)
    echo "Cleaning up (stop + remove volumes)..."
    "${COMPOSE[@]}" down -v
    echo "Done. All data removed."
    ;;
  *)
    echo "Usage: ./dev.sh {up|down|build|restart|logs|clean}"
    exit 1
    ;;
esac
