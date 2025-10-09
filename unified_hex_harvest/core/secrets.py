"""
Secrets management for Hex integration.
"""

import os
from typing import Optional


class HexSecrets:
    """Handle secrets from Hex environment."""
    
    @staticmethod
    def get_harvest_credentials() -> str:
        """
        Get Harvest credentials from Hex secrets.
        
        Returns:
            Harvest credentials JSON string
        """
        # In Hex, this would be: HARVEST_CREDENTIALS
        return os.environ.get('HARVEST_CREDENTIALS', '')
    
    @staticmethod
    def get_artifactory_username() -> str:
        """Get Artifactory username from Hex secrets."""
        return os.environ.get('ARTIFACTORY_USERNAME', '')
    
    @staticmethod
    def get_artifactory_access_token() -> str:
        """Get Artifactory access token from Hex secrets."""
        return os.environ.get('ARTIFACTORY_ACCESS_TOKEN', '')
    
    @staticmethod
    def get_artifactory_url() -> str:
        """Get Artifactory URL from Hex secrets."""
        return os.environ.get('ARTIFACTORY_URL', '')
    
    @staticmethod
    def setup_credentials():
        """
        Setup credentials for BigQuery access.
        This should be called at the beginning of each Hex notebook.
        """
        harvest_credentials = HexSecrets.get_harvest_credentials()
        
        if not harvest_credentials:
            raise ValueError(
                "HARVEST_CREDENTIALS not found in Hex secrets. "
                "Please add it to your Hex project secrets."
            )
        
        # Write credentials to temporary file for BigQuery
        with open('credentials.json', 'w') as f:
            f.write(harvest_credentials)
        
        # Set environment variable for BigQuery
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = 'credentials.json'
        
        print("✅ Credentials setup complete")


class LocalSecrets:
    """Handle secrets for local development (when not in Hex)."""
    
    @classmethod
    def setup_credentials(cls):
        """Setup credentials for local development."""
        try:
            # Try to import from local_secrets_actual.py
            from local_secrets_actual import HARVEST_CREDENTIALS
        except ImportError:
            raise ValueError(
                "For local development, please:\n"
                "1. Copy local_secrets.py to local_secrets_actual.py\n"
                "2. Fill in your actual credentials in local_secrets_actual.py\n"
                "3. Make sure local_secrets_actual.py is in .gitignore"
            )
        
        if not HARVEST_CREDENTIALS:
            raise ValueError(
                "HARVEST_CREDENTIALS is empty in local_secrets_actual.py. "
                "Please add your actual credentials."
            )
        
        with open('credentials.json', 'w') as f:
            f.write(HARVEST_CREDENTIALS)
        
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = 'credentials.json'
        print("✅ Local credentials setup complete")


def setup_credentials(use_hex_secrets: bool = True):
    """
    Setup credentials based on environment.
    
    Args:
        use_hex_secrets: Whether to use Hex secrets (True) or local secrets (False)
    """
    if use_hex_secrets:
        HexSecrets.setup_credentials()
    else:
        LocalSecrets.setup_credentials()
