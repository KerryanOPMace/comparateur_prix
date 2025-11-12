"""
Script de diagnostic mémoire pour les scrapers
"""
import gc
import psutil
import os

def check_memory():
    """Affiche l'usage mémoire actuel"""
    process = psutil.Process()
    memory_info = process.memory_info()
    memory_mb = memory_info.rss / 1024 / 1024
    print(f"Mémoire utilisée: {memory_mb:.2f} MB")
    return memory_mb

def test_scraper_memory_leak():
    """Test de fuites mémoire des scrapers"""
    print("=== Test de fuites mémoire ===")
    
    # Import après pour isoler
    from stores.carrefour import get_price_carrefour
    from stores.aldi import get_price_aldi
    from stores.monoprix import get_price_monoprix
    
    initial_memory = check_memory()
    
    # Test items
    items = [
        {"name": "lait", "brand": "lactel", "quantity": "1L"},
        {"name": "pain", "brand": "", "quantity": "400g"},
        {"name": "eau", "brand": "evian", "quantity": "1L"},
    ]
    
    stores = ["carrefour", "aldi", "monoprix"]
    
    for store in stores:
        print(f"\n--- Test {store} ---")
        memory_before = check_memory()
        
        for item in items:
            try:
                if store == "carrefour":
                    get_price_carrefour("Marly le roi", item)
                elif store == "aldi":
                    get_price_aldi("Marly le roi", item)
                elif store == "monoprix":
                    get_price_monoprix("Marly le roi", item)
                    
                # Nettoyage forcé
                gc.collect()
                
            except Exception as e:
                print(f"Erreur {store}: {e}")
        
        memory_after = check_memory()
        leak = memory_after - memory_before
        print(f"Fuite mémoire {store}: +{leak:.2f} MB")
        
        if leak > 50:  # Plus de 50MB de fuite
            print(f"⚠️ FUITE IMPORTANTE détectée dans {store}")
    
    final_memory = check_memory()
    total_leak = final_memory - initial_memory
    print(f"\nFuite totale: +{total_leak:.2f} MB")
    
    if total_leak > 100:
        print("❌ PROBLÈME MAJEUR: Plus de 100MB de fuite!")
        print("Solutions:")
        print("1. Vérifiez les sessions HTTP non fermées")
        print("2. Nettoyez les caches navigateur")
        print("3. Libérez les variables lourdes")
    else:
        print("✅ Fuites acceptables")

if __name__ == "__main__":
    test_scraper_memory_leak()