import numpy
from discord.ext import commands as bot


foods = ['Sweet Cookie', 'Blue Cheese', 'Ham', 'Flour']
foods_dist = [0.2, 0.2, 0.2, 0.4]


def process_steps(lukas, num_steps):
    ret_strings = []

    def give_random_item():
        item = numpy.random.choice(foods, 1, foods_dist)[0]
        print(item)
        lukas.add_item(item)
        print("Gave " + item)
        return ["It appears I've found some " + item + '.']
    def give_exp():
        exp = numpy.random.choice([10, 15, 25, 50, 100], 1, [0.5, 0.25, 0.125, 0.1, 0.025])[0]
        result = process_exp(lukas, exp)
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


def process_exp(lukas, exp):
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


class LukasQuest:
    """Lukas Quest is a background game that will let Lukas grow as we chat in #lukas-general. He will level up and eventually promote, just like the real games!
    Every time we send a message, Lukas takes a step using stamina. Without stamina, Lukas will not move. For every couple of steps, Lukas will encounter one of 3 random events:
        * Obtaining a random item.
        * Gaining experience.
        * Encountering an enemy (unimplemented)."""
    def __init__(self, bot):
        self.bot = bot


def setup(bot):
    bot.add_cog(LukasQuest(bot))
