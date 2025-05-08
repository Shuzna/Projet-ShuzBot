import discord
from discord.ext import commands
from discord import app_commands
import json
import re
import os
from transformers import pipeline
from detoxify import Detoxify

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='/', intents=intents)

memory_file = "memory.json"
if os.path.exists(memory_file):
    with open(memory_file, 'r') as f:
        user_memory = json.load(f)
else:
    user_memory = {}

chatbot = pipeline("text-generation", model="microsoft/DialoGPT-medium")
nsfw_classifier = pipeline("text-classification", model="eliasalbouzidi/distilbert-nsfw-text-classifier")
toxicity_classifier = Detoxify('original')

GUILD_ID = 1234567890  # Remplacez par l'ID de votre serveur

@bot.event
async def on_ready():
    print(f"Connecté en tant que {bot.user}")
    try:
        await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print("Commandes synchronisées.")
    except Exception as e:
        print(f"Erreur de synchronisation : {e}")

@bot.event
async def on_member_join(member):
    try:
        await member.send("Bienvenue sur le serveur ! 🎉 N'hésite pas à inviter tes amis !")
    except Exception as e:
        print(f"Erreur d'envoi de MP : {e}")

@bot.tree.command(name="kickinactif", description="Exclut les membres inactifs depuis 14 jours.")
@app_commands.guilds(discord.Object(id=GUILD_ID))
async def kickinactif(interaction: discord.Interaction):
    await interaction.response.defer()
    count = await interaction.guild.prune_members(days=14, compute_prune_count=True)
    await interaction.followup.send(f"{count} membres inactifs ont été expulsés.")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    content = message.content.lower()
    uid = str(message.author.id)

    nsfw_result = nsfw_classifier(content)[0]
    if nsfw_result['label'] == 'nsfw' and nsfw_result['score'] > 0.7:
        await message.delete()
        await message.author.send("Votre message a été supprimé pour contenu inapproprié.")
        return

    tox = toxicity_classifier.predict(content)
    if tox['toxicity'] > 0.8:
        await message.delete()
        await message.author.send("Votre message a été supprimé pour langage inapproprié.")
        return

    match = re.search(r"j'ai (\d+) ans", content)
    if match:
        age = match.group(1)
        if uid not in user_memory:
            user_memory[uid] = {}
        user_memory[uid]['age'] = age
        with open(memory_file, 'w') as f:
            json.dump(user_memory, f, indent=2)
        await message.channel.send(f"Âge enregistré : {age} ans.")
        if int(age) < 13:
            await message.guild.kick(message.author, reason="Âge inférieur à 13 ans.")
            return

    if bot.user in message.mentions:
        question = message.content.replace(f"<@!{bot.user.id}>", "").strip()
        context = f"L'utilisateur a {user_memory.get(uid, {}).get('age', 'un âge inconnu')} ans. "
        result = chatbot(context + question, max_length=100, num_return_sequences=1)
        await message.channel.send(result[0]['generated_text'])

    await bot.process_commands(message)

if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    bot.run(token)