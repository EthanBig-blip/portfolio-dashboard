@echo off
chcp 65001 >nul
title Portfolio Dashboard

echo.
echo  ╔══════════════════════════════════════╗
echo  ║      Portfolio Dashboard             ║
echo  ╚══════════════════════════════════════╝
echo.

:: -- 1. Git pull --
echo [1/4] Mise a jour du depot...
git pull
if errorlevel 1 (
    echo  AVERTISSEMENT : git pull a echoue, on continue avec la version locale.
)
echo.

:: -- 2. Activer le venv --
echo [2/4] Activation de l'environnement virtuel...
if not exist "venv\Scripts\activate.bat" (
    echo  ERREUR : venv introuvable. Lance d'abord :
    echo    python -m venv venv
    echo    venv\Scripts\activate
    echo    pip install -r requirements.txt
    pause
    exit /b 1
)
call venv\Scripts\activate.bat
echo.

:: -- 3. Install / mise a jour des dependances --
echo [3/4] Verification des dependances...
pip install -r requirements.txt -q
echo.

:: -- 4. Lancer le serveur --
echo [4/4] Demarrage du serveur...
echo.
echo  ► Ouvre ton navigateur sur : http://localhost:8000
echo  ► Portefeuille manuel      : http://localhost:8000/portefeuille
echo  ► Ctrl+C pour arreter
echo.

:: Ouvre le navigateur apres 2 secondes
start "" /b cmd /c "timeout /t 2 >nul && start http://localhost:8000"

uvicorn backend.main:app --reload --port 8000

pause
