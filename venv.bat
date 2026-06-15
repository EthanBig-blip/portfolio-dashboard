@echo off
chcp 65001 >nul
title Portfolio Dashboard — venv

echo.
echo  Activation du venv...

if not exist "venv\Scripts\activate.bat" (
    echo  ERREUR : venv introuvable.
    echo  Lance d'abord : python -m venv venv
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

echo  venv actif. Tu peux lancer tes commandes.
echo  (tape 'deactivate' pour quitter le venv)
echo.

cmd /k
