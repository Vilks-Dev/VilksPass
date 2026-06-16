@echo off
echo Installation de VilksPass...

:: Vérifier si Python est installé
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERREUR] Python n'est pas installe ou n'est pas dans le PATH.
    pause
    exit /b
)

:: Créer un environnement virtuel
echo Creation de l'environnement virtuel...
python -m venv venv

:: Activer l'environnement et installer les requirements
echo Installation des dependances...
call venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo ========================================================
echo Installation terminee avec succes !
echo Pour lancer le programme, executez : start_vilks.bat
echo ========================================================
pause