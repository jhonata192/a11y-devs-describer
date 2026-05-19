#!/usr/bin/env bash
set -euo pipefail

PIP_REQUIREMENTS="requirements.txt"
OPENCODE_URL="http://127.0.0.1:4096"

echo "========================================"
echo "  Bot Acess — Instalacao automatica"
echo "========================================"
echo ""

# ── 1. Verificar OpenCode serve ──
echo "[...] Verificando OpenCode serve..."
if curl -sf "${OPENCODE_URL}/global/health" > /dev/null 2>&1; then
    echo "[OK] OpenCode serve esta em execucao."
else
    echo "[AVISO] OpenCode serve nao detectado em ${OPENCODE_URL}"
    echo "        Certifique-se de que o OpenCode esta instalado e execute:"
    echo "        opencode serve --port 4096 --hostname 127.0.0.1"
    echo ""
    echo "        Deseja continuar mesmo assim? (s/n)"
    read -r CONTINUE
    if [ "$CONTINUE" != "s" ] && [ "$CONTINUE" != "S" ]; then
        exit 1
    fi
fi

# ── 2. Dependencias Python ──
if command -v pip &>/dev/null; then
    echo "[...] Instalando dependencias Python..."
    pip install -r "$PIP_REQUIREMENTS"
    echo "[OK] Dependencias instaladas."
else
    echo "[AVISO] pip nao encontrado. Instale as dependencias manualmente:"
    echo "        pip install -r $PIP_REQUIREMENTS"
fi

# ── 3. Verificar .env ──
if [ ! -f ".env" ]; then
    echo "[AVISO] Arquivo .env nao encontrado."
    echo "        Copie .env.example para .env e configure o BOT_TOKEN."
fi

echo ""
echo "========================================"
echo "  Instalacao concluida!"
echo "  Execute: python run.py"
echo "========================================"
