import discord, os, re, random
from discord.ext import commands
from lukas import Lukas
from lukas_quest import *

import utilities, chat, lukas_quest

bot = commands.Bot(command_prefix=['!', 'lukas '], description='I am here to serve. I will try to respond to messages that start with `!` or `lukas `.')

lukas = Lukas('./lukas_stats.json')
debug = False


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    lukas.print_status()
    await bot.change_presence(game=discord.Game(name="Steps Taken: " + str(lukas.steps_taken)))


# @bot.command()
# async def lukas_quest():
#     """Please type '!help lukas_quest' for the manual.
#
#     As with regular commands, you can interact with questing Lukas with the following commands, preceded by '!' or 'lukas ':
#         status            shows us the current status of Lukas
#         eat [item]       tell Lukas to eat a food item in his inventory (recovers stamina, HP, and can affect happiness)
#     Lukas will not take a step when you use these commands."""


@bot.event
async def on_message(message):
    # we do not want the bot to reply to itself
    if message.author == bot.user:
        return

    lukas_quest_channel = 'lukas-general'

    if message.author.id == '192820409937297418':
        if message.content == '!toggle_debug':
            global debug
            debug = not debug
            if debug:
                await bot.send_message(message.channel, "Now debugging Lukas Quest.")
            else:
                await bot.send_message(message.channel, "No longer debugging Lukas Quest.")

    # testing lukas quest
    if message.author.id == '192820409937297418' and (debug or message.channel == 'bot-stuff'):
        if message.content == '!lukas_quest_complete_reset':
            global lukas
            lukas = lukas.delete_status()
            await bot.send_message(message.channel, 'Lukas Quest completely reset.')
            return
        elif message.content.startswith('give'):
            item = message.content.split(' ', 1)[1].rstrip()
            lukas.inventory.add_item(item)
            lukas.print_status()
        else:
            num_steps = 1
            if message.content.startswith('step'):
                num_steps = int(message.content.split()[1].rstrip())

            for event in process_steps(lukas, num_steps):
                if event:
                    await bot.send_message(message.channel, event)
            lukas.print_status()
            return
    elif message.channel.name == lukas_quest_channel:
        if message.content.startswith('!status') or message.content.startswith('lukas status'):
            await bot.send_message(message.channel, lukas.get_status())
            return
        elif message.content.startswith('!eat') or message.content.startswith('lukas eat'):
            num_split = 2 if message.content.startswith('lukas eat') else 1
            args = message.content.split(' ', num_split)
            print(args)
            if len(args) < num_split:
                await bot.send_message(message.channel, "Please specify a food item.")
            else:
                food = args[num_split]
                await bot.send_message(message.channel, lukas.eat(food.lower().title()))
            return
        else:
            for event in process_steps(lukas, 1):
                if event:
                    await bot.send_message(message.channel, event)

    luke_pattern = re.compile('.*gotta.*love.*luke', re.I)
    if luke_pattern.match(message.content):
        lukas.affect_happiness(-20)
        await bot.send_file(message.channel, './emotions/upset.png')
    lukas_pattern = re.compile('.*love.*lukas', re.I)
    if lukas_pattern.match(message.content):
        lukas.affect_happiness(20)
        await bot.send_file(message.channel, './emotions/happy.png')
        await bot.send_message(message.channel,
                               random.choice(
                                   ['Thank you! I quite enjoy your company as well.',
                                    'That just made my day. I hope yours goes well too.',
                                    'It\'s very nice to be appreciated. Let\'s do our best!']))

    await bot.change_presence(game=discord.Game(name="Steps Taken: " + str(lukas.steps_taken)))
    await bot.process_commands(message)

token = os.environ.get('TOKEN', default=None)
if token is None:
    token = open('./token').read().replace('\n','')

utilities.setup(bot)
chat.setup(bot)
lukas_quest.setup(bot)

bot.run(token)
