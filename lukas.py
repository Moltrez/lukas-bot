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
    quotes = ["I like to lose myself in the books here when I can. It should be no surprise. Even I like a good escape.", "I am of a noble family...at least in the world where I am from.Our home is near the border, so I joined the Deliverance when crisis erupted in our lands."]
    await bot.say(random.choice(quotes))
    
token = os.environ.get('TOKEN')
