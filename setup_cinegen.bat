@echo off
chcp 65001 >nul
title 🎬 CINEGEN - INSTALADOR OFICIAL
color 0b

echo.
echo =========================================================================
echo       ⚡ CINEGEN :: AUTONOMOUS AI CINEMA STUDIO - SETUP AUTOMÁTICO ⚡
echo =========================================================================
echo  Desenvolvido por NarraVox Studios - Otimizado para NVIDIA RTX (6GB VRAM)
echo =========================================================================
echo.

:: 1. Verificação do Python
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    color 0c
    echo.
    echo ❌ ERRO CRÍTICO: Python não foi encontrado no PATH do Windows!
    echo    Por favor, instale o Python 3.10, 3.11 ou 3.12 em https://www.python.org/
    echo    Lembre-se de marcar a opção "Add Python to PATH" durante a instalação.
    echo.
    pause
    exit /b 1
)

:: 2. Inicia o Instalador Visual com Botão e Terminal de Logs
echo 🚀 Abrindo Interface Visual do Instalador CineGen Studio...
echo    (Uma janela será aberta com o botão de instalação e terminal de logs)
echo.
python cinegen_installer.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ⚠️ A interface gráfica foi encerrada. Se desejar rodar a instalação
    echo    diretamente pelo terminal, pressione qualquer tecla para continuar...
    pause >nul
    python -m venv venv_cinegen
    call venv_cinegen\Scripts\activate.bat
    python -m pip install --upgrade pip
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
    pip install -r requirements.txt
    echo ✅ Instalação via terminal concluída!
    pause
)
