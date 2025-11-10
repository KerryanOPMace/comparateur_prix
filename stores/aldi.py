import time
from urllib.parse import quote_plus
from regex.utils import fuzzy_score
from playwright.sync_api import sync_playwright

URL="https://www.aldi.fr/recherche.html?query="

def get_price_aldi(city: str, item: dict):
    
    query = f"{item.get('name', '')} {item.get('brand', '')}".strip()
    url = f"{URL}{quote_plus(query)}"
    print(f"Recherche ALDI : {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--incognito'])
        context = browser.new_context(user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        ))
        page = context.new_page()
        page.goto(url, wait_until="networkidle", timeout=20000)

        # Gérer la popup cookies
        try:
            if page.is_visible('button:has-text("Continuer sans accepter")'):
                page.click('button:has-text("Continuer sans accepter")')
            elif page.is_visible('button:has-text("Tout accepter")'):
                page.click('button:has-text("Tout accepter")')
            time.sleep(1)
        except:
            pass

        # Attendre les articles
        try:
            page.wait_for_selector("div.product-tile", timeout=20000)
        except:
            print("Aucun produit trouvé pour", query)
            return "", "", False

        articles = page.query_selector_all("div.product-tile")
        results = []

        for a in articles[:5]:
            try:
                # Nom du produit
                name_element = a.query_selector("h2.product-tile__content__upper__product-name")
                name = name_element.inner_text().strip() if name_element else ""
                
                # Marque (peut être vide chez Aldi)
                brand_element = a.query_selector("p.product-tile__content__upper__brand-name")
                brand = brand_element.inner_text().strip() if brand_element else ""
                
                # Prix
                price_element = a.query_selector("span.tag__label--price")
                if price_element:
                    price_text = price_element.inner_text().strip().replace(",", ".")
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
                print(f"Erreur lors du traitement d'un article Aldi : {e}")
                continue

        browser.close()

        if not results:
            return "", "", False

        bests = sorted(results[:5], key=lambda x: x["score"], reverse=True)
        bests_sorted_by_price = sorted(bests[:3], key=lambda x: x["price"])
        highest_price = bests_sorted_by_price[-1]["price"]
        lowest_price = bests_sorted_by_price[0]["price"]
        
        return highest_price, lowest_price, True


# Test de la fonction
if __name__ == "__main__":
    item = {"name": "Coca", "brand": "", "quantity": "1L"}
    best = get_price_aldi("", item)
    print(best)