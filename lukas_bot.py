import discord, os, random, re, pickle, numpy
from PIL import Image
from discord.ext import commands
from image_process import resize_and_crop
from lukas import Lukas

bot = commands.Bot(command_prefix=['!', 'lukas '], description='I am here to serve. I will try to respond to messages that start with `!` or `lukas `.')

def load_lukas():
    if os.path.exists('./lukas_stats'):
        print("A boy is loaded.")
        with open('./lukas_stats', 'rb') as to_load:
            return pickle.load(to_load)
    return Lukas('./lukas_stats')

foods = ['Sweet Cookie', 'Blue Cheese', 'Ham', 'Flour']
foods_dist = [0.2, 0.2, 0.2, 0.4]

def process_steps(num_steps):
    ret_strings = []

    def give_random_item():
        item = numpy.random.choice(foods, 1, foods_dist)[0]
        print(item)
        lukas.add_item(item)
        print("Gave " + item)
        return ["It appears I've found some " + item + '.']
    def give_exp():
        exp = numpy.random.choice([10, 15, 25, 50, 100], 1, [0.5, 0.25, 0.125, 0.1, 0.025])[0]
        result = process_exp(exp)
        print("Gave " + str(exp) + " EXP")
        return ["It appears I've gained " + str(exp) + ' experience.', result]

    events = {
        "item" : give_random_item,
        "exp" : give_exp
    }

    while num_steps > 0:
        if lukas.stamina > 0:
            if lukas.take_step(1):
                if lukas.steps_taken % 20 == 0 or lukas.steps_taken % 30 == 0:
                    #pick and perform event
                    event = numpy.random.choice(['item', 'exp'])
                    ret_strings += events[event]()
                num_steps -= 1
            else:
                ret_strings.append("I'm afraid... I can walk no further...")
                break
        else:
            break
    return ret_strings

def process_exp(exp):
    old_stats = lukas.get_stats_array()
    if lukas.give_exp(exp):
        levelupmessage = 'My mind must be playing tricks on me...'
        new_stats = lukas.get_stats_array()
        diff = new_stats - old_stats
        if (numpy.sum(diff)) > 1:
            if diff[1] or diff[5]:
                levelupmessage = 'Hmm... A palpable improvement.'
            elif diff[2] or diff[3]:
                levelupmessage = 'My senses feel sharp today.'
            else:
                levelupmessage = 'Luck appears to be on my side.'
        levelupstring = ''
        for i in diff:
            if i:
                levelupstring += '  ^|'
            else:
                levelupstring += '   |'
        return levelupmessage + str(lukas.stats)[:-3] + '\n' + levelupstring[:-1] + '```'
    return ''

lukas = load_lukas()
debug = False

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    lukas.print_status()
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
            for extension in ['.png', '.jpg', '.JPG']:
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

@bot.command()
async def lukas_quest():
    """Please type '!help lukas_quest' for the manual.
    Lukas Quest is a background game that will let Lukas grow as we chat in #lukas-general. He will level up and eventually promote, just like the real games!
    Every time we send a message, Lukas takes a step using stamina. Without stamina, Lukas will not move. For every couple of steps, Lukas will encounter one of 3 random events:
        * Obtaining a random item.
        * Gaining experience.
        * Encountering an enemy (unimplemented).
    As with regular commands, you can interact with questing Lukas with the following commands, preceded by '!' or 'lukas ':
        status            shows us the current status of Lukas
        feed [item]       tell Lukas to eat a food item in his inventory (recovers stamina, HP, and can affect happiness)
    Lukas will not take a step when you use these commands."""

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
    if (message.author.id == '192820409937297418' and debug) or message.channel == 'bot-stuff':
        if message.content == '!lukas_quest_complete_reset':
            os.remove('./lukas_stats')
            global lukas
            lukas = Lukas('./lukas_stats')
            await bot.send_message(message.channel, 'Lukas Quest completely reset.')
            return
        elif message.content.startswith('ls'):
            dir = message.content.split(' ', 1)[1].rstrip()
            await bot.send_message(message.channel, str(os.listdir(dir)))
        elif message.content.startswith('status'):
            await bot.send_message(message.channel, lukas.get_status())
        elif message.content.startswith('levelup'):
            await bot.send_message(message.channel, process_exp(100))
        elif message.content.startswith('!feed') or message.content.startswith('lukas feed'):
            num_split = 2 if message.content.startswith('lukas feed') else 1
            args = message.content.split(' ', num_split)
            print(args)
            if len(args) < num_split:
                await bot.send_message(message.channel, "Please specify a food item.")
            else:
                food = args[num_split]
                await bot.send_message(message.channel, lukas.feed(food.lower().title()))
        elif message.content.startswith('give'):
            item = message.content.split(' ', 1)[1].rstrip()
            lukas.inventory.add_item(item)
        else:
            num_steps = 1
            if message.content.startswith('step'):
                num_steps = int(message.content.split()[1].rstrip())

            for event in process_steps(num_steps):
                if event:
                    await bot.send_message(message.channel, event)
        lukas.print_status()
        return
    elif message.channel.name == lukas_quest_channel:
        if message.content.startswith('!status') or message.content.startswith('lukas status'):
            await bot.send_message(message.channel, lukas.get_status())
            return
        elif message.content.startswith('!feed') or message.content.startswith('lukas feed'):
            num_split = 3 if message.content.startswith('lukas feed') else 4
            food = message.content.split(num=num_split)[num_split-1]
            print(food)
            await bot.send_message(message.channel, lukas.feed(food))
            return
        else:
            for event in process_steps(1):
                if event:
                    await bot.send_message(message.channel, event)

    luke_pattern = re.compile('.*gotta.*love.*luke', re.I)
    if luke_pattern.match(message.content):
        lukas.affect_happiness(-20)
        await bot.send_message(message.channel, '<:upsetlukas:326630615065559041>')
    lukas_pattern = re.compile('.*love.*lukas', re.I)
    if lukas_pattern.match(message.content):
        lukas.affect_happiness(20)
        await bot.send_message(message.channel, '<:lukas:316202740495679488>')
    await bot.process_commands(message)

token = os.environ.get('TOKEN', default=None)
if token is None:
    token = open('./token').read().replace('\n','')
bot.run(token)
