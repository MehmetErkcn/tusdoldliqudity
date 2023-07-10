import logging
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext, JobQueue
from telegram.error import BadRequest, NetworkError
from telegram.ext import ChatMemberHandler
import locale

import asyncio

from telegram.ext import (
    Application,
    ContextTypes,
    CommandHandler,
)

# locale ayarları

locale.setlocale(locale.LC_ALL, 'C.UTF-8')

# Telegram bot token
TOKEN = ''
ids = -1001885723366
bal = 36271

# API endpoint
API = 'https://api.venus.io/api/vtoken'

log_file = 'tusdold.log'

# Enable logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)
handler = logging.FileHandler(log_file, encoding='utf-8')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
handler.setFormatter(formatter)
logging.getLogger('').addHandler(handler)


# check_liquidity görevini duraklatma/deaktive etme işlemi için bir bayrak
check_liquidity_paused = False


async def balance(update: Update, context: CallbackContext):
    # Kullanıcı ID'sini alın
    user_id = update.effective_user.id

    # API'ya istek gönderin
    response = requests.get(API)

    if response.status_code == 200:
        data = response.json()
        if 'data' in data and 'markets' in data['data']:
            tusd_data = next((market for market in data['data']['markets'] if market['symbol'] == 'vTUSDOLD'), None)
            if tusd_data:
                liquidity_str = tusd_data['liquidity']
                try:
                    liquidity = float(liquidity_str)
                    formatted_liquidity = locale.format_string('%.2f', liquidity, grouping=True)
                    message = f"$TUSDOLD Liquidity: <b>{formatted_liquidity}</b>"
                    chat_id = update.effective_chat.id
                    # print(chat_id)
                    await context.bot.send_message(chat_id=chat_id, text=message, parse_mode='HTML')
                    if liquidity > bal:
                        warning_message = "<b>Alert! \nLiquidity is above 36,271!</b>"
                        combined_message = f"{warning_message}\n\n{message}"
                        await context.bot.send_message(chat_id=chat_id, text=combined_message, parse_mode='HTML')
                except ValueError:
                    logger.error("Invalid liquidity value")
            else:
                logger.error("TUSD market data not found")
        else:
            logger.error("Error retrieving data from API")
    else:
        logger.error("Error connecting to API")





async def check_liq(context: CallbackContext):

    # API'ya istek gönderin
    response = requests.get(API)

    if response.status_code == 200:
        data = response.json()
        if 'data' in data and 'markets' in data['data']:
            tusd_data = next((market for market in data['data']['markets'] if market['symbol'] == 'vTUSDOLD'), None)
            if tusd_data:
                liquidity_str = tusd_data['liquidity']
                try:
                    liquidity = float(liquidity_str)
                    formatted_liquidity = locale.format_string('%.2f', liquidity, grouping=True)
                    message = f"$TUSDOLD Liquidity: <b>{formatted_liquidity}</b>"
                    chat_id = ids # Telegram grubunuzun ID'sini buraya ekleyin
                    # print(chat_id)
                    await context.bot.send_message(chat_id=chat_id, text=message, parse_mode='HTML')
                    if liquidity > bal:
                        warning_message = "<b>Alert! \nLiquidity is above 36,271!</b>"
                        combined_message = f"{warning_message}\n\n{message}"
                        await context.bot.send_message(chat_id=chat_id, text=combined_message, parse_mode='HTML')
                except ValueError:
                    logger.error("Invalid liquidity value")
            else:
                logger.error("TUSD market data not found")
        else:
            logger.error("Error retrieving data from API")
    else:
        logger.error("Error connecting to API")      
    
async def check_liquidity(context: CallbackContext):
    global check_liquidity_paused
    if not check_liquidity_paused:
        # API'ya istek gönderin
        response = requests.get(API)

        if response.status_code == 200:
            data = response.json()
            if 'data' in data and 'markets' in data['data']:
                tusd_data = next((market for market in data['data']['markets'] if market['symbol'] == 'vTUSDOLD'), None)


                if tusd_data:
                    liquidity_str = tusd_data['liquidity']
                    try:
                        liquidity = float(liquidity_str)
                        formatted_liquidity = locale.format_string('%.2f', liquidity, grouping=True)
                        message = f"<b>$TUSDOLD Liquidity: {formatted_liquidity}</b>"
                        if liquidity > bal:
                            warning_message = "<b>Alert! \nLiquidity is above 36,271!</b>"
                            chat_id = ids  # Telegram grubunuzun ID'sini buraya ekleyin
                            combined_message = f"{warning_message}\n\n{message}"
                            await context.bot.send_message(chat_id=chat_id, text=combined_message, parse_mode='HTML')
                            check_liquidity_paused = True
                    except ValueError:
                        logger.error("Invalid liquidity value")
                else:
                    logger.error("TUSD market data not found")
            else:
                logger.error("Error retrieving data from API")
        else:
            logger.error("Error connecting to API")



async def help_command(update: Update, context: CallbackContext):
    help_message = "This bot checks the liquidity every minute. If it is above 36,271, it sends an warning message to the group. Additionally, every 4 hours, it automatically sends the current liquidity to the group. \n\nIf you want to manually view the liquidity, you can use the /balance command."
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id=chat_id, text=help_message)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    logger.error("Exception while handling an update:", exc_info=context.error)
    logger.error("Network Error")







def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    bot = Application.builder().token(TOKEN).build()

    # on different commands - answer in Telegram
    bot.add_error_handler(error_handler)

    bot.add_handler(CommandHandler("balance", balance))
    bot.add_handler(CommandHandler("help", help_command))
    
    
    try:
        # Telegram bot update
        # Örneğin:
        job_queue = bot.job_queue
        job_queue.run_repeating(check_liq, interval=14400, first=0)
        
        job_queue.run_repeating(check_liquidity, interval=60, first=0)

        bot.run_polling(allowed_updates=Update.ALL_TYPES)
    except NetworkError as e:
        logger.info("NetworkError: {}".format(e))
        if "Flood control exceeded" in str(e):
            logger.info("Flood control exceeded")
            # Flood control hatası görmezden geliniyor
            pass
        else:
            # Diğer NetworkError hataları ele alınıyor
            # Hata mesajını yazdırabilir veya başka bir işlem yapabilirsiniz
            # print("NetworkError:", e)
            logger.info("NetworkError:", e)

    # bot.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
