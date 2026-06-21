#!/bin/bash

# VANTAGE LAYER_1 — Pipeline Notion (core) v7.5
# Uso: layer_1_pipeline.sh [status|analytics|batch|recovery|profile|feed|backfill]

LAYER_1_DIR="${LAYER_1_DIR:-$HOME/Documents/04-VANTAGE_CV/LAYER_1}"

run_module() {
    local script="$1"
    local label="$2"

    if [ ! -d "$LAYER_1_DIR" ]; then
        echo "❌ Error: $LAYER_1_DIR no encontrado"
        exit 1
    fi

    cd "$LAYER_1_DIR" || exit 1

    if [ ! -d ".venv" ]; then
        echo "❌ Error: Virtual environment no encontrado en $LAYER_1_DIR/.venv"
        echo "💡 Ejecuta: python3 -m venv .venv && pip install -r requirements.txt"
        exit 1
    fi

    source .venv/bin/activate

    if [ ! -f "scripts/$script" ]; then
        echo "❌ Error: scripts/$script no encontrado"
        exit 1
    fi

    echo "$label"
    echo ""
    python3 "scripts/$script"
    local exit_code=$?

    if [ $exit_code -eq 0 ]; then
        echo ""
        echo "✅ Completado: $script"
    else
        echo ""
        echo "❌ Falló: $script — revisar errores arriba"
        exit $exit_code
    fi
}

case "$1" in
    status)
        echo "📊 Generando reporte de status..."
        run_module "status_report.py" "📊 Status Report"
        ;;
    analytics)
        echo "📊 Generando análisis de fuentes..."
        run_module "source_analytics.py" "📊 Source Analytics"
        ;;
    batch)
        echo "🔄 Ejecutando operaciones batch..."
        run_module "batch_operations.py" "🔄 Batch Operations"
        ;;
    recovery)
        echo "🔧 Verificando estado del sistema..."
        run_module "pipeline_recovery.py" "🔧 Pipeline Recovery"
        ;;
    profile)
        echo "🔄 Gestionando evolución de perfil..."
        run_module "profile_evolution.py" "🔄 Profile Evolution"
        ;;
    backfill)
        echo "🔄 Backfill Class A (layer · hash)..."
        if [ ! -d "$LAYER_1_DIR" ]; then
            echo "❌ Error: $LAYER_1_DIR no encontrado"
            exit 1
        fi
        cd "$LAYER_1_DIR" || exit 1
        source .venv/bin/activate
        python3 scripts/backfill_class_a.py "${@:2}"
        exit $?
        ;;
    feed)
        FEED_FILE="${2:?'Uso: layer_1_pipeline.sh feed YYYY-MM-DD_feed.json'}"
        if [ ! -d "$LAYER_1_DIR" ]; then
            echo "❌ Error: $LAYER_1_DIR no encontrado"
            exit 1
        fi
        cd "$LAYER_1_DIR" || exit 1
        if [ ! -d ".venv" ]; then
            echo "❌ Error: Virtual environment no encontrado en $LAYER_1_DIR/.venv"
            exit 1
        fi
        source .venv/bin/activate
        if [ ! -f "scripts/feed_processor.py" ]; then
            echo "❌ Error: scripts/feed_processor.py no encontrado"
            exit 1
        fi
        # Soporte para ruta absoluta o relativa
        if [[ "$FEED_FILE" = /* ]]; then
            FEED_PATH="$FEED_FILE"
        else
            FEED_PATH="feeds/$FEED_FILE"
        fi
        echo "📥 Procesando feed: $FEED_PATH (Layer ${3:-1})"
        echo ""
        python3 scripts/feed_processor.py --file "$FEED_PATH" --layer "${3:-1}"
        exit_code=$?
        if [ $exit_code -eq 0 ]; then
            echo ""
            echo "✅ Completado: feed_processor.py"
        else
            echo ""
            echo "❌ Falló: feed_processor.py — revisar errores arriba"
            exit $exit_code
        fi
        ;;
    "")
        echo "🚀 Iniciando VANTAGE LAYER_1 Pipeline..."
        echo "=================================="

        if [ ! -d "$LAYER_1_DIR" ]; then
            echo "❌ Error: $LAYER_1_DIR no encontrado"
            exit 1
        fi

        cd "$LAYER_1_DIR" || exit 1

        if [ ! -d ".venv" ]; then
            echo "❌ Error: Virtual environment no encontrado"
            exit 1
        fi

        source .venv/bin/activate

        if [ ! -f "config/layer_1.env" ] && [ ! -f ".env" ]; then
            echo "❌ Error: config/layer_1.env no encontrado"
            exit 1
        fi

        if [ ! -f "scripts/layer_1_run.py" ]; then
            echo "❌ Error: scripts/layer_1_run.py no encontrado"
            exit 1
        fi

        echo "📊 Ejecutando pipeline v7.5 (layer_1_run.py)..."
        echo ""
        python3 scripts/layer_1_run.py

        if [ $? -eq 0 ]; then
            echo ""
            echo "✅ Pipeline v7.5 completado"
            echo "👉 Notion: Pipeline Activo · Score >= 60 · revisar Fuente en Inbound"
            echo "=================================="
        else
            echo ""
            echo "❌ Pipeline falló. Revisar errores arriba."
            exit 1
        fi
        ;;
    *)
        echo "❌ Comando desconocido: $1"
        echo "Uso: layer_1_pipeline.sh [status|analytics|batch|recovery|profile|feed|backfill]"
        exit 1
        ;;
esac
