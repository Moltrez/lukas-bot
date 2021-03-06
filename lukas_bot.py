import discord, os, re, random
from discord.ext import commands

import utilities, fehwiki_parse
from feh_cache import cache_log

import dl

bot = commands.Bot(command_prefix=['?', '? ', 'lukas ', 'Lukas ', 'lukas, ', 'Lukas, ', 'f?'], description='I am here to serve. I will try to respond to messages that start with `?` or `lukas `.')

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    if bot.user.name != 'Not Lukas':
        try:
            with open('./avatar.png', 'rb') as avatar:
                await bot.user.edit(username='Not Lukas', avatar=avatar.read())
        except Exception as ex:
            print(ex)
            await bot.user.edit(username='Not Lukas')
    await bot.change_presence(activity=discord.Game(name="FEHWiki"))

luke_pattern = re.compile('.*gotta.*love.*luke', re.I)
lukas_pattern = re.compile('.*love.*lukas', re.I)
python_pattern = re.compile('.*love.*python', re.I)
forsyth_pattern = re.compile('.*love.*forsyth($|[^e])', re.I)

@bot.event
async def on_message(message):
    # we do not want the bot to reply to itself
    log_message = ''
    while cache_log:
        next_message = cache_log.pop()
        if (len(log_message) + len(next_message) + 1 >= 2000) or len(cache_log) == 0:
            for ch in bot.private_channels:
                if ch.recipients[0].name == 'SUP' and str(ch.recipients[0].discriminator) == '0169':
                    await message.ch.send(log_message + ('' if len(cache_log) else next_message))
            log_message = ''
        log_message += next_message + '\n'
    if message.author == bot.user:
        return
    if str(message.author) == 'SUP#0169' and message.content == '?cache':
        await message.author.send(file=discord.File('./data_cache.json'))
        return
    if luke_pattern.match(message.content):
        await message.channel.send(file=discord.File('./emotions/upset.png', 'upset.png'))
    if lukas_pattern.match(message.content):
        await message.channel.send(file=discord.File('./emotions/happy.png', 'happy.png'))
        await message.channel.send(
                               random.choice(
                                   ['Thank you! I quite enjoy your company as well.',
                                    'That just made my day. I hope yours goes well too.',
                                    'It\'s very nice to be appreciated. Let\'s do our best!']))
    if python_pattern.match(message.content):
        await message.channel.send(file=discord.File('./emotions/happy.png', 'happy.png'))
        await message.channel.send("I am also quite pleased at the good work he did in my absence.")
    if forsyth_pattern.match(message.content) and str(message.author) == 'codefreak8#5021':
        await message.channel.send(file=discord.File('./emotions/upset.png', 'upset.png'))
        await message.channel.send("Sure you do, Code.")
    if forsyth_pattern.match(message.content):
        await message.channel.send(file=discord.File('./emotions/happy.png', 'happy.png'))
        await message.channel.send("I am sure could spare some orbs for him, then.")
    await bot.process_commands(message)

token = os.environ.get('TOKEN', default=None)
if token is None:
    token = open('./token').read().replace('\n', '')

utilities.setup(bot)
dl.setup(bot)

bot.run(token)
