import discord
from discord.ext import commands
import asyncio
from datetime import datetime, timedelta

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Liste d'insultes / NSFW fréquemment utilisées (à adapter si besoin)
MOTS_INTERDITS = [
    "nique", "fdp", "ta gueule", "enculé", "salope", "batard", "putain",
    "pute", "merde", "connard", "conne", "tg", "ntm", "zboob", "seins",
    "bite", "cul", "chatte", "porn", "pd", "pédé", "encule", "suce"
]

def contient_mot_interdit(message):
    contenu = message.content.lower()
    return any(mot in contenu for mot in MOTS_INTERDITS)

@bot.event
async def on_ready():
    print(f"{bot.user.name} est en ligne.")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if contient_mot_interdit(message):
        try:
            await message.delete()
            await message.author.send("🚫 Ton message a été supprimé car il enfreint les règles du serveur.")
        except:
            pass
        return

    await bot.process_commands(message)

# Commande pour kick les membres inactifs depuis 2 semaines
@bot.command()
@commands.has_permissions(administrator=True)
async def kickinactif(ctx):
    deux_semaines = datetime.utcnow() - timedelta(days=14)
    kicked = 0
    for member in ctx.guild.members:
        if member.bot:
            continue
        if member.status == discord.Status.offline:
            joined_at = member.joined_at or deux_semaines
            if joined_at < deux_semaines:
                try:
                    await member.kick(reason="Inactivité de plus de 2 semaines")
                    kicked += 1
                except:
                    pass
    await ctx.send(f"👢 {kicked} membres inactifs ont été expulsés.")

# Message privé à l’arrivée d’un nouveau membre
@bot.event
async def on_member_join(member):
    try:
        await member.send("👋 Bienvenue sur le serveur ! Invite tes potes pour qu'on s'amuse encore plus 🎉")
    except:
        pass

# Lance le bot
import os
TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
