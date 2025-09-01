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

# Conteneur principal des résultats dans le main
container = main_section.find_element(By.CSS_SELECTOR, "div.max-w-search-results-container")

doctors = container.find_elements(By.CLASS_NAME, "dl-card")

print(f"{len(doctors)} cartes trouvées dans le main !")

for doctor in doctors:
    # récupérer le lien vers la fiche du médecin
    link = doctor.find_element(By.TAG_NAME, "a").get_attribute("href")
    
    # ouvrir la fiche dans le même onglet
    driver.get(link)
    
    # attendre que la fiche charge
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "dl-profile-header"))  # exemple
    ) 

    try:
        nomDiv = driver.find_element(By.CLASS_NAME, "dl-profile-header-name-speciality")
        nom = nomDiv.find_element(By.CLASS_NAME, "dl-text").text
    except:
        nom = ""
    try:
        # Par défaut, consultation sur place
        consultation = "Sur place"
        consultationDiv = doctor.find_element(By.CLASS_NAME, "dl-profile-booking-card-wrapper")
        # Vérifier si la consultation vidéo est disponible
        consultationDiv.find_element(By.CSS_SELECTOR, 'div[data-test="telehealth"]')
        consultation = "Sur place,Vidéo"
    except:
        # Si pas de vidéo, on garde seulement "Sur place"
        pass
    try:
        secteur = doctor.find_element(By.CLASS_NAME, "dl-insurance").text
    except:
        secteur = ""
    try:
        prix = doctor.find_element(By.CLASS_NAME, "dl-price").text
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

    try:
        dispo = doctor.find_element(By.CLASS_NAME, "dl-next-available").text
    except:
        dispo = ""

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
    
    # retourner à la page de résultats
    driver.back()
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "dl-card"))
    )

# ------------------------------
# Export CSV
# ------------------------------
df = pd.DataFrame(data)
df.to_csv("docteurs.csv", index=False, encoding="utf-8-sig")
print("Scraping terminé, fichier docteurs.csv créé !")

# ------------------------------
# Fermeture du navigateur
# ------------------------------
driver.quit()
