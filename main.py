import re

import requests
from bs4 import BeautifulSoup, NavigableString
import random
import csv
import os
import time
from datetime import datetime
import dateparser
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

#Différents utilisateurs
user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]

#Entête pour se faire passer pour un navigateur
headers = {
    'User-Agent': random.choice(user_agents),
    'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language':'fr-FR,fr;q=0.9,en;q=0.8',
    'Accept-Encoding':'gzip, deflate, br',
    'connection': 'keep-alive'
}
#variables globales
#Fonction permettant d'extraire les données
def scrape(url):
    nbre_essai = 3
    for essai in range (nbre_essai):
        try:
            #print(f'url à contacter: {url} ...')
            response = requests.get(url, headers=headers, timeout=30)
            print(f'url contacter: {url} !')
            response.raise_for_status() # Lève une exception si le statut HTTP n'est pas 200
            print(f"Succès à l'essai {essai}")
            # Récupération du contenu HTML
            soup = BeautifulSoup(response.text, 'html5lib')
            return soup

        except requests.RequestException as e:
            print(f"Erreur lors de la requête : {e} avec l'url : {url}")
            print(f"essai numéro {essai}")
            if essai == nbre_essai-1:  # Si c'est le dernier essai
                print("Échec après tous les essais")
                return None
        except Exception as e:
            print(f"Erreur inattendue : {e} avec l'url : {url}")
            print(f"essai numéro {essai}")
            if essai == nbre_essai-1:  # Si c'est le dernier essai
                print("Échec après tous les essais")
                return None
        time.sleep(2)

# Fonction pour tester si un element est vide
def test_if_empty (element):
    if element is None:
        print(f"soup est vide !")
        return []
    else:
        print(f"soup est n'on vide !")



# Fonction pour convertir en une date
def convertir_en_date(relative_date_str):
    """
    Convertit une expression relative comme "il y a 3 jours" ou "6 months ago" en une date exacte.
    Retourne un objet datetime.date correspondant.
    """
    if not relative_date_str:
        return None

    # On utilise dateparser pour analyser les formats relatifs automatiquement
    date = dateparser.parse(relative_date_str, settings={
        'RELATIVE_BASE': datetime.now(),
        'PREFER_DATES_FROM': 'past',
        'TIMEZONE': 'UTC',
        'RETURN_AS_TIMEZONE_AWARE': False
    })

    if date:
        return date.date()
    else:
        return None



#Fonction permettant d'ajouter des offres
def ajouter_offres(offres,lien,titre='',compagnie='',description='',niveau_etude='',experience='',type_contrat='',lieu='',date_publication='',date_expiration='',origine=''):
    print("Ajouter offres ...")
    nouvelle_offres ={
        'lien': lien,
        'titre': titre,
        'compagnie': compagnie,
        'description': description,
        'niveau_etude': niveau_etude,
        'experience': experience,
        'type_contrat': type_contrat,
        'lieu': lieu,
        'date_publication': date_publication,
        'date_expiration': date_expiration,
        'origine': origine
    }
    offres.append(nouvelle_offres)

    save_to_file([nouvelle_offres], 'offres_emploi.csv', 'a')

    print("Nouvelles offres ajoutées !")



def scraper_offres_emploicm(url) :
    soup = scrape(url)
    #test_if_empty(soup)
    #save_to_file(soup, "emploicm.html", 'w', 'html')
    #Récupération des cartes
    cards = soup.select('.card-job')
    
    #Liste des offres
    offres = []
    
    #Récupération des données
    for card in cards :
        lien = card.get('data-href', '') if card.get('data-href' , '') else ''
        titre = card.select_one('.card-job-detail h3').text.strip() if card.select_one('.card-job-detail h3') else ''
        compagnie = card.select_one('.card-job-detail a.card-job-company').text.strip() if card.select_one('.card-job-detail a') else ''
        description = card.select_one('.card-job-detail .card-job-description p').text.strip() if card.select_one('.card-job-detail .card-job-description p') else ''
        niveau_etude = card. select_one('.card-job-detail ul li:nth-child(1) strong').text.strip() if card.select_one('.card-job-detail ul li:nth-child(1) strong') else ''
        experience = card. select_one('.card-job-detail ul li:nth-child(2) strong').text.strip() if card.select_one('.card-job-detail ul li:nth-child(2) strong') else ''
        type_contrat = card. select_one('.card-job-detail ul li:nth-child(3) strong').text.strip() if card.select_one('.card-job-detail ul li:nth-child(3) strong') else ''
        lieu = card. select_one('.card-job-detail ul li:nth-child(4) strong').text.strip() if card.select_one('.card-job-detail ul li:nth-child(4) strong') else ''
        date_publication = card. select_one('.card-job-detail time').text.strip() if card.select_one('.card-job-detail time') else ''
        date_expiration = ''
        origine = 'emploicm'
        
        #Ajout des données à la liste
        ajouter_offres(offres, lien, titre, compagnie, description, niveau_etude, experience, type_contrat, lieu,
                       date_publication, date_expiration, origine)
    return offres
def scrape_all_pages_emploicm(url) :
    scrape_all_pages(url, scraper_offres_emploicm, "query")


def scraper_offres_cameroondesk(url):
    soup = scrape(url)
    test_if_empty(soup)
    save_to_file(soup, "cameroondesk.html", 'w', 'html')
    posts = soup.select('.post-filter')
    offres = []
    for post in posts:
        titre = post.select_one('.entry-title a').text.strip() if post.select_one('.entry-title a') else ''
        date_publication = post.select_one('i.bi-calendar2-minus').text.strip() if post.select_one('i.bi-calendar2-minus') else ''
        lien = post.select_one('a.post-filter-inner').get('href') if post.select_one('a.post-filter-inner') else ''
        description = post.select_one('div.post-snippet').text.strip() if post.select_one('div.post-snippet') else ''
        niveau_etude = ''
        experience = ''
        type_contrat = ''
        lieu = ''
        compagnie = ''
        origine = 'Cameroon Desk'

        ajouter_offres(offres,lien,titre,compagnie,description,niveau_etude,experience,type_contrat,lieu,date_publication,origine)

    return offres


def scraper_offres_jobinfocamer(url):
    soup = scrape(url)
    test_if_empty(soup)
    save_to_file(soup, "jobinfocamer.html", 'w', 'html')
    rows = soup.select('tbody tr')
    offres = []
    for row in rows:
        date_publication = row.select_one('td:nth-child(1) a').text.strip() if row.select_one('td:nth-child(1) a') else ''
        titre = row.select_one('td:nth-child(2) strong').text.strip() if row.select_one('td:nth-child(2) strong') else ''
        #récupération du lieu
        p = row.select_one('td:nth-child(2) p')
        if p:
            a = p.find('a')
            if a and a.next_sibling and isinstance(a.next_sibling, NavigableString):
                lieu = a.next_sibling.strip()
            else:
                lieu = ''
        else:
            lieu = ''
        type_contrat = row.select_one('td:nth-child(3) span').text.strip() if row.select_one('td:nth-child(3) span') else ''
        #récupération de la compagnie
        compagnie=''
        for element in p:
            if element.name == 'a':
                compagnie = element.text.strip()
                break

        lien = row.select_one('td:nth-child(2) a').get('href') if row.select_one('td:nth-child(2) a') else ''

        offres.append({
            'lien': lien,
            'titre': titre,
            'compagnie': compagnie,
            'description': '',
            'niveau_etude': '',
            'experience': '',
            'type_contrat': type_contrat,
            'lieu': lieu,
            'date_publication': date_publication
        })


def scrape_all_offres_fne(url):
    complete_url = ''
    offres = []
    reference = '000001'

    count_type_lien1 = 0
    count_type_lien2 = 0
    type_lien = 2

    while True:
        if type_lien == 1:
            complete_url = f"{url}/jla_afficheoffre.php?reference={reference}"
        elif type_lien == 2:
            complete_url = f"{url}/c_afficheoffre.php?reference=C04-OE-2025-{reference}"
        soup = scrape(complete_url)
        #test_if_empty(soup)

        print("Recherche des tableaux...")
        table = soup.select_one('table div.telecharger_tableau table.table tbody')

        if table is None and int(reference) > 33950 and type_lien == 1:
            count_type_lien1 += 1

        if table is None and type_lien == 2 and int(reference) > 200:
            count_type_lien2 += 1

        if table is not None:
            print("Tableaux trouvés")
            count_type_lien1 = 0
            count_type_lien2 = 0
            lien = complete_url
            titre = table.select_one('tr:nth-child(2) td:nth-child(2) b.text-success').text.strip() if table.select_one(
                'tr:nth-child(2) td:nth-child(2) b.text-success') else ''
            compagnie = ''
            cle = soup.find('td', string=lambda x: x and "Missions / Tâches" in x)
            description = cle.find_next_sibling('td').text.strip() if cle else ''
            cle = soup.find('td', string=lambda x: x and "Formation initiale" in x)
            niveau_etude = cle.find_next_sibling('td').text.strip() if cle else ''
            cle = soup.find('td', string=lambda x: x and "Durée de l'expérience professionnelle" in x)
            experience = cle.find_next_sibling('td').text.strip() if cle else ''
            type_contrat = table.select_one('tr:nth-child(6) td:nth-child(2)').text.strip() if table.select_one(
                'tr:nth-child(6) td:nth-child(2)') else ''

            number_child = 9 if type_lien == 1 else 8

            lieu = table.select_one(f'tr:nth-child({number_child-1}) td:nth-child(2)').text.strip() if table.select_one(
                'tr:nth-child(8) td:nth-child(2)') else ''
            date_publication = ''
            date_expiration = table.select_one(f'tr:nth-child({number_child}) td:nth-child(2)').text.strip() if table.select_one(
                'tr:nth-child(9) td:nth-child(2)') else ''
            print(f"Date d'expiration : {date_expiration}")
            origine = 'FNE'

            ajouter_offres(offres, lien, titre, compagnie, description, niveau_etude, experience, type_contrat, lieu,
                       date_publication, date_expiration, origine)

        if count_type_lien1 == 10 and type_lien == 1 :
            print(f"scraping terminé avec l'url de type {type_lien}: {complete_url}\n")
            type_lien = 2
            reference = '000000'
            print(f"Nombre d'offres : {len(offres)}\n"
                  f"Passons maintenant à l'url de type {type_lien}: {complete_url}\n")

        if count_type_lien2 == 100 :
            print("Opération terminée !")
            break

        reference = incrementer_avec_zeros(reference)

    return offres


def scraper_offres_loumaJobs(url,driver):

    print(f"Connexion à l'url {url}...")
    safe_get(driver, url)
    print("Connexion réussie !")

    print("Récupération des sections...")
    sections_blocks = driver.find_elements(By.CSS_SELECTOR, '.emploi')
    offres = []

    if sections_blocks is not None:
        print("Sections récupérés !")
        for section in sections_blocks:
            lien = section.find_element(By.CSS_SELECTOR, "h3.card_default__title a").get_attribute('href') if section.find_element(By.CSS_SELECTOR,"h3.card_default__title a") else ''
            lieu = section.find_element(By.CSS_SELECTOR,"div.card_default__tags span").text.strip() if section.find_element(By.CSS_SELECTOR,"div.card_default__tags") else ''
            titre = section.find_element(By.CSS_SELECTOR,"h3.card_default__title a").text.strip() if section.find_element(By.CSS_SELECTOR,"h3.card_default__title") else ''
            type_contrat = section.find_element(By.CSS_SELECTOR,".card_default__content p:nth-of-type(2)").text.strip() if section.find_element(By.CSS_SELECTOR,".card_default__content p:nth-of-type(2)") else ''

            date_expiration = section.find_element(By.CSS_SELECTOR,".card_default__datepublication p").text.strip() if section.find_element(By.CSS_SELECTOR,".card_default__datepublication p") else ''
            date_expiration = date_expiration.lower().replace("date cloture : ", "")

            print(f"Connexion à l'url {lien}...")
            soup = scrape(lien)
            print("Connexion réussie !")

            compagnie = soup.select_one("article .entreprise-title h2.h6 a").text.strip() if soup.select_one("article .entreprise-title h2.h6 a") else ''
            compagnie = compagnie.lower().replace("en savoir plus sur", "").strip()

            description = soup.select_one("div.post-content .post-real-content p").text.strip() if soup.select_one("div.post-content .post-real-content p") else ''
            niveau_etude = ''

            experience = soup.select_one("article div:nth-child(4) ul li:nth-child(5) span").text.strip() if soup.select_one("article div:nth-child(4) ul li:nth-child(5) span") else ''
            experience = experience.lower().replace("expérience : ", "")

            date_publication = soup.select_one( "article .entreprise-title span:nth-child(2)").text.strip() if soup.select_one( "article .entreprise-title span:nth-child(2)") else ''
            date_publication = convertir_en_date(date_publication)

            #categorie = soup.select_one("article div:nth-child(4) ul li:nth-child(5) span").text.strip() if soup.select_one("article div:nth-child(4) ul li:nth-child(5) span") else ''
            origine = 'Louma Jobs'

            ajouter_offres(offres, lien, titre, compagnie, description, niveau_etude, experience, type_contrat, lieu,date_publication, date_expiration, origine)

    return offres
def scrape_all_pages_loumaJobs(url,driver):
    scrape_all_pages(url, scraper_offres_loumaJobs, "path", driver=driver, first=827)


def scraper_offres_minajobs(url, driver):

    print(f"Connexion à l'url {url}...")
    safe_get(driver, url)
    print("Connexion réussie !")

    print("Récupération des balises li...")
    balises_li = driver.find_elements(By.CSS_SELECTOR, '.desktop-listing-content')
    offres = []
    offres_temp = []
    liens_offres = []


    for li in balises_li:
        html = li.get_attribute("outerHTML")
        soup = BeautifulSoup(html, 'html.parser')

        titre = soup.select_one(".listing-title").text.strip() if soup.select_one(".listing-title") else ''
        lien = 'https://cameroun.minajobs.net' + soup.select_one("b a").get('href') if soup.select_one("b a") else ''
        liens_offres.append(lien)
        compagnie = soup.select_one("div.listing-info span.opaque").text.strip() if soup.select_one(
            "div.listing-info") else ''
        lieu = soup.select_one("div.listing-info span.opaque:nth-child(4)").text.strip() if soup.select_one(
            "div.listing-info") else ''

        offres_temp.append({
            "titre": titre,
            "lien": lien,
            "compagnie": compagnie,
            "lieu": lieu
        })
    print("Nombre d'offres trouvées :", len(offres_temp))

    for i, offre in enumerate(offres_temp, start=1):
        print(f"Connexion à l'url de l'offre No : {i}: {offre["lien"]}")
        safe_get(driver, offre["lien"])
        soup_lien = BeautifulSoup(driver.page_source, 'html.parser')

        date_publication = soup_lien.select_one('.job-detail-icons .listing-icon:nth-child(2)')
        date_publication = date_publication.next_sibling.strip().replace("Date de publication :",
                                                                         "").strip() if date_publication else ''

        description = soup_lien.select_one("div.detail-font")
        description = description.text.strip() if description else ''

        # Ajout via ta fonction
        ajouter_offres(
            offres=offres,
            lien=offre["lien"],
            titre=offre["titre"],
            compagnie=offre["compagnie"],
            lieu=offre["lieu"],
            date_publication=date_publication,
            description=description,
            origine="minajobs"
        )

    print("Toutes les offres ont été traitées !")
    return offres
def scrape_all_pages_minajobs(url,driver,first):
    scrape_all_pages(url=url, fonction_scraping=scraper_offres_minajobs,  format_page="query" , driver=driver , first=first, type_format="p")


def scraper_offres_optioncarriere():
    def scraper_offres_optioncarriere_region(url):
        print(f"Récupération des offres pour la région : {nom_region}")
        soup = scrape(url)
        print('HTML récupérées pour la région :', nom_region)
        offres = []

        contents = soup.select('#search-content ul.jobs article') if soup else None
        if contents:
            for content in contents:
                lien_offre = 'https://www.optioncarriere.cm' + content.select_one('header a').get(
                    'href') if content.select_one('header a') else ''
                print('lien offres :', lien_offre)
                soup_offre = scrape(lien_offre)
                if soup_offre:
                    article = soup_offre.select_one('article')
                    if article:
                        type_contrat = article.select_one('ul.details li:nth-child(2)').text.strip() if article.select_one(
                            'ul.details li:nth-child(2)') else ''
                        if type_contrat.lower() != 'stage':
                            titre = article.select_one('h1').text.strip() if article.select_one('h1') else ''
                            compagnie = article.select_one('header p.company').text.strip() if article.select_one(
                                'header p.company') else ''
                            lieu = article.select_one('ul.details span').text.strip() if article.select_one(
                                'ul.details span') else ''
                            date_publication = article.select_one('ul.tags span.badge').text.strip() if article.select_one(
                                'ul.tags span.badge') else ''
                            date_publication = convertir_en_date(date_publication)
                            description = article.select_one('section.content').text.strip() if article.select_one(
                                'section.content') else ''

                            ajouter_offres(offres, lien_offre, titre, compagnie, description, niveau_etude='',
                                           experience='', type_contrat=type_contrat, lieu=lieu, date_publication=date_publication,
                                           date_expiration='', origine='optioncarriere')

    regions = (
            {'Littoral': 'https://www.optioncarriere.cm/emploi/R%C3%A9gion-du-Littoral', },
            {'Ouest': 'https://www.optioncarriere.cm/emploi/R%C3%A9gion-de-l%E2%80%99Ouest', },
            {'Nord-Ouest': 'https://www.optioncarriere.cm/emploi/R%C3%A9gion-du-Nord-Ouest', },
            {'Sud-Ouest': 'https://www.optioncarriere.cm/emploi/R%C3%A9gion-du-Sud-Ouest', },
            {'Nord': 'https://www.optioncarriere.cm/emploi/R%C3%A9gion-du-Nord', },
            {'Adamaoua': 'https://www.optioncarriere.cm/emploi/R%C3%A9gion-de-l%E2%80%99Adamaoua', },
            {'Est': 'https://www.optioncarriere.cm/emploi/R%C3%A9gion-de-l%E2%80%99Est', },
            {'Centre': 'https://www.optioncarriere.cm/emploi/R%C3%A9gion-du-Centre', },
            {'Sud': 'https://www.optioncarriere.cm/emploi/R%C3%A9gion-du-Sud', }
        )

    for region in regions:
        for nom_region, url_region in region.items():
            if nom_region == 'Sud':
                scrape_all_pages(url_region, scraper_offres_optioncarriere_region, first=1 , format_page='query', type_format='p')



# Permet d'attendre que la page soit chargée avant de continuer en utilisant selenium
def safe_get(driver, url, max_retries=3, delay=2):
    """
    Tente de charger une URL avec un nombre défini de tentatives et un délai entre chaque.

    :param driver: Instance de WebDriver (ex: webdriver.Chrome())
    :param url: URL à charger
    :param max_retries: Nombre maximum de tentatives
    :param delay: Délai (en secondes) entre chaque tentative
    """
    for attempt in range(1, max_retries + 1):
        try:
            driver.get(url)
            return  # Succès
        except Exception as e:
            print(f"[Tentative {attempt}/{max_retries}] Échec : {e}")
            if attempt == max_retries:
                print("Toutes les tentatives ont échoué.")
                raise
            time.sleep(delay)

#Fonction permettant de parcourir les pages
def scrape_all_pages(url, fonction_scraping , format_page, driver=None, first = 0, type_format = "page"):
    choice_format = ''
    page = first
    count_not_offre = 0

    while True:
        if format_page == "path":
            choice_format = f"{url}/page/{page + 1}"
        elif format_page == "query":
            choice_format = f"{url}?{type_format}={page}"

        url_page = choice_format

        print(f"Scraping page {page}...")
        #print(f"Connexion à l'url {url_page}")
        offres_page = fonction_scraping(url_page) if driver == None else fonction_scraping(url_page,driver)

        count_not_offre = (count_not_offre + 1) if not offres_page else 0

        if not offres_page and count_not_offre > 5:
            print("Fin de la pagination !")
            break
        print("Données ajoutées !")
        print('Repos !')
        page += 1

        time.sleep(2)
        print('Reprise...')
    return "Scraping terminé !"

#Enregistrement des données dans un fichier CSV
def save_to_file(offres, filename, save_type='w', extension='csv'):
    if extension == 'csv':
        if offres:
            file_exists = os.path.exists(filename)
            is_empty = not file_exists or os.path.getsize(filename) == 0

            with open(filename, save_type, newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=offres[0].keys())
                if save_type == 'w' or is_empty:
                    writer.writeheader()
                writer.writerows(offres)
            print("Données enregistrées avec succès !")

    elif extension == 'html':
        with open(filename, save_type, encoding='utf-8') as f:
            f.write(offres)
        print("Contenu HTML enregistré avec succès !")

def incrementer_avec_zeros(nombre_str):
    longueur = len(nombre_str)
    nombre = int(nombre_str)
    incremente = nombre + 1
    return str(incremente).zfill(longueur)

# Fonction permettant de piloter le navigateur
def start_browser():
    # Chemin vers le chromedriver local
    chemin_driver = os.path.join(os.getcwd(), "chromedriver.exe")  # ou "chromedriver" sous Linux/macOS
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--headless")

    service = Service(executable_path=chemin_driver)
    driver = webdriver.Chrome(service=service, options=options)
    return driver

# Fonction permettant de convertir des expressions régulière ou non en date
def convertir_en_date(relative_date_str):
    """
    Convertit une expression relative comme "il y a 3 jours" ou "6 months ago" en une date exacte.
    Retourne un objet datetime.date correspondant.
    """
    if not relative_date_str:
        return None

    # 🔹 Nettoyer la chaîne : extraire uniquement la partie utile
    # Exemple : "publié il y a 45 minutes." → "il y a 45 minutes"
    match = re.search(r"(il y a .+|.+ ago)", relative_date_str.lower())
    if match:
        relative_date_str = match.group(1)

    # 🔹 Utiliser dateparser
    date = dateparser.parse(relative_date_str, settings={
        'RELATIVE_BASE': datetime.now(),
        'PREFER_DATES_FROM': 'past',
        'TIMEZONE': 'UTC',
        'RETURN_AS_TIMEZONE_AWARE': False
    })

    if date:
        return date.date()
    else:
        return None

"""examples = [
    'il y a 1 heure',
    '6 months ago',
    '3 days ago',
    'il y a 2 semaines',
    '1 an auparavant',
    'hier',
    'today',
    'avant-hier'
]

for e in examples:
    print(f"'{e}' => {convertir_en_date(e)}")"""
