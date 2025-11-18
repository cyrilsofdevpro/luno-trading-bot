"""
Alert & Notification System: send alerts via Email, WhatsApp, and Telegram.
"""
import os
import logging
from typing import List, Dict, Optional
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

LOGGER = logging.getLogger(__name__)

class NotificationManager:
    """Manage alerts and notifications across multiple channels."""
    
    def __init__(self):
        """Initialize notification manager with channel configs."""
        self.email_config = self._load_email_config()
        self.telegram_config = self._load_telegram_config()
        self.whatsapp_config = self._load_whatsapp_config()
        self.enabled_channels = []
        self._detect_enabled_channels()
    
    def _load_email_config(self) -> Dict:
        """Load email configuration from environment."""
        return {
            'enabled': bool(os.getenv('SMTP_SERVER')),
            'server': os.getenv('SMTP_SERVER', ''),
            'port': int(os.getenv('SMTP_PORT', 587)),
            'sender': os.getenv('SMTP_SENDER', ''),
            'password': os.getenv('SMTP_PASSWORD', ''),
            'recipients': os.getenv('EMAIL_RECIPIENTS', '').split(',') if os.getenv('EMAIL_RECIPIENTS') else [],
        }
    
    def _load_telegram_config(self) -> Dict:
        """Load Telegram configuration from environment."""
        return {
            'enabled': bool(os.getenv('TELEGRAM_BOT_TOKEN')),
            'bot_token': os.getenv('TELEGRAM_BOT_TOKEN', ''),
            'chat_ids': os.getenv('TELEGRAM_CHAT_IDS', '').split(',') if os.getenv('TELEGRAM_CHAT_IDS') else [],
        }
    
    def _load_whatsapp_config(self) -> Dict:
        """Load WhatsApp configuration from environment (Twilio)."""
        return {
            'enabled': bool(os.getenv('TWILIO_ACCOUNT_SID')),
            'account_sid': os.getenv('TWILIO_ACCOUNT_SID', ''),
            'auth_token': os.getenv('TWILIO_AUTH_TOKEN', ''),
            'from_number': os.getenv('TWILIO_WHATSAPP_FROM', ''),
            'to_numbers': os.getenv('WHATSAPP_RECIPIENTS', '').split(',') if os.getenv('WHATSAPP_RECIPIENTS') else [],
        }
    
    def _detect_enabled_channels(self):
        """Detect which notification channels are enabled."""
        if self.email_config['enabled']:
            self.enabled_channels.append('email')
        if self.telegram_config['enabled']:
            self.enabled_channels.append('telegram')
        if self.whatsapp_config['enabled']:
            self.enabled_channels.append('whatsapp')
    
    def send_trade_alert(self, action: str, pair: str, price: float, volume: float, order_id: str = None):
        """Send alert when a trade is executed."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        subject = f"🤖 Trade Alert: {action.upper()} {pair}"
        message = f"""
Trade Executed at {timestamp}

Pair: {pair}
Action: {action.upper()}
Price: ₦{price:.2f}
Volume: {volume:.8f}
Order ID: {order_id or 'N/A'}

Bot continues monitoring...
        """
        
        self._send_notifications(subject, message, alert_type='trade')
    
    def send_price_drop_alert(self, pair: str, price_drop_pct: float, current_price: float):
        """Send alert when price drops significantly."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        subject = f"📉 Price Drop Alert: {pair}"
        message = f"""
Significant Price Drop at {timestamp}

Pair: {pair}
Price Drop: {price_drop_pct:.2f}%
Current Price: ₦{current_price:.2f}

Consider buying on this dip!
        """
        
        self._send_notifications(subject, message, alert_type='price_drop')
    
    def send_daily_summary(self, stats: Dict):
        """Send daily trading summary."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        subject = f"📊 Daily Trading Summary - {timestamp.split()[0]}"
        
        pnl = stats.get('pnl_ngn', 0)
        pnl_pct = stats.get('pnl_pct', 0)
        pnl_emoji = "📈" if pnl > 0 else "📉" if pnl < 0 else "➡️"
        
        message = f"""
Daily Trading Summary

Date: {timestamp.split()[0]}
Total P/L: {pnl_emoji} ₦{pnl:.2f} ({pnl_pct:.2f}%)
Total Trades: {stats.get('total_trades', 0)}
Active Pairs: {stats.get('unique_pairs', 0)}
Reinvested: ₦{stats.get('total_reinvested', 0):.2f}
Savings: ₦{stats.get('total_savings', 0):.2f}

Keep trading smart!
        """
        
        self._send_notifications(subject, message, alert_type='summary')
    
    def _send_notifications(self, subject: str, message: str, alert_type: str = 'general'):
        """Send notification through all enabled channels."""
        for channel in self.enabled_channels:
            try:
                if channel == 'email':
                    self._send_email(subject, message)
                elif channel == 'telegram':
                    self._send_telegram(subject, message)
                elif channel == 'whatsapp':
                    self._send_whatsapp(subject, message)
            except Exception as e:
                LOGGER.error(f"Failed to send {channel} notification: {e}")
    
    def _send_email(self, subject: str, message: str):
        """Send email notification."""
        if not self.email_config['enabled']:
            return
        
        try:
            server = smtplib.SMTP(self.email_config['server'], self.email_config['port'])
            server.starttls()
            server.login(self.email_config['sender'], self.email_config['password'])
            
            for recipient in self.email_config['recipients']:
                msg = MIMEMultipart()
                msg['From'] = self.email_config['sender']
                msg['To'] = recipient.strip()
                msg['Subject'] = subject
                msg.attach(MIMEText(message, 'plain'))
                
                server.send_message(msg)
            
            server.quit()
            LOGGER.info(f"Email sent: {subject}")
        except Exception as e:
            LOGGER.error(f"Email sending failed: {e}")
    
    def _send_telegram(self, subject: str, message: str):
        """Send Telegram notification."""
        if not self.telegram_config['enabled']:
            return
        
        try:
            import requests
            bot_token = self.telegram_config['bot_token']
            chat_ids = self.telegram_config['chat_ids']
            
            full_message = f"*{subject}*\n\n{message}"
            
            for chat_id in chat_ids:
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                data = {
                    'chat_id': chat_id.strip(),
                    'text': full_message,
                    'parse_mode': 'Markdown',
                }
                requests.post(url, json=data, timeout=10)
            
            LOGGER.info(f"Telegram message sent: {subject}")
        except Exception as e:
            LOGGER.error(f"Telegram sending failed: {e}")
    
    def _send_whatsapp(self, subject: str, message: str):
        """Send WhatsApp notification via Twilio."""
        if not self.whatsapp_config['enabled']:
            return
        
        try:
            from twilio.rest import Client
            
            account_sid = self.whatsapp_config['account_sid']
            auth_token = self.whatsapp_config['auth_token']
            from_number = self.whatsapp_config['from_number']
            to_numbers = self.whatsapp_config['to_numbers']
            
            client = Client(account_sid, auth_token)
            
            full_message = f"{subject}\n\n{message}"
            
            for to_number in to_numbers:
                message_obj = client.messages.create(
                    from_=from_number,
                    body=full_message,
                    to=to_number.strip(),
                )
            
            LOGGER.info(f"WhatsApp message sent: {subject}")
        except Exception as e:
            LOGGER.error(f"WhatsApp sending failed: {e}")
    
    def get_enabled_channels(self) -> List[str]:
        """Get list of enabled notification channels."""
        return self.enabled_channels
    
    def get_channels_status(self) -> Dict:
        """Get status of all notification channels."""
        return {
            'email': {
                'enabled': self.email_config['enabled'],
                'recipients': len(self.email_config['recipients']),
            },
            'telegram': {
                'enabled': self.telegram_config['enabled'],
                'chat_ids': len(self.telegram_config['chat_ids']),
            },
            'whatsapp': {
                'enabled': self.whatsapp_config['enabled'],
                'recipients': len(self.whatsapp_config['to_numbers']),
            },
        }
