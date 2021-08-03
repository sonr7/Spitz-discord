import discord
import asyncio
import os

token = os.environ.get('DISCORD_BOT_TOKEN')

client = discord.Client()

@client.event
async def on_ready():
    print('起動しました')

@client.event
async def on_message(message):
    if message.content.startswith('#spitz:'):
        kasi = message.content.replace('#spitz:', '')
        with open(kasi) as kasii:
            kasiyaru = kasii.read()
        embed = discord.Embed(title = kasi, description = kasiyaru)
        await message.channel.send(embed = embed)


client.run(token)
