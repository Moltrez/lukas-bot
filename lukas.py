import discord, os, random
from PIL import Image
from discord.ext import commands

bot = commands.Bot(command_prefix=['!', 'lukas '], description='Hello.')

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    await bot.change_presence(game=discord.Game(name="Fire Emblem Echoes: Shadows of Valentia"))

@bot.command()
async def hi():
    quotes = ["I like to lose myself in the books when I can. It should be no surprise. Even I like a good escape.", "I am of a noble family... at least in the world where I am from. Our home is near the border, so I joined the Deliverance when crisis erupted in our lands."]
    await bot.say(random.choice(quotes))

@bot.command()
async def selfie():
    background_path = './selfie/backgrounds/'
    selfie_path = './selfie/made/'
    background_file = random.choice(os.listdir(background_path))
    await bot.say("Ah yes, here I am at the " + background_file[:-3])
    if not os.path.exists(selfie_path + background_file):
        background = Image.open(background_path + background_file)
        foreground = Image.open('./selfie/lukas.png')
        background.paste(foreground, (0,0), foreground)
        background.save(selfie_path + background_file, "PNG")
    await bot.upload(selfie_path + background_file)

token = os.environ.get('TOKEN', default=None)
if token is None:
    token = open('./token').read().replace('\n','')
bot.run(token)
