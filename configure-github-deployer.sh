# Configuration du service account github-deployer pour Cloud Run
# À exécuter dans Google Cloud Shell ou votre terminal avec gcloud configuré

PROJECT_ID="shopsync-eb9c1"
SERVICE_ACCOUNT="github-deployer@shopsync-eb9c1.iam.gserviceaccount.com"

echo "Configuration des permissions pour $SERVICE_ACCOUNT"

# 1. Activer l'API Cloud Run (si pas déjà fait)
gcloud services enable run.googleapis.com --project=$PROJECT_ID

# 2. Donner le rôle Cloud Run Admin (peut créer/modifier/supprimer des services Cloud Run)
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/run.admin"

# 3. Donner le rôle Service Account User (obligatoire pour Cloud Run)
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/iam.serviceAccountUser"

# 4. Donner l'accès en lecture à Artifact Registry (déjà fait probablement)
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/artifactregistry.reader"

echo "Configuration terminée ! Votre service account github-deployer peut maintenant déployer sur Cloud Run."

# 5. Vérifier les rôles attribués
echo "Vérification des rôles attribués :"
gcloud projects get-iam-policy $PROJECT_ID \
    --flatten="bindings[].members" \
    --format="table(bindings.role)" \
    --filter="bindings.members:$SERVICE_ACCOUNT"