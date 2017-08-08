import discord, os, re
from discord.ext import commands
from lukas import Lukas
from lukas_quest import *

import utilities

bot = commands.Bot(command_prefix=['!', 'lukas '], description='I am here to serve. I will try to respond to messages that start with `!` or `lukas `.')

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    await bot.change_presence(game=discord.Game(name="FEHWiki"))

token = os.environ.get('PUB_TOKEN', default=None)
if token is None:
    token = open('./pub_token').read().replace('\n', '')

utilities.setup(bot)

bot.run(token)
