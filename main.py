#!/usr/bin/env python3
"""
Luno Trading Bot - Railway Deployment Entry Point
Runs the bot as a background process looping continuously.
Uses environment variables for API credentials.
"""

import os
import sys
import time
import logging
from dotenv import load_dotenv

# Load environment variables from .env file (for local testing)
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Import bot modules
try:
    from smart_strategy import SmartStrategy
    from luno_client import LunoClient
    from profit_tracker import ProfitTracker
    from notification_manager import NotificationManager
except ImportError as e:
    logger.error(f"Failed to import bot modules: {e}")
    sys.exit(1)


def load_credentials():
    """Load Luno API credentials from environment variables."""
    api_key = os.getenv('LUNO_API_KEY')
    api_secret = os.getenv('LUNO_API_SECRET')
    
    if not api_key or not api_secret:
        logger.error("Missing LUNO_API_KEY or LUNO_API_SECRET environment variables")
        return None, None
    
    return api_key, api_secret


def run_bot():
    """
    Main bot loop that runs continuously.
    Executes trading strategy every cycle and logs results.
    """
    # Load credentials
    api_key, api_secret = load_credentials()
    if not api_key or not api_secret:
        logger.error("Cannot start bot without API credentials")
        return False
    
    # Initialize bot components
    try:
        client = LunoClient(api_key, api_secret)
        strategy = SmartStrategy()
        tracker = ProfitTracker()
        notifier = NotificationManager()
        logger.info("✅ Bot components initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize bot components: {e}")
        return False
    
    # Main loop
    cycle = 0
    try:
        logger.info("🚀 Luno Trading Bot started - running continuously...")
        while True:
            cycle += 1
            try:
                logger.debug(f"Cycle {cycle}: Fetching market data...")
                
                # Get active coin from strategy
                active_coin = strategy.get_active_coin()
                logger.info(f"Active coin: {active_coin}")
                
                # Fetch ticker data
                ticker = client.get_ticker(active_coin)
                last_price = float(ticker.get('last', 0))
                bid = float(ticker.get('bid', 0))
                
                logger.info(f"Pair: {active_coin} | Price: {last_price:.2f} | Bid: {bid:.2f}")
                
                # Get account balances (LunoClient provides get_balances)
                balances = client.get_balances()
                logger.debug(f"Balances: {balances}")
                
                # Execute strategy logic (buy/sell signals)
                signal = strategy.evaluate_signal(active_coin)
                logger.info(f"Signal for {active_coin}: {signal}")
                
                # Log cycle completion
                logger.info(f"✓ Cycle {cycle} completed successfully")
                
            except Exception as e:
                logger.error(f"Error in trading cycle {cycle}: {e}", exc_info=True)
                # Continue loop even on error
            
            # Sleep before next cycle
            cycle_interval = int(os.getenv('BOT_CYCLE_INTERVAL', 60))
            logger.debug(f"Sleeping for {cycle_interval}s before next cycle...")
            time.sleep(cycle_interval)
    
    except KeyboardInterrupt:
        logger.info("⏹ Bot interrupted by user")
        return True
    except Exception as e:
        logger.error(f"Fatal error in bot loop: {e}", exc_info=True)
        return False


def main():
    """Entry point for the bot."""
    logger.info("=" * 60)
    logger.info("Luno Trading Bot - Railway Deployment")
    logger.info("=" * 60)
    
    # Display environment info
    env = os.getenv('ENVIRONMENT', 'production')
    dry_run = os.getenv('DRY_RUN', 'false').lower() == 'true'
    logger.info(f"Environment: {env}")
    logger.info(f"Dry Run Mode: {dry_run}")
    
    # Start bot
    success = run_bot()
    
    if success:
        logger.info("Bot exited cleanly")
        sys.exit(0)
    else:
        logger.error("Bot exited with errors")
        sys.exit(1)


if __name__ == '__main__':
    main()
