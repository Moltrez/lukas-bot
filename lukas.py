import discord
from discord.ext import commands

bot = commands.Bot(command_prefix=['!'], description='Hello.')

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

@bot.command
async def hi():
    await bot.say("I like to lose myself in the books here when I can. It should be no surprise. Even I like a good escape.")
    
#token = os.environ.get('TOKEN')
bot.run('MzI2NTgxNTcwNjkxMzk5Njgy.DCo9SQ.Ezm4TJi0wDIx1kNz7Pv91TT5bqU')
