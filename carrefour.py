from playwright.sync_api import sync_playwright
from urllib.parse import quote_plus
import time
from regex.utils import fuzzy_score


def get_price(store: str, item: dict):
    if store.lower() != "carrefour":
        raise NotImplementedError("Seul Carrefour est supporté actuellement.")

    query = f"{item.get('name', '')} {item.get('brand', '')} {item.get('quantity', '')}".strip()
    url = f"https://www.carrefour.fr/s?q={quote_plus(query)}"
    print(f"🔎 Recherche : {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
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

        # Attendre les articles
        try:
            page.wait_for_selector("article.product-list-card-plp-grid-new", timeout=1000)
        except:
            print("⚠️ Aucun produit trouvé pour", query)
            return "", "", False

        articles = page.query_selector_all("article.product-list-card-plp-grid-new")
        results = []

        for a in articles[:5]:
            try:
                name = a.query_selector(".product-list-card-plp-grid-new__title").inner_text().strip()
                brand = a.query_selector(".product-list-card-plp-grid-new__brand").inner_text().strip() if a.query_selector(".product-list-card-plp-grid-new__brand") else ""
                price_int = a.query_selector(".product-price__content.c-text--size-m").inner_text().strip()
                price_dec = a.query_selector(".product-price__content.c-text--size-s").inner_text().replace(",", ".").strip()
                price = float(price_int + price_dec)
               

                full_text = f"{name} {brand}"
                score = fuzzy_score(query, full_text)

                results.append({
                    "name": name,
                    "brand": brand,
                    "price": price,
                    "score": score
                })
            except:
                continue

        browser.close()
        print(results)

        if not results:
            return "", "", False

        bests = sorted(results[:5], key=lambda x: x["score"], reverse=True)
        bests_sorted_by_price = sorted(bests[:3], key=lambda x: x["price"])
        highest_price = bests_sorted_by_price[0]["price"]
        lowest_price = bests_sorted_by_price[-1]["price"]
        print("💰 Prix le plus bas :", lowest_price, "€", "pour article", bests_sorted_by_price[-1]["name"])
        print("💰 Prix le plus élevé :", highest_price, "€", "pour article", bests_sorted_by_price[0]["name"])
        return highest_price, lowest_price, True


item = {"name": "Spaghetti", "brand": "Barilla", "quantity": "500g"}
best = get_price("carrefour", item)
print(best)
