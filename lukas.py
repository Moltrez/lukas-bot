import discord, os, random, re
from PIL import Image
from discord.ext import commands
from image_process import resize_and_crop

bot = commands.Bot(command_prefix=['!', 'lukas '], description='I am here to serve. I will try to respond to messages that start with `!` or `lukas `.')

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    await bot.change_presence(game=discord.Game(name="Fire Emblem Echoes: Shadows of Valentia"))

@bot.command()
async def hi():
    """Allow me to tell you a bit about myself."""
    quotes = ["I like to lose myself in the books when I can. It should be no surprise. Even I like a good escape.",
              "Some may find this surprising, but I am a fan of sweets. When I have a sweet cookie or a spoonful of honey, it's like all my fatigue is blown away!",
              "I am of a noble family... at least in the world where I am from. Our home is near the border, so I joined the Deliverance when crisis erupted in our lands."]
    await bot.say(random.choice(quotes))

background_path = './selfie/backgrounds/'

@bot.command()
async def selfie(*args):
    """Please type `!help selfie` for more information.
    I have travelled to many places and have many photos to share with you. Ask me for a random one or specify a location I've been to.
    Usage: selfie (\"location\")"""
    selfie_path = './selfie/made/'

    requested = args
    background_files = []
    if (len(requested) == 0):
        background_files = [random.choice(os.listdir(background_path))]
    else:
        for request in requested:
            file_extension_or_not_pattern = re.compile('(\.[a-z]+)?$', re.I | re.M)
            found = False
            for extension in ['.png', '.jpg']:
                request_file = file_extension_or_not_pattern.sub(extension, request)
                if os.path.exists(background_path + request_file):
                    background_files.append(request_file)
                    found = True
            if not found:
                await bot.say('I have not been to ' + request + '.')
                await bot.say('If the location is multiple words, try grouping it within quotes, such as `"mountain trail"`.')
                await bot.say('Please keep in mind I am case-sensitive.')


    for background_file in background_files:
        await bot.say("Ah yes, here I am at the " + background_file[:-3])
        if not os.path.exists(selfie_path + background_file):
            background = resize_and_crop(background_path + background_file, (500, 500))
            foreground = Image.open('./selfie/lukas.png')
            background.paste(foreground, (0,0), foreground)
            background.save(selfie_path + background_file, "PNG")
        await bot.upload(selfie_path + background_file)

@bot.command()
async def where():
    """I will tell you where I have been."""
    file_extension_pattern = re.compile('\.[a-z]+$', re.I | re.M)
    locations = file_extension_pattern.sub('', "\n".join(map(str, os.listdir(background_path))))
    await bot.say("I have taken selfies at these locations:\n" + "```" + locations + "```")

@bot.event
async def on_message(message):
    # we do not want the bot to reply to itself
    if message.author == bot.user:
        return
    luke_pattern = re.compile('.*gotta.*love.*luke', re.I)
    if luke_pattern.match(message.content):
        await bot.send_message(message.channel, '<:upsetlukas:326630615065559041>')
    lukas_pattern = re.compile('.*love.*lukas', re.I)
    if lukas_pattern.match(message.content):
        await bot.send_message(message.channel, '<:lukas:316202740495679488>')
    await bot.process_commands(message)

token = os.environ.get('TOKEN', default=None)
if token is None:
    token = open('./token').read().replace('\n','')
bot.run(token)
