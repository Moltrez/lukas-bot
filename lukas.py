import discord
from discord.ext import commands

bot = commands.Bot(command_prefix=['!'], description='Hello.')

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

bot.run('MzI2NTgxNTcwNjkxMzk5Njgy.DCo9SQ.Ezm4TJi0wDIx1kNz7Pv91TT5bqU')
