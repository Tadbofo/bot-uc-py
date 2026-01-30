import os
import json
import requests
import feedparser
import discord
from discord import Embed
from flask import Flask
from threading import Thread
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
RSS_URL = os.getenv("RSS_URL")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
ROLE_ID = 1465209219497328798

DATA_FILE = "lastNews.json"

app = Flask('')

@app.route('/')
def home():
    return "Bot UC activo"

def run_web():
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)

Thread(target=run_web).start()


intents = discord.Intents.default()
intents.message_content = True  

client = discord.Client(intents=intents)


def get_last_link():
    if not os.path.exists(DATA_FILE):
        return None
    with open(DATA_FILE, "r") as f:
        return json.load(f).get("lastLink")

def save_last_link(link):
    with open(DATA_FILE, "w") as f:
        json.dump({"lastLink": link}, f)


async def check_rss(first_run=False):
    print("Revisando RSS...")

    try:
        response = requests.get(RSS_URL, timeout=10)
        response.raise_for_status()
        content = response.text.encode('utf-8', errors='ignore')  
        feed = feedparser.parse(content)
    except Exception as e:
        print("Error al obtener el feed:", e)
        return

    if not feed.entries:
        print("RSS vacío o no compatible con feedparser.")
        if hasattr(feed, 'bozo_exception') and feed.bozo:
            print("Error en el feed:", feed.bozo_exception)
        return

    last_link = get_last_link()
    new_entries = []

  
    if first_run and last_link is None:
        print("Primera ejecución: guardando la última noticia sin enviar nada.")
        save_last_link(feed.entries[0].link)
        return

   
    for entry in feed.entries:
        if entry.link == last_link:
            break
        new_entries.append(entry)

    if not new_entries:
        print("No hay noticias nuevas")
        return


    channel = await client.fetch_channel(CHANNEL_ID)
    for entry in reversed(new_entries):
        print("Preparando noticia:", entry.title, entry.link)

        embed = Embed(
            title=entry.title,
            url=entry.link,
            description=(entry.summary[:600] + "...") if hasattr(entry, "summary") else "",
            color=0x003DA5
        )
        embed.set_thumbnail(url="https://i.imgur.com/yQ5ANpU.jpg")
        await channel.send(content=f"<@&{ROLE_ID}>", embed=embed)
        print("Noticia enviada:", entry.title)


    save_last_link(feed.entries[0].link)


@client.event
async def on_ready():
    print(f"Bot conectado como {client.user}")

    scheduler = AsyncIOScheduler()
    scheduler.add_job(lambda: check_rss(), "interval", minutes=10)
    scheduler.start()


    await check_rss(first_run=True)


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.lower() == "!funcionando":
        await message.channel.send("Estoy funcionando ✅")


client.run(TOKEN)