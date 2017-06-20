import discord
from discord.ext import commands

bot = commands.Bot(command_prefix=['!'], description='Hello.')

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

token = os.environ.get('TOKEN', default=None)
bot.run(token)
