# Utiliser une image Python officielle comme base
FROM python:3.11-slim

# Définir le répertoire de travail
WORKDIR /app

# Installer les dépendances système nécessaires pour Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers de requirements
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Installer les navigateurs Playwright
RUN playwright install --with-deps chromium

# Copier le code de l'application
COPY . .

# Exposer le port 8080
EXPOSE 8080

# Définir la commande par défaut
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]