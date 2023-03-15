# bot.py
import os
import discord

TOKEN = os.getenv('MTA4NTMzOTY5NTc0NTA3NzI1NQ.Gd8FGl.6fOV74Xhs2NxIfT7wnE-bT8TqElYF6HiFRThdI')

client = discord.Client()

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

client.run(TOKEN)