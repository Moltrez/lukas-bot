import discord, os, re, random
from discord.ext import commands

import utilities, fehwiki_parse
from feh_cache import cache_log

bot = commands.Bot(command_prefix=['?', '? ', 'lukas ', 'Lukas ', 'lukas, ', 'Lukas, '], description='I am here to serve. I will try to respond to messages that start with `?` or `lukas `.')

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    await bot.change_presence(game=discord.Game(name="FEHWiki"))


@bot.event
async def on_message(message):
    # we do not want the bot to reply to itself
    log_message = ''
    while cache_log:
        next_message = cache_log.pop()
        if (len(log_message) + len(next_message) + 1 >= 2000) or len(cache_log) == 0:
            for ch in bot.private_channels:
                if ch.recipients[0].name == 'monkeybard' and str(ch.recipients[0].discriminator) == '3663':
                    await bot.send_message(ch, log_message + ('' if len(cache_log) else next_message))
            log_message = ''
        log_message += next_message + '\n'
    if message.author == bot.user:
        return
    if str(message.author) == 'monkeybard#3663' and message.content == '?cache':
        await bot.send_file(message.author, './data_cache.json')
        return
    luke_pattern = re.compile('.*gotta.*love.*luke', re.I)
    if luke_pattern.match(message.content):
        await bot.send_file(message.channel, './emotions/upset.png')
    lukas_pattern = re.compile('.*love.*lukas', re.I)
    if lukas_pattern.match(message.content):
        await bot.send_file(message.channel, './emotions/happy.png')
        await bot.send_message(message.channel,
                               random.choice(
                                   ['Thank you! I quite enjoy your company as well.',
                                    'That just made my day. I hope yours goes well too.',
                                    'It\'s very nice to be appreciated. Let\'s do our best!']))
    await bot.process_commands(message)

token = os.environ.get('TOKEN', default=None)
if token is None:
    token = open('./token').read().replace('\n', '')

utilities.setup(bot)

bot.run(token)
