import discord
from discord.ext import commands
import asyncio
import re
import random
import urllib
import urllib.request
import urllib.error
import os
import json

bot = commands.Bot(command_prefix=['!'], description='Hello.')

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    await bot.change_presence(game=discord.Game(name="Fire Emblem Echoes: Shadows of Valentia"))

token = os.environ.get('TOKEN', default=None)
bot.run(token)
