import discord, random, urllib.request, urllib.parse, json, argparse, io, os.path
from discord.ext import commands as bot
from bs4 import BeautifulSoup as BSoup

from feh_alias import *

feh_source = "https://feheroes.gamepedia.com/%s"
INVALID_HERO = 'no'
GAUNTLET_URL = "https://support.fire-emblem-heroes.com/voting_gauntlet/current"


def get_page(url):
    print(url)
    request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    response = urllib.request.urlopen(request)
    return json.load(response)

def true_page(arg):
    # extra cases for common aliases
    if arg.lower() in aliases:
        return aliases[arg.lower()]

    # convert arg to title case, in the case of (A), (F), (BB), etc. convert stuff in parentheses to upper
    arg = arg.split('(')
    arg[0] = arg[0].title()
    if len(arg) > 1:
        if len(arg[1]) <= 3:
            arg[1] = arg[1].upper()
        else:
            arg[1] = arg[1].title()
    arg = '('.join(arg)
    arg = arg.replace("'S", "'s").replace(" And ", " and ").replace(" Or ", " or ").replace(" Of ", " of ").\
        replace('Hp ', 'HP ').replace('Atk ', 'Attack ').replace('Spd ', 'Speed ').replace('Def ', 'Defense ').replace('Res ', 'Resistance ').replace(' +', ' Plus').\
        replace('Hp+', 'HP Plus').replace('Atk+', 'Attack Plus').replace('Spd+', 'Speed Plus').replace('Def+', 'Defense Plus').replace('Res+', 'Resistance Plus')

    redirect = feh_source % "api.php?action=query&titles=%s&redirects=true&format=json" % (urllib.parse.quote(arg))
    info = get_page(redirect)
    if '-1' in info['query']['pages']:
        return INVALID_HERO
    if 'redirects' in info['query']:
        return info['query']['redirects'][0]['to']
    return arg


def get_heroes_list():
    html = BSoup(get_text('Stats Table'), "lxml")
    table = html.find('table')
    heroes_list = [list_row_to_dict(row) for row in table.find_all('tr')]
    return heroes_list

def list_row_to_dict(row):
    data = row.find_all('td')
    colour, weapon = row['data-weapon-type'].split()
    hero = {
        'Name':data[1].text,
        'Colour':colour,
        'Weapon':weapon,
        'Movement':row['data-move-type'],
        'HP':int(data[4].text), 'ATK':int(data[5].text), 'SPD':int(data[6].text), 'DEF':int(data[7].text), 'RES':int(data[8].text), 'BST':int(data[9].text)
    }
    return hero

def get_icon(arg, prefix=""):
    url = feh_source %\
          "api.php?action=query&titles=File:%s%s.png&prop=imageinfo&iiprop=url&format=json" %\
          (prefix, urllib.parse.quote(arg.replace('+', '_Plus' + '_' if not prefix == "Weapon_" else '')))
    info = get_page(url)
    if '-1' in info['query']['pages']:
        return None
    return info['query']['pages'][next(iter(info['query']['pages']))]['imageinfo'][0]['url']


def get_categories(arg):
    url = feh_source % "api.php?action=query&titles=%s&prop=categories&format=json" % (urllib.parse.quote(arg))
    info = get_page(url)
    if 'categories' not in info['query']['pages'][next(iter(info['query']['pages']))]:
        return []
    categories = info['query']['pages'][next(iter(info['query']['pages']))]['categories']
    return [a['title'].lstrip('Category:') for a in categories]


def get_text(arg):
    url = feh_source % "api.php?action=parse&page=%s&format=json" % (urllib.parse.quote(arg))
    info = get_page(url)
    return info['parse']['text']['*']


def get_infobox(html):
    table = html.find("div", attrs={"class": "hero-infobox"}).find("table")
    return {a.find("th").get_text().strip() if not a.find("th") is None else None: a.find(
        "td").get_text().strip() if not a.find("td") is None else None for a in table.find_all("tr")}


def extract_table(table_html):
    table = []
    headings = [a.get_text() for a in table_html.find_all("th")]
    for learner in table_html.find_all("tr"):
        if len(learner.find_all("td")) == 0:
            continue
        data = [a.get_text() for a in learner.find_all("td")]
        table.append({headings[a]: data[a] for a in range(0, len(headings))})
    return table


def format_stats_table(table):
    if len(table) == 0:
        return None
    stats = '`|' + '|'.join(['%8s' % key if key != 'Rarity' else '★' for key in table[0]][:-1]) + '|`'
    for set in table:
        stats += '\n`|' + '|'.join(['%8s' % set[key] if key != 'Rarity' else set[key] for key in set][:-1]) + '|`'
    return stats


def calc_bst(stats_table):
    if len(stats_table) == 0:
        return None
    if 'Total' not in stats_table[-1]:
        return None
    return stats_table[-1]['Total']


def get_gauntlet_scores():
        newurl = urllib.request.urlopen(GAUNTLET_URL).geturl()
        toopen = urllib.request.Request(newurl, headers={'Accept-Language':'en-GB'})
        html = BSoup(urllib.request.urlopen(toopen).read(), "lxml")
        round = html.find_all('ul')[2]
        scores = [[m.find('div', attrs={'class':'tournaments-art-left'}), m.find('div', attrs={'class':'tournaments-art-right'})] for m in round.find_all('li')]
        scores = [[{'Name':s[0].p.text, 'Score':s[0].find_all('p')[-1].text, 'Status':'Same' if 'normal' in s[0]['class'][-1] else 'Weak'},
                    {'Name':s[1].p.text, 'Score':s[1].find_all('p')[-1].text, 'Status':'Same' if 'normal' in s[1]['class'][-1] else 'Weak'}] for s in scores]
        for s in scores:
            if s[0]['Status'] == 'Weak':
                s[1]['Status'] = 'Strong'
            elif s[1]['Status'] == 'Weak':
                s[0]['Status'] = 'Strong'
        return scores


def standardize(d, k):
    l = d[k]
    valid_filters = ['Red', 'Blue', 'Green', 'Neutral', 'Sword', 'Lance', 'Axe', 'Bow', 'Staff', 'Breath', 'Tome', 'Dagger', 'Infantry', 'Cavalry', 'Armored', 'Flying']
    valid_sorts = ['HP', 'ATK', 'SPD', 'DEF', 'RES', 'BST', 'Name', 'Colour', 'Weapon', 'Movement']
    for i in range(len(l)):
        l[i] = l[i].title()
        if l[i] == 'R':
            l[i] = 'Red'
        if l[i] == 'B':
            l[i] = 'Blue'
        if l[i] == 'G':
            l[i] = 'Green'
        if l[i] == 'C':
            l[i] = 'Colourless'
        if l[i] == 'Sw':
            l[i] = 'Sword'
        if l[i] == 'La':
            l[i] = 'Lance'
        if l[i] == 'Ax':
            l[i] = 'Axe'
        if l[i] == 'Bo':
            l[i] = 'Bow'
        if l[i] == 'St':
            l[i] = 'Staff'
        if l[i] == 'Br':
            l[i] = 'Breath'
        if l[i] == 'Da':
            l[i] = 'Dagger'
        if l[i] == 'To':
            l[i] = 'Tome'
        if l[i] == 'In':
            l[i] = 'Infantry'
        if l[i] in ['Ca', 'Mo', 'Mounted']:
            l[i] = 'Cavalry'
        if l[i] in ['Ar', 'Armoured']:
            l[i] = 'Armored'
        if l[i] == 'Fl':
            l[i] = 'Flying'
        if l[i] in ['Hp', 'Atk', 'Spd', 'Def', 'Res', 'Bst']:
            l[i] = l[i].upper()
        if l[i] == 'Attack':
            l[i] = 'ATK'
        if l[i] == 'Speed':
            l[i] = 'SPD'
        if l[i] == 'Defense':
            l[i] = 'DEF'
        if l[i] == 'Resistance':
            l[i] = 'RES'
        if l[i] in ['Total', 'Stats', 'Stat']:
            l[i] = 'BST'
        if l[i] == 'Na':
            l[i] = 'Name'
        if l[i] == 'Co':
            l[i] = 'Colour'
        if l[i] == 'We':
            l[i] = 'Weapon'
        if l[i] == 'Mov':
            l[i] = 'Movement'
    print(l)
    if k == 'f': 
        if bool(set(l) - set(valid_filters)):
            return None
        else:
            colours = list(filter(lambda x:x in ['Red', 'Blue', 'Green', 'Colourless'], l))
            weapons = list(filter(lambda x:x in ['Sword', 'Lance', 'Axe', 'Bow', 'Staff', 'Dagger', 'Breath', 'Tome'], l))
            move = list(filter(lambda x:x in ['Infantry', 'Cavalry', 'Armored', 'Flying'], l))
            filters = {}
            if colours:
                filters['Colour'] = colours
            if weapons:
                filters['Weapon'] = weapons
            if move:
                filters['Movement'] = move
            return filters
    if k == 's' and bool(set(l) - set(valid_sorts)):
        return None
    return l

class MagikarpJump:
    """The game we don't play anymore."""

    def __init__(self, bot):
        self.bot = bot

    @bot.command(aliases=['Lmr'])
    async def lmr(self):
        """I will tell you which rod will net you the best Magikarp."""
        await self.bot.say(random.choice(['L', 'M', 'R']))
        
class FireEmblemHeroes:
    """The game we don't play anymore."""

    def __init__(self, bot):
        self.bot = bot
        
    @bot.command(aliases=['Gauntlet'])
    async def gauntlet(self):
        """I will tell you the current Voting Gauntlet score."""
        scores = get_gauntlet_scores()
        longest = max(scores, key=lambda s: len(s[0]['Score']) + len(s[0]['Status']) + 3)
        longest = len(longest[0]['Score']) + len(longest[0]['Status']) + 3
        message = '```'
        for s in scores:
            message += """{:>{width}} vs {}
{:>{width}}    {}
""".format(s[0]['Name'], s[1]['Name'], (s[0]['Score'] + ' (' + s[0]['Status'] + ')'), ('(' + s[1]['Status'] + ') ' +  s[1]['Score']), width = longest)
        message += '```'
        await self.bot.say(message)
        
    @bot.command(pass_context=True, aliases=['Feh'])
    async def feh(self, ctx, *, arg):
        """I will provide some information on any Fire Emblem Heroes topic."""
        if str(ctx.message.author) in sons and arg.lower() in ['son', 'my son']:
            arg = sons[str(ctx.message.author)]
        else:
            arg = true_page(arg)
        if arg == INVALID_HERO:
            await self.bot.say("I'm afraid I couldn't find information on that.")
            return
        print(arg)
        message = discord.Embed(
            title=arg,
            url=feh_source % (urllib.parse.quote(arg)),
            color=0x222222
        )
        categories = get_categories(arg)
        if 'Heroes' in categories:
            html = BSoup(get_text(arg), "lxml")
            stats = get_infobox(html)
            base_stats_table, max_stats_table = [extract_table(a)
                                                 for a in html.find_all("table", attrs={"class":"wikitable"})[1:3]]
            colour = 0x54676E # colorless
            if 'Red' in stats['Weapon Type']:
                colour = 0xCC2844
            if 'Blue' in stats['Weapon Type']:
                colour = 0x2A63E6
            if 'Green' in stats['Weapon Type']:
                colour = 0x139F13
            message = discord.Embed(
                title=arg,
                url=feh_source % (urllib.parse.quote(arg)),
                color=colour
            )
            icon = get_icon(arg, "Icon_Portrait_")
            if not icon is None:
                message.set_thumbnail(url=icon)
            rarity = ', '.join(a+'★' for a in stats['Rarities'] if a.isdigit())
            message.add_field(
                name="Rarities",
                value= rarity if rarity else 'N/A'
            )
            bst = calc_bst(max_stats_table)
            if not bst is None:
                message.add_field(
                    name="BST",
                    value=calc_bst(max_stats_table)
                )
            message.add_field(
                name="Weapon Type",
                value=stats['Weapon Type']
            )
            message.add_field(
                name="Move Type",
                value=stats['Move Type']
            )
            message.add_field(
                name="Base Stats",
                value=format_stats_table(base_stats_table),
                inline=False
            )
            message.add_field(
                name="Max Level Stats",
                value=format_stats_table(max_stats_table),
                inline=False
            )
            skill_tables = html.find_all("table", attrs={"class":"skills-table"})
            skills = ''
            for table in skill_tables:
                headings = [a.get_text().strip() for a in table.find_all("th")]
                if 'Might' in headings:
                    # weapons
                    skills += '**Weapons:** '
                elif 'Range' in headings:
                    # assists
                    skills += '**Assists:** '
                elif 'Cooldown' in headings:
                    # specials
                    skills += '**Specials:** '
                for row in table.find_all("tr")[(-2 if 'Might' in headings else None):]:
                    slot = row.find("td", attrs={"rowspan":True})
                    if not slot is None:
                        skills = skills.rstrip(', ') + '\n**' + slot.get_text() + '**: '
                    skills += row.find("td").get_text().strip() + ', '
                skills = skills.rstrip(', ') + '\n'
            message.add_field(
                name="Learnable Skills",
                value=skills,
                inline=False
            )
        elif 'Weapons' in categories:
            icon = get_icon(arg, "Weapon_")
            if not icon is None:
                message.set_thumbnail(url=icon)
            html = BSoup(get_text(arg), "lxml")
            stats = get_infobox(html)
            print(stats)
            message.add_field(
                name="Might",
                value=stats['Might']
            )
            message.add_field(
                name="Range",
                value=stats['Range']
            )
            message.add_field(
                name="SP Cost",
                value=stats['SP Cost']
            )
            message.add_field(
                name="Exclusive?",
                value=stats['Exclusive?']
            )
            if 'Special Effect' in stats:
                message.add_field(
                    name="Special Effect",
                    value=stats[None],
                    inline=False
                )
            learners_table = html.find("table", attrs={"class":"sortable"})
            learners = [a.find("td").find_all("a")[1].get_text() for a in learners_table.find_all("tr")]
            print(learners)
            message.add_field(
                name="Heroes with " + arg,
                value=', '.join(learners),
                inline=False
            )
        elif 'Passives' in categories or 'Specials' in categories or 'Assists' in categories:
            html = BSoup(get_text(arg), "lxml")
            stats_table = html.find("table", attrs={"class": "sortable"})
            stats = [a.get_text().strip() for a in stats_table.find_all("tr")[-1].find_all("td")] + \
                    [a.get_text().strip() for a in
                     stats_table.find_all("tr")[1].find_all("td")[(-2 if 'Passives' in categories else -1):]]
            stats = [a if a else 'N/A' for a in stats]
            message.add_field(
                name="Effect",
                value=stats[2],
                inline=False
            )
            if 'Passives' in categories:
                icon = get_icon(stats[1])
                if not icon is None:
                    message.set_thumbnail(url=icon)
                message.add_field(
                    name="Slot",
                    value=stats[-1]
                )
            elif 'Specials' in categories:
                message.add_field(
                    name="Cooldown",
                    value=stats[1]
                )
            elif 'Assists' in categories:
                message.add_field(
                    name="Range",
                    value=stats[1]
                )
            message.add_field(
                name="SP Cost",
                value=stats[3]
            )
            message.add_field(
                name="Inherit Restrictions",
                value=stats[-2]
            )
            if 'Seal Exclusive Skills' not in categories:
                learners_table = html.find_all("table", attrs={"class": "sortable"})[-1]
                learners = []
                if 'Passives' in categories:
                    learners = [b[0].find_all("a")[1].get_text() + " (" + b[-1].get_text() + "★)"
                                for b in
                                [a.find_all("td") for a in learners_table.find_all("tr")[1:]]]
                else:
                    learners = [a['Name'] for a in extract_table(learners_table)]
                message.add_field(
                    name="Heroes with " + arg,
                    value=', '.join(learners),
                    inline=False
                )
        await self.bot.say(embed=message)
    
    @bot.command(pass_context=True, aliases=['Flaunt'])
    async def flaunt(self, ctx):
        """Use this command to show off your prized units.
If you want to add a flaunt please send a screenshot of your unit to monkeybard."""
        user = str(ctx.message.author)
        message = "I'm afraid you have nothing to flaunt."
        if user in flaunt:
            request = urllib.request.Request(flaunt[user], headers={'User-Agent': 'Mozilla/5.0'})
            response = urllib.request.urlopen(request)
            f = response.read()
            f = io.BytesIO(f)
            f.name = os.path.basename(flaunt[user])
        await self.bot.upload(f)
    
    @bot.command(aliases=['list', 'List', 'Fehlist'])
    async def fehlist(self, *args):
        """I will create a list of heroes to serve your needs.
Usage: fehlist|list [-f filters] [-s fields_to_sort_by] [-r (reverse the results)]
Filters reduce the list down to the heroes you want. You can filter by Colour (Red, Blue, Green, Colourless), Weapon (Sword, Lance, Axe, Bow, Dagger, Staff, Tome, Breath) or Movement Type (Infantry, Cavalry, Flying, Armored).
Sorting fields let you choose how to sort the heroes. You can sort highest first in any stat (HP, ATK, SPD, DEF, RES, BST (Total)) or alphabetically by Name, Colour, Weapon or Movement Type. The order you declare these will be the order of priority.
There are shorthands to make it easier:
Red, Blue, Green, Colourless = r, b, g, c
Sword, Lance, Axe, Bow, Dagger, Staff, Tome, Breath = sw, la, ax, bo, da, st, to, br
Infantry, Cavalry, Flying, Armored = in, ca, fl, ar
Name, Colour, Weapon, Movement Type = na, co, we, mov
Or you can just type out the full name.
Example: !list -f red sword infantry -s attack hp
         is the same as
         !list -f r sw in -s atk hp
         and will produce a list of units that are Red, wield Swords and are Infantry sorted by Attack and then by HP.
        """
        if args:
            if (len(args) > 1 and '-r' in args and '-f' not in args and '-s' not in args) or ('-r' not in args and '-f' not in args and '-s' not in args) or (args[0] not in ['-r', '-f', '-s']):
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
        heroes = get_heroes_list()
        for f in filters:
            heroes = list(filter(lambda h:h[f] in filters[f], heroes))
        if not heroes:
            await self.bot.say('No results found for selected filters.')
            return
        for key in reversed(sort_keys):
            heroes = sorted(heroes, key=lambda h:h[key], reverse=not args['r'] if key in ['Name', 'Movement', 'Colour', 'Weapon'] else args['r'])
        list_string = ', '.join([h['Name'] + (' ('+','.join([str(h[k]) for k in sort_keys if k != 'Name'])+')' if sort_keys else '') for h in heroes])
        n = 0
        while len(list_string) > 2000:
            list_string = ', '.join([h['Name'] + (' ('+','.join([str(h[k]) for k in sort_keys if k != 'Name'])+')' if sort_keys else '') for h in heroes])
            if n == 0:
                heroes = heroes[:100]
                n += 5
            else:
                n += 5
        message = list_string
        await self.bot.say(message)


def setup(bot):
    bot.add_cog(MagikarpJump(bot))
    bot.add_cog(FireEmblemHeroes(bot))