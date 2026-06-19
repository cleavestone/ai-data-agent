#!/bin/bash
# ─────────────────────────────────────────────────────────────
# dev.sh — manage the development environment
# Usage:
#   ./dev.sh up       start all dev services
#   ./dev.sh down     stop all services
#   ./dev.sh restart  restart all services
#   ./dev.sh logs     tail logs from all services
#   ./dev.sh clean    stop + remove volumes (DELETES ALL DATA)
#   ./dev.sh ps       show running containers and their status
# ─────────────────────────────────────────────────────────────

set -e  # exit immediately if any command fails

COMPOSE="docker compose -f docker-compose.yml -f docker-compose.dev.yml"

case "$1" in
  up)
    echo "Starting dev environment..."
    $COMPOSE up -d
    echo ""
    echo "Services running:"
    echo "  Postgres  → localhost:5432"
    echo "  Redis     → localhost:6379"
    echo "  pgAdmin   → http://localhost:5050"
    ;;

  down)
    echo "Stopping dev environment..."
    $COMPOSE down
    ;;

  restart)
    echo "Restarting dev environment..."
    $COMPOSE down
    $COMPOSE up -d
    ;;

  logs)
    $COMPOSE logs -f
    ;;

  logs:postgres)
    $COMPOSE logs -f postgres
    ;;

  logs:redis)
    $COMPOSE logs -f redis
    ;;

  clean)
    echo "WARNING: This will delete all data including the database."
    read -p "Are you sure? (yes/no): " confirm
    if [ "$confirm" = "yes" ]; then
      $COMPOSE down -v
      echo "All containers and volumes removed."
    else
      echo "Cancelled."
    fi
    ;;

  ps)
    $COMPOSE ps
    ;;

  *)
    echo "Usage: ./dev.sh {up|down|restart|logs|logs:postgres|logs:redis|clean|ps}"
    exit 1
    ;;
esac