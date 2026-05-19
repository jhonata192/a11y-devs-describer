@echo off
setlocal enabledelayedexpansion

set PIP_REQUIREMENTS=requirements.txt
set OPENCODE_URL=http://127.0.0.1:4096

echo ========================================
echo   Bot Acess — Instalacao automatica
echo ========================================
echo.

REM ── 1. Verificar OpenCode serve ──
echo [...] Verificando OpenCode serve...
curl -s -o nul -w "%%{http_code}" "%OPENCODE_URL%/global/health" | findstr "200" >nul
if %errorlevel% equ 0 (
    echo [OK] OpenCode serve esta em execucao.
) else (
    echo [AVISO] OpenCode serve nao detectado em %OPENCODE_URL%
    echo         Certifique-se de que o OpenCode esta instalado e execute:
    echo         opencode serve --port 4096 --hostname 127.0.0.1
    echo.
    echo         Deseja continuar mesmo assim? (S/N)
    set /p CONTINUE=
    if /i not "!CONTINUE!"=="S" (
        exit /b 1
    )
)

REM ── 2. Dependencias Python ──
pip --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [...] Instalando dependencias Python...
    pip install -r %PIP_REQUIREMENTS%
    echo [OK] Dependencias instaladas.
) else (
    echo [AVISO] pip nao encontrado. Instale as dependencias manualmente:
    echo          pip install -r %PIP_REQUIREMENTS%
)

REM ── 3. Verificar .env ──
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
