from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time

# ------------------------------
# Paramètres à modifier
# ------------------------------
LOCALISATION = "75001"
REQUETE_MEDICALE = "dermatologue"
MAX_RESULTATS = 10

# ------------------------------
# Initialisation Selenium
# ------------------------------
driver = webdriver.Chrome()  # Assurez-vous que chromedriver est dans le PATH
driver.get("https://www.doctolib.fr/")

wait = WebDriverWait(driver, 10)

# ------------------------------
# Gestion du popup cookies
# ------------------------------
try:
    reject_btn = wait.until(
        EC.element_to_be_clickable((By.ID, "didomi-notice-disagree-button"))
    )
    reject_btn.click()
    wait.until(EC.invisibility_of_element_located((By.ID, "didomi-notice-disagree-button")))
except:
    pass

# ------------------------------
# Champ recherche médicale
# ------------------------------
search_input = wait.until(
    EC.presence_of_element_located((By.CSS_SELECTOR, "input.searchbar-input.searchbar-query-input"))
)
search_input.clear()
search_input.send_keys(REQUETE_MEDICALE)
time.sleep(1)  # laisser le temps à l'autocomplétion
search_input.send_keys(Keys.ENTER)

# ------------------------------
# Champ localisation
# ------------------------------
place_input = wait.until(
    EC.presence_of_element_located((By.CSS_SELECTOR, "input.searchbar-input.searchbar-place-input"))
)
place_input.clear()
place_input.send_keys(LOCALISATION)
time.sleep(1)  # laisser le temps à l'autocomplétion
place_input.send_keys(Keys.ENTER)

# Petit temps pour laisser le navigateur traiter
time.sleep(0.5)

# Deuxième Enter pour lancer la recherche
place_input.send_keys(Keys.ENTER)

# ------------------------------
# Pause pour que les résultats se chargent
# ------------------------------
time.sleep(5)

# ------------------------------
# Récupération des résultats
# ------------------------------
data = []


# Récupérer le main
main_section = driver.find_element(By.TAG_NAME, "main")

search_toolbar = main_section.find_element(By.CSS_SELECTOR, 'div[data-test-id="search-toolbar"]')
buttons = search_toolbar.find_elements(By.TAG_NAME, "button")
print(buttons)

if buttons:
    buttons[1].click()
    radio_today = driver.find_element(By.CSS_SELECTOR, "div.dl-modal-body div[data-design-system-component='Radio']:first-child")
    radio_today.click()
    submit_filter = driver.find_element(By.CSS_SELECTOR, "button[data-test-id='submit-filter']")
    submit_filter.click()
else:
    print("Aucun bouton trouvé")
    
time.sleep(5)

# Conteneur principal des résultats dans le main
container = main_section.find_element(By.CSS_SELECTOR, "div.max-w-search-results-container")

doctors = container.find_elements(By.CLASS_NAME, "dl-card")

print(f"{len(doctors)} cartes trouvées dans le main !")

for doctor in doctors:
    try:
        availabilities_container = doctor.find_element(By.CSS_SELECTOR, 'div[data-test-id="availabilities-container"]')
        try:
            next_div = availabilities_container.find_element(By.CSS_SELECTOR, 'div[data-design-system="oxygen"]')
            button = next_div.find_element(By.TAG_NAME, "button")
            dispo = button.find_element(By.CSS_SELECTOR, "span.dl-button-label span").text
        except:
            dispo = "Aucune disponibilité"
    except:
        dispo = "Aucune disponibilité"

    print(dispo)

        
    # récupérer le lien vers la fiche du médecin
    link = doctor.find_element(By.TAG_NAME, "a").get_attribute("href")
    
    # ouvrir la fiche dans un nouvel onglet
    driver.execute_script("window.open(arguments[0], '_blank');", link)
    
    # passer sur le nouvel onglet
    driver.switch_to.window(driver.window_handles[1])
    
    time.sleep(5)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "dl-profile-header"))
        ) 
        nomDiv = driver.find_element(By.CLASS_NAME, "dl-profile-header-name-speciality")
        nom = nomDiv.find_element(By.CLASS_NAME, "dl-text").text
    except:
        nom = ""
    try:
        consultation = "Sur place"
        consultationDiv = driver.find_element(By.CLASS_NAME, "dl-profile-booking-card-wrapper")
        consultationDiv.find_element(By.CSS_SELECTOR, 'div[data-test="telehealth"]')
        consultation = "Sur place et en Vidéo"
    except:
        pass
    cards = driver.find_elements(By.CLASS_NAME, "dl-profile-card")
    if cards:
        first_card = cards[0]
        try:
            p_tags = first_card.find_element(By.CLASS_NAME, "dl-profile-text").find_elements(By.TAG_NAME, "p")
            if p_tags:
                secteur = p_tags[0].text
        except:
            secteur = ""
    try:
        prixTitle = driver.find_element(By.XPATH,'//h2[contains(@class,"dl-profile-card-title") and normalize-space(text())="Tarifs"]')
        prix_card = prixTitle.find_element(By.XPATH, "./ancestor::div[contains(@class, 'dl-profile-card-content')]")
        prix_list = prix_card.find_elements(By.TAG_NAME, "li")
        prix = ", ".join([li.text for li in prix_list]) 
    except:
        prix = ""
    try:
        adresse = doctor.find_element(By.CLASS_NAME, "dl-address").text
        rue = adresse.split(",")[0] if "," in adresse else adresse
        code_ville = adresse.split(",")[1].strip() if "," in adresse else ""
        code_postal = code_ville.split(" ")[0] if code_ville else ""
        ville = " ".join(code_ville.split(" ")[1:]) if code_ville else ""
    except:
        rue = code_postal = ville = ""

    data.append({
        "Nom": nom,
        "Prochaine disponibilité": dispo,
        "Consultation": consultation,
        "Secteur assurance": secteur,
        "Prix": prix,
        "Rue": rue,
        "Code postal": code_postal,
        "Ville": ville
    })
    
    # fermer l'onglet du médecin
    driver.close()
    
    # revenir à la page des résultats
    driver.switch_to.window(driver.window_handles[0])

# ------------------------------
# Export CSV
# ------------------------------
df = pd.DataFrame(data)
df['Prix'] = df['Prix'].str.replace('\n', ' | ', regex=True)
df['Secteur assurance'] = df['Secteur assurance'].str.replace('\n', ' | ', regex=True)
df.to_csv("docteurs.csv", index=False, encoding="utf-8-sig", sep=';')
print("Scraping terminé, fichier docteurs.csv créé !")

# ------------------------------
# Fermeture du navigateur
# ------------------------------
driver.quit()
