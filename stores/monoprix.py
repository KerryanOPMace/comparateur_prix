import time
from urllib.parse import quote_plus
from regex.utils import fuzzy_score
from playwright.sync_api import sync_playwright

URL = "https://courses.monoprix.fr/search?q="

def get_price_monoprix(city: str, item: dict):
    
    query = f"{item.get('name', '')} {item.get('brand', '')} {item.get('quantity', '')}".strip()
    url = f"{URL}{quote_plus(query)}"
    print(f"Recherche Monoprix : {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--incognito'])
        context = browser.new_context(user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        ))
        page = context.new_page()
        page.goto(url, wait_until="networkidle", timeout=10000)

        # Gérer la popup cookies
        try:
            if page.is_visible('button:has-text("Continuer sans accepter")'):
                page.click('button:has-text("Continuer sans accepter")')
            elif page.is_visible('button:has-text("Tout accepter")'):
                page.click('button:has-text("Tout accepter")')
            elif page.is_visible('button:has-text("Accepter")'):
                page.click('button:has-text("Accepter")')
            time.sleep(1)
        except:
            pass

        # Attendre les articles
        try:
            page.wait_for_selector("div[data-test^='fop-wrapper:']", timeout=5000)
        except:
            print("Aucun produit trouvé pour", query)
            return "", "", False

        articles = page.query_selector_all("div[data-test^='fop-wrapper:']")
        results = []

        for a in articles[:5]:
            try:
                # Nom du produit
                name_element = a.query_selector("h3[data-test='fop-title']")
                name = name_element.inner_text().strip() if name_element else ""
                
                # Prix
                price_element = a.query_selector("span[data-test='fop-price']")
                if price_element:
                    price_text = price_element.inner_text().strip()
                    # Nettoyer le prix : "4,55 €" -> "4.55"
                    price_text = price_text.replace("€", "").replace(",", ".").replace("\u00a0", "").strip()
                    price = float(price_text)
                else:
                    continue
                
                full_text = f"{name}"
                score = fuzzy_score(query, full_text)

                results.append({
                    "name": name,
                    "price": price,
                    "score": score
                })
            except Exception as e:
                print(f"Erreur lors du traitement d'un article Monoprix : {e}")
                continue

        browser.close()

        if not results:
            return "", "", False

        bests = sorted(results[:5], key=lambda x: x["score"], reverse=True)
        bests_sorted_by_price = sorted(bests[:3], key=lambda x: x["price"])
        highest_price = bests_sorted_by_price[0]["price"]
        lowest_price = bests_sorted_by_price[-1]["price"]
        return highest_price, lowest_price, True


# Test de la fonction
if __name__ == "__main__":
    item = {"name": "Nutella", "brand": "", "quantity": "400g"}
    best = get_price_monoprix("", item)
    print(best)