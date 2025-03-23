import os
import sys
import glob
import pytz
import asyncio
import logging
import importlib
from pathlib import Path
from pyrogram import idle
from aiohttp import web
from typing import Union, Optional, AsyncGenerator
from datetime import date, datetime

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logging.getLogger("aiohttp").setLevel(logging.ERROR)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("aiohttp.web").setLevel(logging.ERROR)

# Importing Required Modules
from info import *
from Script import script
from utils import temp, ping_server
from web.server.clients import initialize_clients

# Plugin Loading
ppath = "plugins/*.py"
files = glob.glob(ppath)

# Initialize Webavbot
Webavbot.start()
loop = asyncio.get_event_loop()

# Define a Simple Request Handler
async def handle(request):
    return web.Response(text="Hello, World!")

# Web Server Setup
async def web_server():
    app = web.Application()

    # Add Routes
    app.router.add_get("/", handle)  # Root URL
    app.router.add_get("/health", lambda request: web.Response(text="OK"))  # Health check

    # Add a catch-all handler for undefined routes
    async def catch_all(request):
        return web.Response(text="Not Found", status=404)

    app.router.add_route("*", "/{tail:.*}", catch_all)

    return app

# Main Bot Initialization
async def start():
    print('\n')
    print('Initializing Your Bot')
    bot_info = await Webavbot.get_me()
    await initialize_clients()

    # Load Plugins
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
            print("Imported => " + plugin_name)

    # Ping Server (if on Heroku)
    if ON_HEROKU:
        asyncio.create_task(ping_server())

    # Bot Information
    me = await Webavbot.get_me()
    temp.BOT = Webavbot
    temp.ME = me.id
    temp.U_NAME = me.username
    temp.B_NAME = me.first_name

    # Time and Date
    tz = pytz.timezone('Asia/Kolkata')
    today = date.today()
    now = datetime.now(tz)
    time = now.strftime("%H:%M:%S %p")

    # Send Restart Message
    await Webavbot.send_message(LOG_CHANNEL, text=script.RESTART_TXT.format(today, time))
    await Webavbot.send_message(ADMINS[0], text='<b>ʙᴏᴛ ʀᴇsᴛᴀʀᴛᴇᴅ !!</b>')

    # Start Web Server
    app = web.AppRunner(await web_server())
    await app.setup()
    bind_address = "0.0.0.0"
    await web.TCPSite(app, bind_address, PORT).start()

    # Keep the Bot Running
    await idle()

# Entry Point
if __name__ == '__main__':
    try:
        loop.run_until_complete(start())
    except KeyboardInterrupt:
        logging.info('----------------------- Service Stopped -----------------------')
