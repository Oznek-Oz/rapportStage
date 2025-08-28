from main import start_browser, scrape_all_pages_minajobs

url = "https://cameroun.minajobs.net/offres-emplois-stages"
print("Contact au driver...")
driver = start_browser()
print("driver contacté !")

scrape_all_pages_minajobs(url , driver, first=300)

driver.close()