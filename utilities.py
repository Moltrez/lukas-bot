import discord, random, argparse, os.path, itertools
import numpy as np
from socket import timeout
from discord.ext import commands as bot
from fehwiki_parse import *
from difflib import SequenceMatcher

import feh_cache


class MagikarpJump:
    """The game we don't play anymore."""

    def __init__(self, bot):
        self.bot = bot

    @bot.command(aliases=['Lmr'])
    async def lmr(self):
        """I will tell you which rod will net you the best Magikarp."""
        await self.bot.say(random.choice(['L', 'M', 'R']))


class ASCIIMessage:

    def __init__(self, title):
        self._message = '%-45.45s\n' % ('[' + title + ']')
        self.inline_count = 0
        self.last_value = ''

    def add_field(self, name, value, inline):
        if inline:
            self._message += '%-22.22s' % ('[' + name + ']')
            if self.inline_count == 0:
                # first message to inline
                self.last_value = value
                self.inline_count = 1
            elif self.inline_count == 1:
                # second message to inline
                self._message += '\n%-22.22s%-22.22s\n' % (self.last_value, value)
                self.inline_count = 0
        if not inline:
            if self.inline_count != 0:
                self._message += ' ' * 23 + '\n%-45.45s\n' % self.last_value
                self.inline_count = 0
            self._message += '%-45.45s\n' % ('[' + name + ']')
            for line in value.split('\n'):
                if not line:
                    continue
                line = line.replace('`', '')
                if '_' in line:
                    underindex = line.find('_')
                    line = ';' + line[:underindex] + line[underindex + 1:]
                if '**' in line:
                    curr_brack = '['
                    while '**' in line:
                        line = line.replace('**', curr_brack, 1)
                        curr_brack = ']' if curr_brack == '[' else ']'
                self._message += line + '\n'

    @property
    def message(self):
        return '```ini\n' + self._message + '```'

    @message.setter
    def message(self, value):
        self._message = value


# these are constant so declare up here
stats = ['HP', 'ATK', 'SPD', 'DEF', 'RES']
merge_bonuses = [np.zeros(5), np.array([1,1,0,0,0]), np.array([1,1,1,1,0]), np.array([2,1,1,1,1]), np.array([2,2,2,1,1]), np.array([2,2,2,2,2]),
                 np.array([3,3,2,2,2]), np.array([3,3,3,3,2]), np.array([4,3,3,3,3]), np.array([4,4,4,3,3]), np.array([4,4,4,4,4])]
summoner_bonuses = {None:np.zeros(5), 'c':np.array([3,0,0,0,2]), 'b':np.array([4,0,0,2,2]), 'a':np.array([4,0,2,2,2]), 's':np.array([5,2,2,2,2])}
separators = ['v', 'vs', '-v', '&', '|']
diff_limit = 6
compare_limit = 40

def find_arg(args, param_list, return_list, param_type, remove=True):
    """Finds arguments that exist in param_list and return the corresponding value from return_list."""
    arg_finding = [i in args for i in param_list]
    arg_index = None
    if arg_finding.count(True) > 1:
        raise ValueError('Multiple %s specified.' % param_type)
    elif arg_finding.count(True) == 1:
        arg_index = arg_finding.index(True)
    arg = return_list[arg_index] if arg_index is not None else None
    if arg is not None and remove:
        args.remove(param_list[arg_index])
    return arg, args


def table_to_array(table, boon, bane, rarity):
    #convert dictionary format to numpy arrays, accounting for boons banes and rarity
    array = np.zeros((5,5), dtype=np.int32)
    keys = ['Rarity', 'HP', 'ATK', 'SPD', 'DEF', 'RES', 'Total']
    for i in range(len(table)):
        row = table[i]
        row_rarity = int(row['Rarity'])
        if rarity is not None and row_rarity != rarity:
            continue
        else:
            row_rarity -= 1
        for key in keys:
            if key in ['Rarity','Total']:
                continue
            stat = row[key].split('/')
            if any([not s.isdigit() for s in stat]):
                raise ValueError('This hero does not appear to have stats yet.')
            stat_index = 1
            if boon and key == boon:
                stat_index = 2
            elif (bane and key == bane):
                stat_index = 0
            if len(stat) != 3:
                stat_index = 0
            array[row_rarity][stats.index(key)] = stat[stat_index]
    return array

def array_to_table(array):
    # convert numpy array back to dictionary format
    if isinstance(array, list):
        return array
    ret = []
    for i in range(len(array)):
        # skip empty rows
        if any(array[i]):
            p1 = {'Rarity':str(i+1)}
            p2 = {stats[j]:str(array[i][j]) for j in range(5)}
            p3 = {'Total':str(array[i].sum())}
            row = dict(p1, **p2)
            row.update(p3)
            ret.append(row)
    return ret

class FireEmblemHeroes:
    """The game that we do still play a lot."""

    def __init__(self, bot):
        self.bot = bot
        self.cache = feh_cache.FehCache()

    def find_similar(self, arg):
        return '\n'.join(
            [p[0] + ' _(' +
             (('Categories: ' +
             ', '.join([c for c in self.cache.categories[self.cache.aliases[p[0]]]
                        if any(helpful in c and helpful not in ['Weapons', 'Heroes', 'Passives'] for helpful in
                               valid_categories +
                               ['Sword', 'Axe', 'Lance', 'Bow', 'Dagger', 'Breath', 'Tome', 'Cavalry', 'Infantry',
                                'Flying', 'Armored', 'A ', 'B ', 'C ', 'Sacred Seals', 'Tempest Trials'])]))
              if self.cache.aliases[p[0]] in self.cache.categories else ('Old Page: ' + self.cache.aliases[p[0]]))
              + ')_'
             for p in
             sorted([[page, SequenceMatcher(None, arg.lower().replace(' ', ''), page).ratio()]
                     for page in self.cache.aliases], key=lambda x:x[1], reverse=True)[:3]
             ]
        )

    def find_data(self, arg, original_arg, ctx=None, ignore_cache=False):
        try:
            arg = find_name(arg, self.cache, ctx=ctx)
            if arg == INVALID_HERO:
                if ctx:
                    if original_arg.lower() in ['son', 'my son']:
                        return False, False,\
                            "I was not aware you had one. If you want me to associate you with one, use the setson command."
                    elif original_arg.lower() in ['waifu', 'my waifu']:
                        return False, False,\
                            "I was not aware you had one. If you want me to associate you with one, use the setwaifu command."
                return False, False,\
                       "I'm afraid I couldn't find information on %s. Could you have meant:\n%s"\
                       % (original_arg.replace('*','\*').replace('_','\_'), self.find_similar(original_arg))

            data = None
            if arg in self.cache.data and not ignore_cache:
                categories = self.cache.categories[arg]
                data = self.cache.data[arg]
            if data is None or arg in self.cache.replacement_list:
                new_categories, new_data = get_data(arg)
                if new_data is None:
                    return False, False,\
                           "I'm afraid I couldn't find information on %s." % arg
                else:
                    categories = new_categories
                    data = new_data
                    if arg in self.cache.replacement_list:
                        self.cache.replacement_list.remove(arg)
            return arg, categories, data
        except timeout:
            print('Timed out')
            if arg and categories and data:
                return arg, categories, data
            return False, False, 'Unfortunately, it seems like I cannot access my sources in a timely fashion at the moment. Please try again later.'
        except urllib.error.HTTPError as err:
            if arg and categories and data:
                return arg, categories, data
            print(err)
            if err.code >= 500:
                return False, False,\
                    "Unfortunately, it seems like I cannot access my sources at the moment. Please try again later."
        except KeyError:
            if arg and categories and data:
                return arg, categories, data
            return False, False, 'It appears the data I have is incomplete. Please try again later.'

    def get_unit_stats(self, args, default_rarity=None, ctx=None):
        # convert to lower case
        args = list(map(lambda x: x.lower(), args))

        # split a *+ if it exists
        to_remove = None
        for arg in args:
            if '*+' in arg:
                to_remove = arg
                r, m = arg.split('+', 1)
                args.append(r)
                args.append('+'+m)
        if to_remove:
            args.remove(to_remove)

        # get IV information
        boons = ['+' + s.lower() for s in stats]
        banes = ['-' + s.lower() for s in stats]
        boon, args = find_arg(args, boons, stats, 'boons')
        bane, args = find_arg(args, banes, stats, 'banes')
        if boon and not bane:
            return False, 'Only boon (+%s) specified.' % boon
        if bane and not boon:
            return False, 'Only bane (-%s) specified.' % bane
        if boon is not None and bane is not None:
            if (boon == bane):
                return False, 'Boon is the same as bane.'
        # get merge number
        merges = ['+' + str(i) for i in range(1, 11)]
        merge, args = find_arg(args, merges, range(1, 11), 'merge levels')
        # get summoner support level
        supports = ['c', 'b', 'a', 's']
        support, args = find_arg(args, supports, supports, 'summoner support levels')
        # get rarity
        rarities = [str(i) + '*' for i in range(1, 6)]
        rarity, args = find_arg(args, rarities, range(1, 6), 'rarities')
        if rarity is None:
            rarity = default_rarity
        # check for manual stat modifiers as well
        modifiers = [a for a in args if '/' in a]
        if modifiers:
            for i in range(len(modifiers)):
                modifier = modifiers[i]
                args.remove(modifier)
                # check that each modifier is valid
                modifier = modifier.split('/')
                if len(modifier) > 5:
                    return 'Too many stat modifiers specified.'
                if not all([m[0] in ['-', '+'] + list(map(str, range(10))) and (m[1:].isdigit() or m[1:] == '') for m in
                            modifier]):
                    return 'Stat modifiers in wrong format (-number or +number).'
                modifier_array = np.zeros(5, dtype=np.int32)
                modifier_array[:len(modifier)] = list(map(int, modifier))
                modifiers[i] = modifier_array
            modifiers = np.array(modifiers).sum(axis=0)
        else:
            modifiers = None

        # get the hero information
        args = ' '.join(args)
        unit, categories, data = self.find_data(args, args, ctx)
        if not unit:
            return False, data
        should_save = self.cache.add_data(args, data, categories, save=False)
        if 'Heroes' not in categories:
            return should_save, '%s does not seem to be a hero.' % (unit)

        base_stats_table = data['4Base Stats'][0]
        max_stats_table = data['5Max Level Stats'][0]
        if base_stats_table is None or max_stats_table is None:
            return should_save, 'This hero does not appear to have stats.'
        if boon is None and bane is None and rarity is None and merge is None and support is None and modifiers is None:
            return should_save, (data['Embed Info'], base_stats_table, max_stats_table)
        base_stats = table_to_array(base_stats_table, boon, bane, rarity)
        max_stats = table_to_array(max_stats_table, boon, bane, rarity)
        # check if empty
        if not any([any(r) for r in base_stats]):
            return should_save, 'This hero does not appear to be available at the specified rarity.'
        # calculate merge bonuses
        if merge is not None:
            for i in range(5):
                if any(base_stats[i]):
                    ordered_stats = (-base_stats[i]).argsort()
                    bonuses = np.zeros(5, dtype=np.int32)
                    bonuses[ordered_stats] = merge_bonuses[merge]
                    base_stats[i] += bonuses
                    max_stats[i] += bonuses
        # summoner bonuses
        if support is not None:
            for i in range(5):
                if any(base_stats[i]):
                    base_stats[i] += summoner_bonuses[support]
                    max_stats[i] += summoner_bonuses[support]
        # add flat modifiers
        if modifiers is not None:
            for i in range(5):
                if any(base_stats[i]):
                    base_stats[i] += modifiers
                    max_stats[i] += modifiers
        return should_save, (data['Embed Info'], base_stats, max_stats)

    @bot.command(aliases=['gauntlet', 'Gauntlet', 'Fehgauntlet', 'FEHgauntlet', 'FEHGauntlet'])
    async def fehgauntlet(self):
        """I will tell you the current Voting Gauntlet score."""
        try:
            scores = get_gauntlet_scores()
        except urllib.error.HTTPError as err:
            if err.code >= 500:
                await self.bot.say("Unfortunately, it seems like I cannot access my sources at the moment. Please try again later.")
                return
        longest = max(scores, key=lambda s: len(s[0]['Score']) + len(s[0]['Status']) + 3)
        longest = len(longest[0]['Score']) + len(longest[0]['Status']) + 3
        message = '```'
        for s in scores:
            message += """{:>{width}} vs {}
{:>{width}}    {}
""".format(s[0]['Name'], s[1]['Name'], (s[0]['Score'] + ' (' + s[0]['Status'] + ')'), ('(' + s[1]['Status'] + ') ' +  s[1]['Score']), width = longest)
        message += '```'
        await self.bot.say(message)

    @bot.command(pass_context=True)
    async def setson(self, ctx, *, son):
        """Set your son so you can find their information easily with `?feh son`! Unset your son with `?setson none`."""
        true_son = None if son.lower() == 'none' else find_name(son, self.cache)
        if true_son == INVALID_HERO:
            true_son = son
        self.cache.set_fam('son', str(ctx.message.author.id), true_son)
        if true_son is None:
            await self.bot.say('You no longer have a son.')
        else:
            await self.bot.say('Successfully set your son to %s (%s). You can now search for that unit with `?feh son`!' % (son, true_son))

    @bot.command(pass_context=True)
    async def setwaifu(self, ctx, *, waifu):
        """Set your waifu so you can find their information easily with `?feh waifu`! Unset your waifu with `?setwaifu none`."""
        true_waifu = None if waifu.lower() == 'none' else find_name(waifu, self.cache)
        if true_waifu == INVALID_HERO:
            true_waifu = waifu
        self.cache.set_fam('waifu', str(ctx.message.author.id), true_waifu)
        if true_waifu is None:
            await self.bot.say('You no longer have a waifu.')
        else:
            await self.bot.say('Successfully set your waifu to %s (%s). You can now search for that unit with `?feh waifu`!' % (waifu, true_waifu))

    @bot.command(pass_context=True, aliases=['toggle', 'Toggle'])
    async def toggledefaultformat(self, ctx):
        """Change your default presentation format between my embeds and Python's codeblocks."""
        result = self.cache.toggle_preference(ctx.message.author.id)
        if result:
            await self.bot.say("I have noted that you prefer Python's codeblocks.")
        else:
            await self.bot.say("I have noted that you prefer my embeds.")

    @bot.command(pass_context=True, aliases=['Feh', 'FEH'])
    async def feh(self, ctx, *, arg):
        """I will provide some information on any Fire Emblem Heroes topic."""
        # admin controls
        ignore_cache = False
        if str(ctx.message.author) == 'monkeybard#3663':
            if arg.startswith('-i '):
                arg = arg[3:]
                ignore_cache = True
            elif arg.startswith('-d '):
                arg = arg[3:]
                args = arg.split('&')
                should_save = False
                for arg in args:
                    should_save = self.cache.delete_alias(arg, save=False) or should_save
                if should_save:
                    self.cache.save()
                await self.bot.say("Deleted!")
                return
            elif arg.startswith('-a '):
                arg = arg[3:]
                args = arg.split(' ', 1)
                aliases = args[0].split('&')
                should_save = False
                for alias in aliases:
                    should_save = self.cache.add_alias(alias, args[1], save=False, resolve_conflicts=False) \
                                  or should_save
                if should_save:
                    self.cache.save()
                await self.bot.say("Added!")
                return
            elif arg.startswith('-aliases'):
                f_string = 'aliases = {\n'
                f_string += ',\n'.join(
                    ['    "%s": "%s"' %(alias, self.cache.aliases[alias]) for alias in self.cache.aliases])
                f_string += '\n}\n'
                f = io.BytesIO(bytes(f_string, 'utf-8'))
                f.name = 'feh_alias.py'
                await self.bot.upload(f)
                return
            elif arg.startswith('-sanitizealiases'):
                for alias in list(self.cache.aliases):
                    if alias[-1] in ['1','2','3']:
                        self.cache.delete_alias(alias, save=False)
                    else:
                        self.cache.resolve_alias(alias, save=False)
                self.cache.save()
                return
            elif arg.startswith('-cleandatabase'):
                linked_to = {self.cache.aliases[a] for a in self.cache.aliases}
                for page in list(self.cache.data):
                    if not any([c in ['Heroes', 'Passives', 'Weapons', 'Specials', 'Assists', 'Disambiguation pages']
                            for c in self.cache.categories[page]]) or page not in linked_to:
                        self.cache.delete_data(page, save=False)
                self.cache.save()
                return
            elif arg.startswith('-clearcategory '):
                arg = arg[len('-clearcategory '):]
                self.cache.clear_category(arg)
                await self.bot.say("Cleared!")
                return
            elif arg.startswith('-reload'):
                self.cache.load()
                await self.bot.say("Reloaded!\n" + self.cache.last_update)
                return
            elif arg.startswith('-currreplace'):
                message = ''
                for r in self.cache.replacement_list:
                    if len(message) + len(r) >= 2000:
                        await self.bot.say(message)
                        message = ''
                    message += r + ', '
                if message:
                    await self.bot.say(message)
                return
            elif arg.startswith('-clearreplace'):
                save = False
                for r in self.cache.replacement_list:
                    if self.cache.delete_data(r):
                        save = True
                self.cache.replacement_list.clear()
                if save:
                    self.cache.save()
                await self.bot.say("Cleared replacement list!")
                return

        python_format = ctx.message.author.id in self.cache.python_preference
        if '-lukas' in arg:
            python_format = False
            l_i = arg.find('-lukas')
            arg = (arg[:l_i] + arg[l_i+6:]).replace('  ', ' ')
        if '-python' in arg:
            python_format = True
            l_i = arg.find('-python')
            arg = (arg[:l_i] + arg[l_i + 7:]).replace('  ', ' ')

        self.cache.update()
        original_arg = arg
        passive_level = -1
        if arg[-1] in ['1','2','3', '4', '5']:
            passive_level = int(arg[-1]) - 1
            arg = arg[:-1].strip()
        arg, categories, original_data = self.find_data(arg, original_arg, ctx, ignore_cache)
        if not arg:
            if original_data.startswith("I'm"):
                if any([(' ' + separator + ' ') in original_arg for separator in separators]) or\
                        original_arg.lower().startswith('compare'):
                    await self.bot.say(
                    "I'm afraid I couldn't find data of %s. Did you mean to do `?compare %s`?" %
                    (original_arg.replace('*','\*').replace('_','\_'),
                     original_arg if not original_arg.lower().startswith('compare') else original_arg[7:].strip()))
                elif any([modifier in original_arg for modifier in
                          ['-f', '-s', '-r']]) or original_arg.lower().startswith('list'):
                    await self.bot.say(
                        "I'm afraid I couldn't find data of %s. Did you mean to do `?list %s`?" %
                        (original_arg.replace('*','\*').replace('_','\_'),
                         original_arg if not original_arg.lower().startswith('list') else original_arg[4:].strip()))
                elif any([modifier in original_arg for modifier in
                             ['-', '/', '+']]) and not original_arg.endswith('+'):
                    if '/' in original_arg:
                        slashloc = original_arg.find('/')
                        if slashloc > 0 and \
                            all(c in map(str,range(10))
                                for c in [original_arg[slashloc-1], original_arg[slashloc+1]]):
                            await self.bot.say(
                                "I'm afraid I couldn't find data of %s. Did you mean to do `?stats %s`?" %
                                (original_arg.replace('*','\*').replace('_','\_'),
                                 original_arg if not original_arg.lower().startswith('stats') else original_arg[
                                                                                                   5:].strip()))
                        else:
                            await self.bot.say(original_data)
                    else:
                        await self.bot.say(
                        "I'm afraid I couldn't find data of %s. Did you mean to do `?stats %s`?" %
                        (original_arg.replace('*','\*').replace('_','\_'),
                         original_arg if not original_arg.lower().startswith('stats') else original_arg[5:].strip()))
                else:
                    await self.bot.say(original_data)
                    return
            else:
                await self.bot.say(original_data)
            return

        if 'Passives' in categories:
            if original_data['Embed Info']['Title'] == 'HP Plus' and passive_level in [2,3,4]:
                passive_level -= 2
            if passive_level < len(original_data['Data']):
                data = original_data['Data'][passive_level]
            else:
                data = original_data['Data'][-1]
        else:
            data = original_data

        if original_arg.startswith('list'):
            data['Message'] = 'Did you mean `?list %s`?' % original_arg[4:].strip()
        elif original_arg.lower() == 'gauntlet':
            data['Message'] = 'Did you mean `?gauntlet`?'

        if python_format:
            message = ASCIIMessage(title=data['Embed Info']['Title'])
        else:
            message = discord.Embed(
                title= data['Embed Info']['Title'],
                url= data['Embed Info']['URL'],
                color= data['Embed Info']['Colour']
            )
            if data['Embed Info']['Icon']:
                message.set_thumbnail(url=data['Embed Info']['Icon'])
            elif 'Specials' in categories:
                message.set_thumbnail(url='https://d1u5p3l4wpay3k.cloudfront.net/feheroes_gamepedia_en/2/25/Icon_Skill_Special.png')
            elif 'Assists' in categories:
                message.set_thumbnail(url='https://d1u5p3l4wpay3k.cloudfront.net/feheroes_gamepedia_en/9/9a/Icon_Skill_Assist.png')
        for key in sorted(data.keys()):
            if key[0].isdigit():
                    message.add_field(
                        name=key[1:],
                        value=data[key][0] if key not in ['4Base Stats', '5Max Level Stats'] else format_stats_table(data[key][0]),
                        inline=data[key][1]
                    )
                    if 'Exclusive?' in key:
                        if 'Evolution' in data:
                            refinable = 'Evolves and Refines' if 'Refine' in data else 'Evolves'
                        elif 'Refine' in data:
                            refinable = 'Yes'
                        else:
                            refinable = 'No'
                        message.add_field(
                            name='Refinable?',
                            value= refinable,
                            inline=True
                        )
        if 'Message' in data:
            if python_format:
                await self.bot.say(data['Message'].replace('. ', '.\n') + '\n' + message.message)
            else:
                await self.bot.say(data['Message'].replace('. ', '.\n'), embed=message)
        else:
            if python_format:
                await self.bot.say(message.message)
            else:
                await self.bot.say(embed=message)
        self.cache.add_data(original_arg, original_data, categories)

    @bot.command(pass_context=True, aliases=['refine', 'Refine', 'Fehrefine', 'FEHRefine'])
    async def fehrefine(self, ctx, *, args):
        """View the refinery options for a weapon."""
        self.cache.update()

        python_format = ctx.message.author.id in self.cache.python_preference
        if '-lukas' in args:
            python_format = False
            l_i = args.find('-lukas')
            args = (args[:l_i] + args[l_i+6:]).replace('  ', ' ')
        if '-python' in args:
            python_format = True
            l_i = args.find('-python')
            args = (args[:l_i] + args[l_i + 7:]).replace('  ', ' ')

        while (True):
            weapon, categories, data = self.find_data(args, args)
            if not weapon:
                await self.bot.say(data)
                return
            if 'Weapons' not in categories:
                await self.bot.say('%s does not seem to be a weapon.' % (weapon))
                return
            if 'Refine' not in data and 'Evolution' not in data:
                if data['3Exclusive?'][0] == ('No') and not weapon.endswith('+'):
                    args = weapon + '+'
                else:
                    await self.bot.say('It appears that %s cannot be refined.' % (weapon))
                    self.cache.save()
                    return
            else:
                break
        # initial weapon message
        if python_format:
            message1 = ASCIIMessage(title=data['Embed Info']['Title'])
        else:
            message1 = discord.Embed(
                title= data['Embed Info']['Title'],
                url= data['Embed Info']['URL'],
                color= data['Embed Info']['Colour']
            )
            if data['Embed Info']['Icon']:
                message1.set_thumbnail(url=data['Embed Info']['Icon'])
        for key in sorted(data.keys()):
            if key != '3Exclusive?' and key[0].isdigit() and 'Heroes with' not in key:
                message1.add_field(
                    name=key[1:],
                    value=data[key][0],
                    inline=data[key][1]
                )
        if 'Refinery Cost' in data:
            message1.add_field(
                name='Refinery Cost',
                value=data['Refinery Cost'],
                inline=False
            )
        if 'Evolution Cost' in data:
            message1.add_field(
                name='Evolution Cost',
                value=data['Evolution Cost'],
                inline=False
            )
        message2 = None
        message3 = None
        if 'Refine' in data:
            if python_format:
                message2 = ASCIIMessage(title='Refinery Options')
            else:
                message2 = discord.Embed(
                    title= 'Refinery Options',
                    url= data['Embed Info']['URL'],
                    color= 0xD6BD53
                )
                if 'Refine Icon' in data:
                    message2.set_thumbnail(url=data['Refine Icon'])
                else:
                    if 'Staves' in categories:
                        message2.set_thumbnail(url='https://d1u5p3l4wpay3k.cloudfront.net/feheroes_gamepedia_en/4/42/Wrathful_Staff_W.png')
                    else:
                        message2.set_thumbnail(url='https://d1u5p3l4wpay3k.cloudfront.net/feheroes_gamepedia_en/2/20/Attack_Plus_W.png')
            for r in data['Refine']:
                value = ''
                if r['Stats'] != '+0 HP':
                    value += r['Stats'] + '\n'
                effect = r['Effect'].replace((data['5Special Effect'][0] if '5Special Effect' in data else ''),'')
                if effect:
                    value += effect.strip()
                message2.add_field(
                    name=r['Type'],
                    value=value.strip(),
                    inline=False
                )
        if 'Evolution' in data:
            # weapon evolves
            args2 = data['Evolution'][0]
            weapon2, categories2, data2 = self.find_data(args2, args2)
            if not weapon2:
                await self.bot.say(data2)
                return
            # evolved weapon message
            if python_format:
                message3 = ASCIIMessage(title=data2['Embed Info']['Title'])
            else:
                message3 = discord.Embed(
                    title= data2['Embed Info']['Title'],
                    url= data2['Embed Info']['URL'],
                    color= data2['Embed Info']['Colour']
                )
                if data2['Embed Info']['Icon']:
                    message3.set_thumbnail(url=data2['Embed Info']['Icon'])
            for key in sorted(data2.keys()):
                if key != '3Exclusive?' and key[0].isdigit() and 'Heroes with' not in key:
                    message3.add_field(
                        name=key[1:],
                        value=data2[key][0],
                        inline=data2[key][1]
                    )
        if python_format:
            to_send = message1.message
            if message2 is not None:
                if len(to_send) + len(message2.message) < 2000:
                    to_send += message2.message
                else:
                    await self.bot.say(to_send)
                    to_send = message2.message
            if message3 is not None:
                if len(to_send) + len(message3.message) < 2000:
                    to_send += message3.message
                else:
                    await self.bot.say(to_send)
                    to_send = message3.message
            if to_send:
                await self.bot.say(to_send)
        else:
            await self.bot.say(embed=message1)
            if message2 is not None:
                await self.bot.say(embed=message2)
            if message3 is not None:
                await self.bot.say(embed=message3)
        if 'Evolution' in data:
            save = self.cache.add_data(weapon, data, categories, save=False)
            self.cache.add_data(weapon2, data2, categories2, force_save=save)
        else:
            self.cache.add_data(weapon, data, categories)

    flaunt_cache = {}

    @bot.command(pass_context=True, aliases=['flaunt', 'Flaunt', 'Fehflaunt', 'FEHFlaunt'])
    async def fehflaunt(self, ctx, *args):
        """Use this command to show off your prized units.
If you want to add a flaunt please send a screenshot of your unit to monkeybard, Datagne, Zylphe, Mortagon or InvdrZim13."""
        user = str(ctx.message.author.id)
        username = str(ctx.message.author)
        if len(args) == 3 and user in ['192820409937297418', '70087410221842432', '69620122100183040', '138570558479532033', '70130363044732928'] and args[0] == '-a':
            img_url = args[2].strip('<>')
            self.cache.set_flaunt(args[1], img_url)
            if args[1] in self.flaunt_cache:
                del self.flaunt_cache[args[1]]
            await self.bot.say("Flaunt changed!")
            return
        f = None
        if user in self.cache.flaunts:
            f = False
            if user in self.flaunt_cache:
                f = self.flaunt_cache[user]
        else:
            # update name to id
            if username in self.cache.flaunts:
                f = False
                img_url = self.cache.flaunts[username]
                del self.cache.flaunts[username]
                self.cache.set_flaunt(user, img_url)
                if username in self.flaunt_cache:
                    f = self.flaunt_cache[username]
                    del self.flaunt_cache[username]
                    self.flaunt_cache[user] = f
        if f is not None and not f:
            print("Downloading flaunt for "+username)
            request = urllib.request.Request(self.cache.flaunts[user].replace('cdn.discordapp.com', 'media.discordapp.net') + '?width=384&height=683', headers={'User-Agent': 'Mozilla/5.0'})
            response = urllib.request.urlopen(request)
            f = response.read()
            self.flaunt_cache[user] = f
        elif f is None:
            await self.bot.say("I'm afraid you have nothing to flaunt. If you want to add a flaunt please send a screenshot of your unit to monkeybard, Datagne, Zylphe, Mortagon or InvdrZim13.")
            return
        f = io.BytesIO(f)
        f.name = os.path.basename(self.cache.flaunts[user])
        print("Uploading flaunt for "+username)
        await self.bot.upload(f)

    @bot.command(pass_context=True, aliases=['stats', 'stat', 'fehstat', 'Stats', 'Stat', 'Fehstat', 'Fehstats', 'FEHstat', 'FEHStat', 'FEHstats', 'FEHStats'])
    async def fehstats(self, ctx, *args):
        """I will calculate the stats of a unit given some parameters.
Possible Parameters (all optional):
                    +[boon], -[bane]: specify a unit's boon and bane where [boon] and [bane] are one of the following: HP, ATK, SPD, DEF, RES. The boon and bane cannot specify the same stat. If a boon or a bane is specified the other must be as well. Default is neutral. Example: +spd -hp
          +[number between 1 and 10]: specify the level of merge a unit is. Default is no merges. Example: +5
                        [c, b, a, s]: specify the level of summoner support the unit has. Default is no support. Example: s
[number/number/number/number/number]: specify any additional modifiers such as modifiers from skills or weapon mt. The order is HP/ATK/SPD/DEF/RES. If you specify less than 5 modifiers, for example 1/1/1, it will add 1 to HP/ATK/SPD only. You can have as many of these as you want. Default is no modifiers. Example: 0/5/-5/0/0
           [number between 1 and 5]*: specify the rarity of the unit. If left unspecified, shows stats for all rarities. Example: 5*
Example usage:
?stats lukas 5* +10 s +def -spd 0/14 0/-3/0/5
will show the stats of a 5* Lukas merged to +10 with +Def -Spd IVs with a Summoner S Support and an additional 14 attack (presumably from a Slaying Lance+) as well as -3 attack and +5 defense (presumably from Fortress Defense)."""
        self.cache.update()

        python_format = ctx.message.author.id in self.cache.python_preference
        if '-lukas' in args:
            python_format = False
            args = list(args)
            args.remove('-lukas')
        if '-python' in args:
            python_format = True
            args = list(args)
            args.remove('-python')

        should_save, unit_stats = self.get_unit_stats(args, ctx=ctx)
        if isinstance(unit_stats, tuple):
            embed_info, base, max = unit_stats
            base = array_to_table(base)
            max = array_to_table(max)
            if python_format:
                message = ASCIIMessage(title=embed_info['Title'])
            else:
                message = discord.Embed(
                    title=embed_info['Title'],
                    url=embed_info['URL'],
                    color=embed_info['Colour']
                )
                if not embed_info['Icon'] is None:
                    message.set_thumbnail(url=embed_info['Icon'])
            message.add_field(
                name="BST",
                value=max[-1]['Total'],
                inline=False
            )
            message.add_field(
                name="Base Stats",
                value=format_stats_table(base),
                inline=False
            )
            message.add_field(
                name="Max Level Stats",
                value=format_stats_table(max),
                inline=False
            )
            if python_format:
                await self.bot.say(message.message)
            else:
                await self.bot.say(embed=message)
        else:
            await self.bot.say(unit_stats)
        if should_save:
            self.cache.save()

    @bot.command(pass_context=True, aliases=['Fehcompare', 'compare', 'Compare', 'FEHcompare', 'FEHCompare'])
    async def fehcompare(self, ctx, *args):
        """I will compare the max stats of two units with specified parameters.
Please reference ?help fehstats for the kinds of accepted parameters.
Simply type in unit builds as you would with ?fehstats and add a v or vs between the units.
Up to 15 units can be compared at the same time.
By default differences will be shown when comparing 2 units but not for more.
Use -d to show the difference as well as the stats. Use -q to only show the difference. Use -a to show who has the highest of each stat.
Unlike ?fehstats, if a rarity is not specified I will use 5★ as the default."""
        self.cache.update()

        args = list(map(lambda a:a.lower(), args))
        # try:
        #     separator, args = find_arg(args, separators, separators, 'separator', remove=False)
        # except ValueError as err:
        #     # multiple separators
        #     await self.bot.say("Please use one "+', '.join(list(map(lambda s:'`'+s+'`', separators[:-1]))) +" or `|` to separate the units you wish to compare.")
        #     return
        sep_finding = [i in args for i in separators]
        # no separators
        if not any(sep_finding):
            await self.bot.say("Please separate the units you wish to compare using "+', '.join(list(map(lambda s:'`'+s+'`', separators[:-1]))) +" or `|`.")
            return
        quiet_mode = False
        stats_mode = True
        analytics_mode = False
        if '-q' in args:
            quiet_mode = True
            stats_mode = False
            args.remove('-q')
        if '-d' in args:
            quiet_mode = True
            args.remove('-d')
        if '-a' in args:
            analytics_mode = True
            args.remove('-a')
        common_args = []
        if '-all' in args:
            all_i = args.index('-all')
            common_args = args[all_i+1:]
            args = args[:all_i]

        unit_requests = []
        current_args = common_args.copy()
        nth_unit = 0
        args.append('&')
        for arg in args:
            if arg in separators:
                if not current_args:
                    continue
                unit_requests.append(current_args)
                current_args = common_args.copy()
                nth_unit += 1
                continue
            current_args.append(arg)
        if nth_unit > compare_limit:
            await self.bot.say('Cannot compare more than %d units at a time.' % compare_limit)
        if nth_unit > diff_limit and quiet_mode:
            await self.bot.say('Cannot show differences for more than %d units at a time.' % diff_limit)
            return
        max_tables = []
        curr_unit = 1
        should_save = False
        for request in unit_requests:
            take_base = False
            if 'lvl1' in request:
                take_base = True
                request.remove('lvl1')
            save, ustats = self.get_unit_stats(request, default_rarity=5, ctx=ctx)
            should_save = should_save or save
            if not isinstance(ustats, tuple):
                await self.bot.say('I had difficulty finding what you wanted for unit %d. ' % curr_unit + ustats)
                return
            unit, base_t, max_t = ustats
            if take_base:
                stats_t = base_t
            else:
                stats_t = max_t
            max_tables.append((shorten_hero_name(unit['Title']), stats_t))
            curr_unit += 1
        row_format = '|%-15.15s|%4s|%4s|%4s|%4s|%4s|%4s|\n'
        message = row_format % ('Unit', 'HP', 'ATK', 'SPD', 'DEF', 'RES', 'BST')
        unit_number = 1
        for unit in max_tables:
            table = array_to_table(unit[1])[0]
            message += row_format % (unit[0], table['HP'], table['ATK'], table['SPD'], table['DEF'], table['RES'], table['Total'])
            unit_number += 1
        raw_stats = [np.array(list(filter(lambda r:any(r), t))[0]) for t in [table[1] for table in max_tables]]
        messages = [message] if stats_mode else []
        if quiet_mode or nth_unit == 2:
            for i in range(0, len(max_tables)-1):
                nmessage = row_format % (max_tables[i][0][:13] + ' -', 'HP', 'ATK', 'SPD', 'DEF', 'RES', 'BST')
                for j in range(i+1, len(max_tables)):
                    difference = raw_stats[i] - raw_stats[j]
                    nmessage += row_format % ('%15.15s' % max_tables[j][0], str(difference[0]), str(difference[1]), str(difference[2]), str(difference[3]), str(difference[4]), str(difference.sum()))
                messages.append(nmessage)
        if analytics_mode:
            analytics_table = np.array(raw_stats).transpose()
            a_row_format = '|%7s|%5s %-31.31s|\n'
            amessage = a_row_format % ('Highest', 'Value', '(Character(s))')
            for i in range(0, len(stats)):
                characters = np.where(analytics_table[i]==analytics_table[i].max())[0]
                amessage += a_row_format % (stats[i], str(analytics_table[i].max()), '('+', '.join([u[0] for u in [max_tables[j] for j in characters]])+')')
            totals = analytics_table.sum(axis=0)
            amessage += a_row_format % ('BST', str(totals.max()), '('+', '.join([u[0] for u in [max_tables[j] for j in np.where(totals==totals.max())[0]]])+')')
            messages.append(amessage)
        curr_message = ''
        for message in messages:
            formatted_message = '```' + message + '```'
            if len(curr_message) + len(formatted_message) > 2000:
                await self.bot.say(curr_message)
                curr_message = ''
            curr_message += formatted_message
        if curr_message:
            await self.bot.say(curr_message)
        if should_save:
            self.cache.save()

    @bot.command(aliases=['list', 'List', 'Fehlist', 'FEHlist', 'FEHList'])
    async def fehlist(self, *args):
        """I will create a list of heroes to serve your needs.
Usage: fehlist|list [-f filters] [-s fields_to_sort_by] [-r (reverse the results)]
Filters reduce the list down to the heroes you want. You can filter by Colour (Red, Blue, Green, Colourless), Weapon (Sword, Lance, Axe, Bow, Dagger, Staff, Tome, Breath) or Movement Type (Infantry, Cavalry, Flying, Armored). You can also filter by a stat threshold such as (HP>30) or (DEF+RES>50).
Sorting fields let you choose how to sort the heroes. You can sort highest first in any stat (HP, ATK, SPD, DEF, RES, BST (Total)) or alphabetically by Name, Colour, Weapon or Movement Type. You can also sort by added stat totals such as (DEF+RES) or (ATK+SPD). The order you declare these will be the order of priority.
There are shorthands to make it easier:
Red, Blue, Green, Colourless = r, b, g, c
Sword, Lance, Axe, Bow, Dagger, Staff, Tome, Breath = sw, la, ax, bo, da, st, to, br
Infantry, Cavalry, Flying, Armored = in, ca, fl, ar
Name, Colour, Weapon, Movement Type = na, co, we, mov
Or you can just type out the full name.
Sorting by an added stat total is as simple as typing in all the stats you want to add with a + between them without spaces. Examples: atk+def+spd def+res
You can filter by a stat or an added stat total by typing the stat(s) as you would for sort and adding a comparison and number. Examples: hp>30 spd<20 def>=30 atk==35 atk=35 hp+spd>60
Example: !list -f red sword infantry -s attack hp
         is the same as
         !list -f r sw in -s atk hp
         and will produce a list of units that are Red, wield Swords and are Infantry sorted by Attack and then by HP."""
        self.cache.update()

        try:
            if args:
                if (len(args) > 1 and '-r' in args and '-f' not in args and '-s' not in args) or\
                    ('-r' not in args and '-f' not in args and '-s' not in args) or\
                    (args[0] not in ['-r', '-f', '-s']) or\
                    ('-r' in args and args[-1] != '-r' and args[args.index('-r')+1] not in ['-f', '-s']) or\
                    any('-' in arg and arg not in ['-r', '-f', '-s'] for arg in args):
                    await self.bot.say('Unfortunately I had trouble figuring out what you wanted. Are you sure you typed the command correctly?\n```Usage: fehlist|list [-f filters] [-s fields_to_sort_by] [-r]```')
                    return

            # set up argument parser
            parser = argparse.ArgumentParser(description='Process arguments for heroes list.')
            parser.add_argument('-f', nargs='*')
            parser.add_argument('-s', nargs='*')
            parser.add_argument('-r', action='store_const', const=False, default=True)
            args = vars(parser.parse_args(args=args))
            filters = {}
            if args['f']:
                filters = standardize(args, 'f')
                if filters is None:
                    await self.bot.say('Invalid filters or multiple filters for the same field were selected.')
                    return
            sort_keys = []
            if args['s']:
                sort_keys = standardize(args, 's')
                if sort_keys is None:
                    await self.bot.say('Invalid fields to sort by were selected.')
                    return
            try:
                heroes = get_heroes_list()
                self.cache.set_list(heroes)
            except urllib.error.HTTPError as err:
                if err.code >= 500:
                    if self.cache.list:
                        heroes = self.cache.list
                    else:
                        await self.bot.say("Unfortunately, it seems like I cannot access my sources at the moment. Please try again later.")
                        return
            except timeout:
                print('Timed out')
            except AttributeError:
                print('Source had an error')
            finally:
                if self.cache.list:
                    heroes = self.cache.list
            # convert from dict to list for easy manipulation
            heroes = [heroes[h] for h in heroes]
            for f in filters:
                if f != 'Threshold':
                    heroes = list(filter(lambda h:h[f] in filters[f], heroes))
                else:
                    for t in filters[f]:
                        heroes = list(filter(lambda h:t[0](list(itertools.accumulate([h[field] for field in t[1]]))[-1], t[2]), heroes))
            if not heroes:
                await self.bot.say('No results found for selected filters.')
                return
            num_results = len(heroes)
            sort_keys.append('Name')
            for key in reversed(sort_keys):
                heroes = sorted(heroes,
                                key=lambda h:
                                    list(
                                        itertools.accumulate([h[field] for field in key] if isinstance(key, tuple) else [h[key]]))[-1],
                                        reverse=not args['r'] if key in ['Name', 'Movement', 'Colour', 'Weapon'] else args['r']
                                        )
            sort_keys.pop()
            list_string = ', '.join([
                h['Name'] + (
                    (' ('+','.join([
                        str(
                            list(itertools.accumulate([h[field] for field in k] if isinstance(k, tuple) else [h[k]]))[-1]
                            ) for k in sort_keys if k != 'Name'
                        ])+')' if sort_keys else '')
                    if len(sort_keys) != 1 or sort_keys[0] != 'Name' else ''
                    ) for h in heroes
                ])
            while len(list_string) > 2000:
                list_string = ', '.join([
                    h['Name'] + (
                        (' ('+','.join([
                            str(
                                list(itertools.accumulate([h[field] for field in k] if isinstance(k, tuple) else [h[k]]))[-1]
                                ) for k in sort_keys if k != 'Name'
                            ])+')' if sort_keys else '')
                        if len(sort_keys) != 1 or sort_keys[0] != 'Name' else ''
                        ) for h in heroes
                    ])
                heroes = heroes[:-1]
            results_string = 'Results found: %d\nResults shown: %d' % (num_results, len(heroes))
            if num_results > 1 and num_results <= compare_limit:
                results_string += '\nIf you wish to compare these units in greater detail:\n`?compare %s -a`' % ' & '.join(h['Name'] for h in heroes)
            await self.bot.say(results_string)
            await self.bot.say(list_string)
        except timeout:
            await self.bot.say('Unfortunately, it seems like I cannot access my sources in a timely fashion at the moment. Please try again later.')

def setup(bot):
    bot.add_cog(MagikarpJump(bot))
    bot.add_cog(FireEmblemHeroes(bot))
