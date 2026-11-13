@echo off
setlocal
cd /d "%~dp0"
title Generador Autónomo Banner SOMBRA

echo ===================================================
echo Lanzando generacion de banner para SOMBRA...
echo ===================================================

python generar_siguiente_banner.py

echo.
echo Proceso finalizado.

