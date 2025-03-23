import os
import sys
import glob
import pytz
import asyncio
import logging
import importlib
from pathlib import Path
from pyrogram import idle, filters
from datetime import date, datetime
from aiohttp import web
from web import web_server
from web.server import Webavbot
from utils import temp, ping_server
from web.server.clients import initialize_clients
from info import *
from Script import script

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logging.getLogger("aiohttp").setLevel(logging.ERROR)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("aiohttp.web").setLevel(logging.ERROR)

# Plugin loading
ppath = "plugins/*.py"
files = glob.glob(ppath)

async def start():
    print('\n')
    print('Initializing Your Bot')

    # Start the Pyrogram client
    await Webavbot.start()  # Await the start method
    bot_info = await Webavbot.get_me()  # Verify bot is started
    logging.info(f"Bot started: {bot_info.username} (ID: {bot_info.id})")
    await initialize_clients()

    # Load plugins
    for name in files:
        with open(name) as a:
            patt = Path(a.name)
            plugin_name = patt.stem.replace(".py", "")
            plugins_dir = Path(f"plugins/{plugin_name}.py")
            import_path = "plugins.{}".format(plugin_name)
            spec = importlib.util.spec_from_file_location(import_path, plugins_dir)
            load = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(load)
            sys.modules["plugins." + plugin_name] = load
            logging.info(f"Imported => {plugin_name}")

    # Ping server if on Heroku
    if ON_HEROKU:
        asyncio.create_task(ping_server())

    # Set bot information
    me = await Webavbot.get_me()
    temp.BOT = Webavbot
    temp.ME = me.id
    temp.U_NAME = me.username
    temp.B_NAME = me.first_name

    # Send restart message
    tz = pytz.timezone('Asia/Kolkata')
    today = date.today()
    now = datetime.now(tz)
    time = now.strftime("%H:%M:%S %p")
    await Webavbot.send_message(LOG_CHANNEL, text=script.RESTART_TXT.format(today, time))
    await Webavbot.send_message(ADMINS[0], text='<b>ʙᴏᴛ ʀᴇsᴛᴀʀᴛᴇᴅ !!</b>')

    # Start aiohttp web server
    app = web.Application()
    app.add_routes([web.get("/", lambda request: web.Response(text="Bot is running!"))])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    # Keep the bot running
    await idle()

# Add a test command handler
@Webavbot.on_message(filters.command("start"))
async def start_command(client, message):
    logging.info(f"Received /start command from {message.from_user.id}")
    await message.reply("Bot is working!")

if __name__ == '__main__':
    try:
        asyncio.run(start())  # Use asyncio.run() instead of get_event_loop()
    except KeyboardInterrupt:
        logging.info('----------------------- Service Stopped -----------------------')
