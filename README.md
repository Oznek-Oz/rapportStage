## Analyse des sites de recherche d'emploi — Rapport de stage

Ce dépôt contient le code et les données utilisés pour l'analyse et le scraping d'offres d'emploi (projet de rapport de stage — Kenzo Tchikaya).

### Objectif

Collecter, nettoyer et analyser des offres d'emploi provenant de plusieurs sites (ex. EmploiCM, CameroonDesk, FNE, Louma Jobs, Minajobs) et fournir un tableau de bord Streamlit pour l'exploration temporelle et géographique des offres.

### Contenu principal

- `main.py` : fonctions de scraping génériques et scrapers par site (EmploiCM, CameroonDesk, FNE, Louma Jobs, Minajobs, ...). Contient aussi des utilitaires de parsing et d'écriture CSV.
- `application_streamlit.py` : dashboard Streamlit pour visualiser et analyser les données (graphiques temporels, géographiques, top entreprises, etc.).
- `app.py` : possible point d'entrée alternatif (vérifier son contenu avant usage).
- `scraping_cameroondesk.py`, `scraping_emploicm.py`, `scraping_fne.py` : scripts dédiés de scraping (exécutables séparément).
- `chromedriver.exe` : binaire Chromedriver (utilisé par Selenium pour certains scrapers). Assurez-vous qu'il correspond à votre version de Chrome.
- `requirements.txt` : liste des dépendances Python requises pour exécuter le projet.
- `offres_emploi*.csv` : exemples/fichiers produits par les scrapers (données d'offres récoltées).
- `src/` : composants réutilisables pour la visualisation et le traitement (ex. `src/components`, `src/utils/data_processor.py`).

### Prérequis

- Windows (instructions données en PowerShell), Python 3.12 recommandé (les dépendances ciblent cette version).
- Google Chrome installé si vous utilisez les scrapers Selenium.

### Installation (rapide)

1. Créer et activer un environnement virtuel (PowerShell) :

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Installer les dépendances :

```powershell
pip install -r requirements.txt
```

Remarque : le fichier `requirements.txt` liste notamment `streamlit`, `folium`, `geopy`, `python-dateutil`, etc.

### Exécution

- Lancer le dashboard Streamlit :

```powershell
streamlit run application_streamlit.py
```

- Exécuter un scraper (exemples) :

```powershell
python scraping_cameroondesk.py
python scraping_emploicm.py
python scraping_fne.py
```

Certains scrapers utilisent Selenium. Si un scraper utilise Selenium, vérifiez que `chromedriver.exe` est compatible et indiquez son chemin si nécessaire dans le script (ou placez-le dans le PATH).

### Sorties attendues

- Fichiers CSV : `offres_emploi.csv`, `offres_emploi_v1.csv`, `offres_emploi_fusion.csv`, etc. Les scrapers appellent une fonction `save_to_file`/`ajouter_offres` qui écrit/append les résultats en CSV.
- Fichiers HTML de sauvegarde pour debug : `cameroondesk.html`, `emploicm.html`, etc.

### Structure rapide des données

Une offre contient typiquement les champs suivants :

- `lien`, `titre`, `compagnie`, `description`, `niveau_etude`, `experience`, `type_contrat`, `lieu`, `date_publication`, `date_expiration`, `origine`

### Points d'attention / limitations

- Certains modules (ex. `src/utils/data_processor.py`) sont présents mais vides ou partiels — vérifier avant d'en dépendre.
- Le scraping dépend fortement de la structure HTML des sites. Les sélecteurs CSS dans `main.py` et les scripts dédiés peuvent nécessiter des mises à jour si les sites changent.
- Geocodage (Nominatim via `geopy`) requiert une connexion internet et peut être limité par rate-limiting.
- Respectez les conditions d'utilisation des sites scrappés et la législation applicable (robots.txt, taux de requêtes, consentement).

### Suggestions / prochaines étapes

- Ajouter un script CLI ou un `__main__` pour orchestrer les scrapers et produire un jeu de données unifié.
- Compléter `src/utils/data_processor.py` pour centraliser le pré-traitement et les exports.
- Ajouter des tests unitaires pour les fonctions critiques de parsing.

### Auteur

Kenzo Tchikaya — Rapport de stage

### Licence

Fichier non accompagné d'une licence explicite dans le dépôt. Si vous souhaitez en ajouter une, créer un fichier `LICENSE` à la racine.

---

Si vous voulez, je peux :
- adapter le README pour inclure des exemples d'exécution précis (avec chemins absolus et options),
- ajouter un script d'installation (`setup.ps1`) ou remplir `src/utils/data_processor.py`.

### Exemples d'exécution détaillés et paramètres Selenium

1) Exécuter le dashboard Streamlit (port par défaut 8501) :

```powershell
streamlit run application_streamlit.py
```

2) Utilisation de Selenium (Chromedriver) — recommandations :

- Vérifiez la version de Google Chrome installée (Aide > À propos de Google Chrome). Téléchargez la version correspondante de Chromedriver et placez `chromedriver.exe` :
	- soit dans un dossier présent dans la variable d'environnement PATH,
	- soit dans le dossier du projet (même répertoire que les scripts),
	- soit indiquez explicitement son chemin dans le script avant d'initialiser le webdriver.

- Exemple d'initialisation explicite (si vous devez fournir le chemin) :

```python
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

chrome_service = Service(executable_path=r"C:\chemin\vers\chromedriver.exe")
chrome_options = Options()
chrome_options.add_argument('--headless')  # optionnel : mode sans tête
driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
```

- Variables d'environnement utiles (PowerShell) :

```powershell
#$env:CHROMEDRIVER_PATH = 'C:\chemin\vers\chromedriver.exe'
# ou ajouter au PATH :
[Environment]::SetEnvironmentVariable('Path', $env:Path + ';C:\chemin\vers', 'User')
```

3) Lancer un scraper qui utilise Selenium

- Si le script attend un chromedriver directement dans le PATH ou au même niveau, placez `chromedriver.exe` dans le dossier du projet et lancez :

```powershell
python scraping_louma.py
```

- Si vous modifiez le script pour accepter un paramètre `--chromedriver`, lancez :

```powershell
python scraping_louma.py --chromedriver "C:\chemin\vers\chromedriver.exe"
```

4) Exemples d'exécution directe pour debug

- Sauvegarder le HTML d'une page (utilisé pour debug dans les scripts) : les scrapers écrivent parfois `cameroondesk.html`, `emploicm.html` dans le répertoire courant.

### Script d'installation PowerShell: `setup.ps1`

Un script PowerShell est fourni pour automatiser la création d'un environnement virtuel et l'installation des dépendances. Il :

- crée `.venv` à la racine du projet,
- active l'environnement (dans la session PowerShell en cours),
- met à jour `pip` et installe les paquets de `requirements.txt`.

Usage (PowerShell) :

```powershell
# Exécuter le script (si nécessaire, débloquer l'exécution temporairement)
.\n+\setup.ps1
```

Après exécution, activez l'environnement si le script ne l'a pas fait dans votre shell :

```powershell
.\.venv\Scripts\Activate.ps1
```

---

Je fournis également `setup.ps1` prêt à l'emploi dans le dépôt.
