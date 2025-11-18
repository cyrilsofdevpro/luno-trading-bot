"""
Minimal Luno API client with safe dry-run mode.
This uses HTTP Basic Auth with (api_key, api_secret).
See README for usage and safety notes.
"""

import logging
import requests
import time
import socket

LOGGER = logging.getLogger(__name__)

# DNS override for environments where system DNS fails (e.g., broken gateway DNS)
# Maps api.luno.com to its known Cloudflare IP
_DNS_OVERRIDE = {
    'api.luno.com': ('104.18.34.135', 443),
    'api.luno.com:443': ('104.18.34.135', 443),
}

_original_getaddrinfo = socket.getaddrinfo

def _patched_getaddrinfo(host, port, *args, **kwargs):
    """Wrap socket.getaddrinfo to inject known IPs for api.luno.com when system DNS fails."""
    if host in _DNS_OVERRIDE:
        ip, p = _DNS_OVERRIDE[host]
        # Return a valid socket tuple: (family, type, proto, canonname, sockaddr)
        return [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, '', (ip, port))]
    return _original_getaddrinfo(host, port, *args, **kwargs)

# Monkey-patch socket.getaddrinfo to use our override
socket.getaddrinfo = _patched_getaddrinfo

BASE_URL = "https://api.luno.com/api/1"


class LunoClient:
    def __init__(self, api_key: str, api_secret: str, dry_run: bool = True):
        """Create a client.

        Args:
            api_key: Luno API key id
            api_secret: Luno API secret
            dry_run: if True, actions that affect account (placing/cancelling orders) won't be executed
        """
        self.auth = (api_key, api_secret)
        self.dry_run = bool(dry_run)

    def get_ticker(self, pair: str = "XBTUSD") -> dict:
        """Get ticker for a trading pair. Returns parsed JSON."""
        url = f"{BASE_URL}/ticker"
        resp = requests.get(url, params={"pair": pair})
        resp.raise_for_status()
        return resp.json()

    def get_order(self, order_id: str) -> dict:
        """Get information about an order. Best-effort depending on your account permissions.

        Returns parsed JSON or raises on HTTP error.
        """
        url = f"{BASE_URL}/getorder"
        resp = requests.get(url, auth=self.auth, params={"order_id": order_id})
        resp.raise_for_status()
        return resp.json()

    def get_balances(self) -> dict:
        """Return account balances (requires auth)."""
        url = f"{BASE_URL}/balances"
        resp = requests.get(url, auth=self.auth)
        resp.raise_for_status()
        return resp.json()

    def place_order(self, pair: str, side: str, volume: float, price: float, order_type: str = "limit") -> dict:
        """Place an order (limit by default). Side = 'buy' or 'sell'.

        Note: This method respects `dry_run` and will return a simulated response when dry.
        Luno API /postorder endpoint expects:
          - pair: currency pair (string)
          - type: 'BID' (buy) or 'ASK' (sell) — uppercase, required
          - volume: order amount (string)
          - price: limit price (integer or string representing integer)
          - order_type: 'limit' or 'market' (string)
        """
        side = side.lower()
        if side not in ("buy", "sell"):
            raise ValueError("side must be 'buy' or 'sell'")

        # Luno /postorder API expects 'type' parameter with 'BID' (buy) or 'ASK' (sell)
        luno_type = "BID" if side == "buy" else "ASK"
        
        # Price must be sent as integer (no decimals)
        price_int = int(float(price))
        
        # Canonical payload per Luno API spec
        payload = {
            "pair": pair,
            "type": luno_type,
            "volume": str(volume),
            "price": str(price_int),
            "order_type": order_type,
        }

        if self.dry_run:
            LOGGER.info("DRY_RUN enabled: not placing order: %s", payload)
            # Simulate an order id for dry run so caller can test order management
            return {"status": "dry_run", "payload": payload, "order_id": f"dry-{int(time.time())}"}

        url = f"{BASE_URL}/postorder"
        
        try:
            resp = requests.post(url, auth=self.auth, data=payload, timeout=15)
        except Exception as e:
            LOGGER.exception('Network error posting order, payload=%s', payload)
            raise RuntimeError(f"Network error placing order: {e}") from e

        body = None
        try:
            body = resp.text
        except Exception:
            body = '<unreadable response body>'

        if resp.ok:
            try:
                return resp.json()
            except Exception:
                # If JSON parsing fails but status is OK, return text
                return {'status': 'ok', 'raw': body}

        # Not OK: parse the error and provide user-friendly message
        error_data = resp.json() if resp.text else {}
        error_msg = error_data.get('error', resp.text)
        
        # Map Luno error messages to user-friendly messages
        error_map = {
            'Account has insufficient funds': 'Insufficient balance to place this order',
            'insufficient funds': 'Insufficient balance to place this order',
            'InsufficientFunds': 'Insufficient balance to place this order',
            'Volume is below the minimum': 'Order volume is below the minimum allowed',
            'Price is below the minimum': 'Order price is below the minimum allowed',
            'Price is above the maximum': 'Order price is above the maximum allowed',
        }
        
        # Check if error message matches any known Luno error
        user_friendly_msg = None
        for luno_err, friendly_msg in error_map.items():
            if luno_err.lower() in str(error_msg).lower():
                user_friendly_msg = friendly_msg
                break
        
        # Use friendly message if found, otherwise use raw Luno message
        final_error = user_friendly_msg or error_msg
        
        LOGGER.error('Postorder failed status=%s error=%s payload=%s', resp.status_code, error_msg, payload)
        raise RuntimeError(final_error)

    def cancel_order(self, order_id: str) -> dict:
        """Attempt to cancel an order. Luno API variants differ; this is a best-effort example.

        Note: respects dry_run.
        """
        if self.dry_run:
            LOGGER.info("DRY_RUN enabled: not cancelling order: %s", order_id)
            return {"status": "dry_run", "order_id": order_id}

        # Luno API cancel endpoints vary between account/order types. Here we attempt a generic cancel.
        # If your account/API version uses another endpoint, replace accordingly.
        url = f"{BASE_URL}/stoporder"
        resp = requests.post(url, auth=self.auth, data={"order_id": order_id})
        # If this endpoint is incorrect for your account, adjust to the correct cancel endpoint.
        resp.raise_for_status()
        return resp.json()
