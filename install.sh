#!/usr/bin/env bash
set -euo pipefail

MODEL="moondream"
PIP_REQUIREMENTS="requirements.txt"

echo "========================================"
echo "  Bot Acess — Instalacao automatica"
echo "========================================"
echo ""

# ── 1. Verificar/instalar Ollama ──
if command -v ollama &>/dev/null; then
    echo "[OK] Ollama ja instalado."
else
    echo "[...] Instalando Ollama..."
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        curl -fsSL https://ollama.com/install.sh | sh
    else
        echo "[ERRO] Este script e para Linux. Use install.bat no Windows."
        exit 1
    fi
fi

# ── 2. Iniciar Ollama (caso nao esteja rodando) ──
if ! ollama list &>/dev/null; then
    echo "[...] Iniciando servico Ollama..."
    nohup ollama serve &>/dev/null &
    sleep 3
fi

# ── 3. Baixar modelo ──
echo "[...] Baixando modelo ${MODEL} (pode levar alguns minutos)..."
ollama pull "$MODEL"
echo "[OK] Modelo ${MODEL} baixado."

# ── 4. Dependencias Python ──
if command -v pip &>/dev/null; then
    echo "[...] Instalando dependencias Python..."
    pip install -r "$PIP_REQUIREMENTS"
    echo "[OK] Dependencias instaladas."
else
    echo "[AVISO] pip nao encontrado. Instale as dependencias manualmente:"
    echo "        pip install -r $PIP_REQUIREMENTS"
fi

# ── 5. Verificar .env ──
if [ ! -f ".env" ]; then
    echo "[AVISO] Arquivo .env nao encontrado."
    echo "        Copie .env.example para .env e configure o BOT_TOKEN."
fi

echo ""
echo "========================================"
echo "  Instalacao concluida!"
echo "  Execute: python run.py"
echo "========================================"
