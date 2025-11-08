from playwright.sync_api import sync_playwright
from urllib.parse import quote_plus
import time
from regex.utils import fuzzy_score
import json


URL="https://www.coursesu.com/recherche?q="

def get_price_u(city: str, item: dict):
    
    query = f"{item.get('name', '')} {item.get('brand', '')} {item.get('quantity', '')}".strip()
    url = f"{URL}{quote_plus(query)}"

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=['--incognito']
        )
        context = browser.new_context(user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        ))
        page = context.new_page()
        page.goto(url, wait_until="networkidle", timeout=45000)

        # Gérer la popup cookies
        try:
            if page.is_visible('button:has-text("Continuer sans accepter")'):
                page.click('button:has-text("Continuer sans accepter")')
            elif page.is_visible('button:has-text("Tout accepter")'):
                page.click('button:has-text("Tout accepter")')
            time.sleep(1)
        except:
            pass

        # Traitement spécifique Super U
        processing_superu(page, city)

        # Attendre les articles
        try:
            page.wait_for_selector("li.grid-tile", timeout=30000)
        except:
            print("Aucun produit trouvé pour", query)
            return "", "", False

        articles = page.query_selector_all("li.grid-tile")
        results = []

        for a in articles[:5]:
            try:
                # Nom du produit
                name_element = a.query_selector(".product-name .name-link")
                name = name_element.inner_text().strip() if name_element else ""
                
                # Marque (extraire de data-tc-product-tile ou du nom)
                brand = ""
                data_tc = a.get_attribute("data-tc-product-tile")
                if data_tc:
                    import json
                    try:
                        data = json.loads(data_tc)
                        brand = data.get("brand", "")
                    except:
                        pass
                
                # Si pas de marque trouvée dans les données, essayer d'extraire du nom
                if not brand and name:
                    # Rechercher des marques communes dans le nom
                    common_brands = ["BARILLA", "PANZANI", "LU", "DANONE", "PRESIDENT", "YOPLAIT"]
                    for b in common_brands:
                        if b in name.upper():
                            brand = b
                            break
                
                # Prix
                price_element = a.query_selector("[data-sup-product-price]")
                if price_element:
                    price_text = price_element.inner_text().strip().replace("€", "").replace(",", ".").strip()
                    price = float(price_text)
                else:
                    continue

                full_text = f"{name} {brand}"
                score = fuzzy_score(query, full_text)

                results.append({
                    "name": name,
                    "brand": brand,
                    "price": price,
                    "score": score
                })
            except Exception as e:
                print(f"Erreur lors du traitement d'un article : {e}")
                continue

        browser.close()

        if not results:
            return "", "", False

        bests = sorted(results[:5], key=lambda x: x["score"], reverse=True)
        bests_sorted_by_price = sorted(bests[:3], key=lambda x: x["price"])
        highest_price = bests_sorted_by_price[0]["price"]
        lowest_price = bests_sorted_by_price[-1]["price"]
        return highest_price, lowest_price, True


def processing_superu(page, city):
    try:
        # Cliquer sur "Trouver votre magasin"
        if page.is_visible('a:has-text("Trouver votre magasin")'):
            page.click('a:has-text("Trouver votre magasin")')
            time.sleep(2)
            
            # Attendre que l'input de recherche de magasin soit visible
            page.wait_for_selector('#store-search', timeout=10000)
            
            time.sleep(1)
            # Saisir le nom de la ville dans l'input
            page.fill('#store-search', city)
            time.sleep(1)
            
            # Appuyer sur Retour arrière pour supprimer la dernière lettre
            page.press('#store-search', 'Backspace')
            time.sleep(0.5)
            
            # Remettre la dernière lettre du nom de la ville
            if city:
                last_letter = city[-1]
                page.type('#store-search', last_letter)
                time.sleep(0.5)
            
            # Appuyer sur Entrée pour valider
            page.press('#store-search', 'Enter')
            time.sleep(2)
            
            # Cliquer sur le premier élément avec la classe "store-delivery-mode-arrow"
            page.wait_for_selector('.store-delivery-mode-arrow', timeout=10000)
            first_store_element = page.query_selector('.store-delivery-mode-arrow')
            if first_store_element:
                first_store_element.click()
                time.sleep(2)
                
                # Cliquer sur le bouton de fermeture
                close_button = page.query_selector('span.ui-button-icon.ui-icon.ui-icon-closethick')
                if close_button:
                    close_button.click()
                    time.sleep(1)
                else:
                    print("⚠️ Bouton de fermeture non trouvé")
            else:
                print("⚠️ Aucun magasin trouvé avec la classe store-delivery-mode-arrow")
            
    except Exception as e:
        print(f"⚠️ Erreur lors de la sélection du magasin Super U : {e}")
    return


# Test de la fonction
if __name__ == "__main__":
    item = {"name": "Oeufs de caille", "brand": "", "quantity": ""}
    best = get_price_u("Vaucresson", item)
    print(best)