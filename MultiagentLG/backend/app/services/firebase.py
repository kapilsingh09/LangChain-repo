"""
firebase.py — Firebase Admin SDK Initialization.

HOW IT WORKS:
  Firebase Admin SDK lets our backend:
    1. Verify Firebase ID tokens sent by the frontend
    2. Read/write to Firestore (our database)

IMPORTANT — NO HARDCODED SECRETS:
  We read the Firebase credentials from environment variables.
  This means you can safely deploy to Cloud Run without
  ever putting secrets in your code or Git repository.

CREDENTIAL VARIABLES REQUIRED IN .env:
  FIREBASE_PROJECT_ID     → Your Firebase project ID
  FIREBASE_CLIENT_EMAIL   → The service account email
  FIREBASE_PRIVATE_KEY    → The private key (long string starting with -----BEGIN...)

HOW TO GET THESE:
  1. Go to Firebase Console → Project Settings → Service Accounts
  2. Click "Generate new private key"  → downloads a JSON file
  3. Copy the values from that JSON file into your .env
     (Do NOT commit that JSON file to Git!)

This module is imported once at startup (in main.py).
After that, firebase_admin.get_app() works everywhere.
"""

import os
import json

import firebase_admin
from firebase_admin import credentials

# Import our env vars from config
# (config.py validates they're present before the server starts)
from app.config import FIREBASE_PROJECT_ID, FIREBASE_CLIENT_EMAIL, FIREBASE_PRIVATE_KEY


def initialize_firebase() -> None:
    """
    Initialize Firebase Admin SDK using environment variables.

    This function is safe to call multiple times — if Firebase is
    already initialized, it skips re-initialization (no crash).

    Call this once at server startup from main.py.
    """

    # Avoid re-initializing if already done (happens on hot-reload in dev)
    if firebase_admin._apps:
        return

    # ── Build the credential dict from environment variables ──────────────────
    # Firebase expects a specific JSON structure for service accounts.
    # We reconstruct it from individual env vars instead of using a file.
    #
    # WHY?  Storing the full JSON file on Cloud Run would require either:
    #   a) Committing it to Git (NEVER do this — it's a secret)
    #   b) Mounting a secret file (complex setup)
    #   c) Using individual env vars (simplest, Cloud Run friendly)  ← we use this

    # The private key comes from .env with literal \n characters.
    # We replace them with real newlines so the key is valid.
    private_key = FIREBASE_PRIVATE_KEY.replace("\\n", "\n")

    service_account_info = {
        "type": "service_account",
        "project_id": FIREBASE_PROJECT_ID,
        "private_key_id": "key-from-env",   # Not needed for verification, just a label
        "private_key": private_key,
        "client_email": FIREBASE_CLIENT_EMAIL,
        "client_id": "",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": (
            f"https://www.googleapis.com/robot/v1/metadata/x509/"
            f"{FIREBASE_CLIENT_EMAIL.replace('@', '%40')}"
        ),
    }

    # Create the credentials object from our dict
    cred = credentials.Certificate(service_account_info)

    # Initialize the app — this only needs to happen once per server process
    firebase_admin.initialize_app(cred)

    print(f"✅ Firebase Admin SDK initialized for project: {FIREBASE_PROJECT_ID}")
