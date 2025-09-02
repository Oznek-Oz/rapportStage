<#
  setup.ps1
  Script PowerShell pour initialiser l'environnement Python du projet.

  Actions :
  - crée un virtualenv dans `.venv`
  - met à jour pip
  - installe les dépendances depuis `requirements.txt`

  Usage : Ouvrir PowerShell dans le dossier du projet puis :
    .\setup.ps1

  Si l'exécution de scripts est restreinte, lancer PowerShell en administrateur et exécuter :
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  puis relancer le script.
#>

Param(
    [string]$VenvPath = ".venv",
    [string]$Requirements = "requirements.txt"
)

Write-Host "== Initialisation de l'environnement Python ==" -ForegroundColor Cyan

if (-Not (Test-Path "$VenvPath")) {
    Write-Host "Création du virtualenv dans $VenvPath..."
    python -m venv $VenvPath
} else {
    Write-Host "Virtualenv $VenvPath existe déjà, je le réutilise."
}

$activate = Join-Path $VenvPath 'Scripts\Activate.ps1'
if (Test-Path $activate) {
    Write-Host "Activation de l'environnement virtuel..."
    # Active pour la session actuelle
    & $activate
} else {
    Write-Host "Fichier d'activation introuvable : $activate" -ForegroundColor Yellow
}

Write-Host "Mise à jour de pip..."
python -m pip install --upgrade pip

if (Test-Path $Requirements) {
    Write-Host "Installation des dépendances depuis $Requirements..."
    pip install -r $Requirements
} else {
    Write-Host "Fichier $Requirements introuvable. Veuillez vérifier." -ForegroundColor Yellow
}

Write-Host "Configuration terminée. Pour activer manuellement l'environnement :" -ForegroundColor Green
Write-Host ".\$VenvPath\Scripts\Activate.ps1" -ForegroundColor Green

Write-Host "Remarque : si vous utilisez Selenium, vérifiez que 'chromedriver.exe' est compatible avec votre version de Chrome." -ForegroundColor Cyan
