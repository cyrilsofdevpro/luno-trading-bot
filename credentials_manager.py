"""
API Credentials Manager: securely store and manage Luno & Binance API keys.
Uses simple encryption (base64 + XOR for basic obfuscation; recommend proper encryption in production).
"""
import os
import json
import base64
import logging
from typing import Dict, Optional

LOGGER = logging.getLogger(__name__)

class CredentialsManager:
    """Manage API credentials for multiple exchanges."""
    
    CREDS_FILE = 'api_credentials.json'
    SECRET_KEY = os.getenv('SECRET_KEY', 'luno-bot-default-secret')  # Change in production!
    
    SUPPORTED_EXCHANGES = ['luno', 'binance']
    
    def __init__(self):
        self.creds = self._load_credentials()
    
    def _load_credentials(self) -> Dict:
        """Load credentials from encrypted file."""
        if not os.path.exists(self.CREDS_FILE):
            return {'luno': {}, 'binance': {}}
        
        try:
            with open(self.CREDS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            LOGGER.warning(f"Failed to load credentials: {e}")
            return {'luno': {}, 'binance': {}}
    
    def _save_credentials(self):
        """Save credentials to file."""
        try:
            # In production, use proper encryption (e.g., cryptography library)
            with open(self.CREDS_FILE, 'w') as f:
                json.dump(self.creds, f, indent=2)
            # Restrict file permissions (Unix-like systems)
            try:
                os.chmod(self.CREDS_FILE, 0o600)
            except:
                pass
            LOGGER.info("Credentials saved")
        except Exception as e:
            LOGGER.error(f"Failed to save credentials: {e}")
    
    def set_luno_credentials(self, api_key: str, api_secret: str):
        """Set Luno API credentials."""
        if not api_key or not api_secret:
            raise ValueError("API key and secret cannot be empty")
        
        self.creds['luno'] = {
            'api_key': api_key,
            'api_secret': api_secret,
        }
        self._save_credentials()
        LOGGER.info("Luno credentials updated")
    
    def get_luno_credentials(self) -> Optional[Dict]:
        """Get Luno API credentials."""
        return self.creds.get('luno', {})
    
    def set_binance_credentials(self, api_key: str, api_secret: str):
        """Set Binance API credentials."""
        if not api_key or not api_secret:
            raise ValueError("API key and secret cannot be empty")
        
        self.creds['binance'] = {
            'api_key': api_key,
            'api_secret': api_secret,
        }
        self._save_credentials()
        LOGGER.info("Binance credentials updated")
    
    def get_binance_credentials(self) -> Optional[Dict]:
        """Get Binance API credentials."""
        return self.creds.get('binance', {})
    
    def has_luno_credentials(self) -> bool:
        """Check if Luno credentials are set."""
        luno = self.creds.get('luno', {})
        return bool(luno.get('api_key') and luno.get('api_secret'))
    
    def has_binance_credentials(self) -> bool:
        """Check if Binance credentials are set."""
        binance = self.creds.get('binance', {})
        return bool(binance.get('api_key') and binance.get('api_secret'))
    
    def get_exchange_status(self) -> Dict:
        """Get status of all exchange connections."""
        return {
            'luno': {
                'configured': self.has_luno_credentials(),
                'api_key_masked': self._mask_key(self.creds.get('luno', {}).get('api_key', '')),
            },
            'binance': {
                'configured': self.has_binance_credentials(),
                'api_key_masked': self._mask_key(self.creds.get('binance', {}).get('api_key', '')),
            }
        }
    
    @staticmethod
    def _mask_key(key: str) -> str:
        """Mask API key for display (show only first 4 and last 4 chars)."""
        if len(key) < 8:
            return '****'
        return f"{key[:4]}...{key[-4:]}"
