#!/usr/bin/env bash
# GCP プロジェクトの初期セットアップ (1回だけ実行)
# 前提: gcloud CLI インストール済み、gcloud auth login 済み、課金有効なプロジェクト作成済み
set -euo pipefail

PROJECT_ID="${1:?usage: setup_gcp.sh <PROJECT_ID> <GITHUB_REPO (owner/name)>}"
GITHUB_REPO="${2:?usage: setup_gcp.sh <PROJECT_ID> <GITHUB_REPO (owner/name)>}"
REGION="asia-northeast1"
BUCKET="${PROJECT_ID}-focus-guardian-assets"
SA_NAME="github-deployer"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
POOL="github-pool"
PROVIDER="github-provider"

gcloud config set project "$PROJECT_ID"

echo "== API 有効化 =="
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  firestore.googleapis.com \
  aiplatform.googleapis.com \
  texttospeech.googleapis.com \
  storage.googleapis.com \
  secretmanager.googleapis.com \
  iamcredentials.googleapis.com

echo "== Firestore (Native) 作成 =="
gcloud firestore databases create --location="$REGION" --type=firestore-native || true

echo "== アセットバケット作成 (公開読み取り) =="
gcloud storage buckets create "gs://${BUCKET}" --location="$REGION" || true
gcloud storage buckets add-iam-policy-binding "gs://${BUCKET}" \
  --member=allUsers --role=roles/storage.objectViewer

echo "== デプロイ用サービスアカウント =="
gcloud iam service-accounts create "$SA_NAME" --display-name="GitHub Actions deployer" || true
for role in roles/run.admin roles/cloudbuild.builds.editor roles/artifactregistry.admin \
    roles/storage.admin roles/iam.serviceAccountUser roles/secretmanager.admin \
    roles/serviceusage.serviceUsageConsumer; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SA_EMAIL}" --role="$role" --condition=None >/dev/null
done

echo "== Cloud Run 実行 SA への権限 (Firestore/Vertex/TTS/GCS/Secret) =="
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')
RUN_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
for role in roles/datastore.user roles/aiplatform.user roles/storage.objectAdmin \
    roles/secretmanager.secretAccessor; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${RUN_SA}" --role="$role" --condition=None >/dev/null
done

echo "== Workload Identity Federation =="
gcloud iam workload-identity-pools create "$POOL" --location=global \
  --display-name="GitHub Actions" || true
gcloud iam workload-identity-pools providers create-oidc "$PROVIDER" \
  --location=global --workload-identity-pool="$POOL" \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
  --attribute-condition="assertion.repository=='${GITHUB_REPO}'" || true
gcloud iam service-accounts add-iam-policy-binding "$SA_EMAIL" \
  --role=roles/iam.workloadIdentityUser \
  --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL}/attribute.repository/${GITHUB_REPO}"

echo "== Voice Monkey トークン用シークレット (空で作成、後で値を設定) =="
gcloud secrets create voicemonkey-token --replication-policy=automatic || true

cat <<EOF

============================================================
GitHub リポジトリ (${GITHUB_REPO}) の Settings > Secrets and variables > Actions に登録:

GCP_PROJECT_ID       = ${PROJECT_ID}
GCS_ASSETS_BUCKET    = ${BUCKET}
WIF_PROVIDER         = projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL}/providers/${PROVIDER}
WIF_SERVICE_ACCOUNT  = ${SA_EMAIL}
VOICEMONKEY_DEVICE   = (Voice Monkey の Speaker デバイス ID)

Voice Monkey トークンの値を設定 (取得後に実行):
  echo -n "<TOKEN>" | gcloud secrets versions add voicemonkey-token --data-file=-

BGM ファイルの配置 (assets/bgm/*.mp3 を用意してから):
  gcloud storage cp assets/bgm/focus.mp3 assets/bgm/nature.mp3 assets/bgm/uptempo.mp3 gs://${BUCKET}/bgm/
============================================================
EOF
