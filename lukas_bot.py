import discord, os, re, random
from discord.ext import commands

import utilities, fehwiki_parse
from feh_cache import cache_log

bot = commands.Bot(command_prefix=['?', '? ', 'python ', 'Python ', 'python, ', 'Python, ', 'f?'], description="*yawn* Hm? I'm Python. Wake me up if you need me by starting your message with `?` or `python `.")

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    try:
        with open('./avatar.png', 'rb') as avatar:
            await bot.edit_profile(username='Python', avatar=avatar.read())
    except Exception as ex:
        print(ex)
        await bot.edit_profile(username='Python')
    await bot.change_presence(game=discord.Game(name="FEHWiki"))

luke_pattern = re.compile('.*gotta.*love.*luke', re.I)
lukas_pattern = re.compile('.*love.*lukas', re.I)
python_pattern = re.compile('.*love.*python', re.I)

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
    if luke_pattern.match(message.content):
        await bot.send_file(message.channel, './emotions/upset.png')

    if lukas_pattern.match(message.content):
        emotion, message_content = random.choice([
            ('happy.png', "Really now? I'll be sure to let him know."),
            ('sad.png', "Yeah, yeah. I'll pass the message one."),
            ('angry.png', "Seems like everybody does. Sorry he's not here anymore, I guess.")
        ])
        await bot.send_file(message.channel, './emotions/' + emotion)
        await bot.send_message(message.channel, message_content)
    if python_pattern.match(message.content):
        await bot.send_file(message.channel, './emotions/happy.png')
        await bot.send_message(message.channel, random.choice([
            "Well ain't that grand?",
            "Thanks, pal. You keep doing you.",
            "You hear that, Forsyth?"
        ]))
    await bot.process_commands(message)

token = os.environ.get('TOKEN', default=None)
if token is None:
    token = open('./token').read().replace('\n', '')

utilities.setup(bot)

bot.run(token)
