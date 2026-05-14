@echo off
setlocal enabledelayedexpansion

set MODEL=moondream
set PIP_REQUIREMENTS=requirements.txt

echo ========================================
echo   Bot Acess — Instalacao automatica
echo ========================================
echo.

REM ── 1. Verificar/instalar Ollama ──
ollama --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Ollama ja instalado.
) else (
    choco --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERRO] Chocolatey nao encontrado. Instale o Chocolatey primeiro:
        echo        https://chocolatey.org/install
        pause
        exit /b 1
    )
    echo [...] Instalando Ollama via Chocolatey...
    choco install ollama -y
    if %errorlevel% neq 0 (
        echo [ERRO] Falha ao instalar via Chocolatey. Instale manualmente:
        echo        https://ollama.com/download
        pause
        exit /b 1
    )
    echo [OK] Ollama instalado.
)

REM ── 2. Aguardar Ollama iniciar ──
echo [...] Aguardando servico Ollama...
:wait_ollama
timeout /t 2 /nobreak >nul
ollama list >nul 2>&1
if %errorlevel% neq 0 goto wait_ollama
echo [OK] Ollama em execucao.

REM ── 3. Baixar modelo ──
echo [...] Baixando modelo %MODEL% (pode levar alguns minutos)...
ollama pull %MODEL%
echo [OK] Modelo %MODEL% baixado.

REM ── 4. Dependencias Python ──
pip --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [...] Instalando dependencias Python...
    pip install -r %PIP_REQUIREMENTS%
    echo [OK] Dependencias instaladas.
) else (
    echo [AVISO] pip nao encontrado. Instale as dependencias manualmente:
    echo          pip install -r %PIP_REQUIREMENTS%
)

REM ── 5. Verificar .env ──
if not exist ".env" (
    echo [AVISO] Arquivo .env nao encontrado.
    echo          Copie .env.example para .env e configure o BOT_TOKEN.
)

echo.
echo ========================================
echo   Instalacao concluida!
echo   Execute: python run.py
echo ========================================
pause
