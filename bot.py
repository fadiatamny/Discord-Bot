import discord
from discord.ext import commands
import asyncio
import logging

from MusicCog import Music


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


tokenFile = input('Bot Token:')
token = open(tokenFile, "r").read() 

description = 'Tragicly organize Tragic'
prefix = '.'

bot = commands.Bot(command_prefix=prefix, description=description)

def setup(bot):
    bot.add_cog(Music(bot))

@bot.event
async def on_ready():
    print('Logged in as {0} {1}'.format(bot.user.id,bot.user.name))
    print('------')

bot.run(token)
