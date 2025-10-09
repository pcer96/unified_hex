"""
Local secrets configuration for development.

⚠️  IMPORTANT: This file contains sensitive information.
- Add this file to .gitignore to avoid committing secrets
- Only use this for local development
- In Hex, use the Hex secrets system instead
"""

# Copy this file to local_secrets_actual.py and fill in your real values
# Then import from local_secrets_actual.py instead

# Your actual Harvest credentials (JSON string)
HARVEST_CREDENTIALS = """
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "your-private-key-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\nYOUR_PRIVATE_KEY_HERE\n-----END PRIVATE KEY-----\n",
  "client_email": "your-service-account@your-project.iam.gserviceaccount.com",
  "client_id": "your-client-id",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com"
}
"""

# Your Artifactory credentials
ARTIFACTORY_USERNAME = "your-artifactory-username"
ARTIFACTORY_ACCESS_TOKEN = "your-artifactory-access-token"
ARTIFACTORY_URL = "your-artifactory-url.com"

# Instructions:
# 1. Copy this file to local_secrets_actual.py
# 2. Replace the placeholder values above with your actual credentials
# 3. Add local_secrets_actual.py to .gitignore
# 4. Import from local_secrets_actual.py in your local development scripts
