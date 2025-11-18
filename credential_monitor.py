"""
Credential Monitor: Detects changes to .env file and reloads credentials.
Allows bot to use new API keys without restart.
"""

import os
import time
from datetime import datetime
from dotenv import load_dotenv
import hashlib
import logging

LOGGER = logging.getLogger(__name__)

class CredentialMonitor:
    """Monitor .env file for changes and reload credentials."""
    
    def __init__(self, env_file=".env", check_interval=10):
        """
        Initialize credential monitor.
        
        Args:
            env_file: Path to .env file
            check_interval: Seconds between checks (default 10)
        """
        self.env_file = env_file
        self.check_interval = check_interval
        self.last_hash = None
        self.last_check = 0
        self.current_credentials = {}
        self._initial_load()
    
    def _initial_load(self):
        """Load credentials on startup."""
        if os.path.exists(self.env_file):
            load_dotenv(self.env_file)
            self.current_credentials = self._read_credentials()
            self.last_hash = self._get_file_hash()
            LOGGER.info(f"✅ Initial credentials loaded from {self.env_file}")
        else:
            LOGGER.warning(f"⚠️ {self.env_file} not found, using environment variables")
            self.current_credentials = self._read_credentials()
    
    def _get_file_hash(self):
        """Get SHA256 hash of .env file to detect changes."""
        if not os.path.exists(self.env_file):
            return None
        
        try:
            with open(self.env_file, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception as e:
            LOGGER.error(f"Error hashing {self.env_file}: {e}")
            return None
    
    def _read_credentials(self):
        """Read Luno credentials from environment."""
        return {
            'api_key': os.getenv('LUNO_API_KEY', ''),
            'api_secret': os.getenv('LUNO_API_SECRET', ''),
            'pair': os.getenv('PAIR', 'XBTNGN'),
            'dry_run': os.getenv('DRY_RUN', 'false').lower() in ('1', 'true', 'yes'),
        }
    
    def check_for_updates(self):
        """
        Check if credentials have changed.
        Returns True if credentials were updated, False otherwise.
        """
        now = time.time()
        
        # Only check after interval has passed
        if now - self.last_check < self.check_interval:
            return False
        
        self.last_check = now
        
        # Get current hash
        current_hash = self._get_file_hash()
        
        if current_hash is None:
            return False
        
        # Check if hash changed
        if current_hash != self.last_hash:
            LOGGER.info("🔄 Change detected in .env file, reloading credentials...")
            
            # Reload .env file
            load_dotenv(self.env_file, override=True)
            
            # Read new credentials
            new_credentials = self._read_credentials()
            
            # Check what changed
            changes = {}
            for key in new_credentials:
                if new_credentials[key] != self.current_credentials.get(key):
                    old_val = self.current_credentials.get(key)
                    new_val = new_credentials[key]
                    
                    # Mask sensitive data in logs
                    if key in ('api_key', 'api_secret'):
                        old_val = self._mask_secret(old_val)
                        new_val = self._mask_secret(new_val)
                    
                    changes[key] = {'old': old_val, 'new': new_val}
            
            if changes:
                LOGGER.info("📝 Credentials updated:")
                for key, change in changes.items():
                    LOGGER.info(f"  • {key}: {change['old']} → {change['new']}")
            
            # Update current credentials
            self.current_credentials = new_credentials
            self.last_hash = current_hash
            
            return True
        
        return False
    
    def get_credentials(self):
        """Get current credentials (checks for updates first)."""
        self.check_for_updates()
        return self.current_credentials.copy()
    
    def _mask_secret(self, secret):
        """Mask API secret for display (show first 4 and last 4 chars)."""
        if not secret:
            return "not set"
        if len(secret) <= 8:
            return "****"
        return f"{secret[:4]}****{secret[-4:]}"
    
    def get_api_key(self):
        """Get current API key (checks for updates)."""
        self.check_for_updates()
        return self.current_credentials['api_key']
    
    def get_api_secret(self):
        """Get current API secret (checks for updates)."""
        self.check_for_updates()
        return self.current_credentials['api_secret']
    
    def get_pair(self):
        """Get current trading pair (checks for updates)."""
        self.check_for_updates()
        return self.current_credentials['pair']
    
    def get_dry_run(self):
        """Get dry run mode (checks for updates)."""
        self.check_for_updates()
        return self.current_credentials['dry_run']
    
    def credentials_valid(self):
        """Check if API credentials are set."""
        creds = self.get_credentials()
        return bool(creds['api_key'] and creds['api_secret'])
    
    def log_status(self):
        """Log current credential status."""
        creds = self.get_credentials()
        
        if not creds['api_key']:
            LOGGER.warning("❌ API Key not set in .env")
            return False
        
        if not creds['api_secret']:
            LOGGER.warning("❌ API Secret not set in .env")
            return False
        
        LOGGER.info(f"✅ Credentials loaded:")
        LOGGER.info(f"  API Key: {self._mask_secret(creds['api_key'])}")
        LOGGER.info(f"  Pair: {creds['pair']}")
        LOGGER.info(f"  Mode: {'DRY RUN' if creds['dry_run'] else 'LIVE TRADING'}")
        
        return True


# Global monitor instance
_monitor = None

def initialize_monitor(env_file=".env", check_interval=10):
    """Initialize the global credential monitor."""
    global _monitor
    _monitor = CredentialMonitor(env_file, check_interval)
    return _monitor

def get_monitor():
    """Get the global credential monitor (initialize if needed)."""
    global _monitor
    if _monitor is None:
        _monitor = CredentialMonitor()
    return _monitor

def get_current_credentials():
    """Get current credentials (auto-checks for updates)."""
    return get_monitor().get_credentials()

def has_valid_credentials():
    """Check if valid credentials are configured."""
    return get_monitor().credentials_valid()
