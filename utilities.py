import discord, random, urllib.request, urllib.parse, json
from discord.ext import commands as bot
from bs4 import BeautifulSoup as BSoup

feh_source = "https://feheroes.gamepedia.com/%s"
INVALID_HERO = 'no'

def get_page(url):
    print(url)
    response = urllib.request.urlopen(url)
    return json.load(response)


def true_page(arg):
    # extra cases for common aliases
    if arg.lower() == 'frobin':
        return 'Robin (F)'
    if arg.lower() == 'fcorrin':
        return 'Corrin (F)'
    if arg.lower() == 'mrobin':
        return 'Robin (M)'
    if arg.lower() == 'mcorrin':
        return 'Corrin (M)'
    if arg.lower() == 'babe':
        return 'Lukas'
    if arg.lower() == 'atiki':
        return 'Tiki (Adult)'
    if arg.lower() == 'ytiki':
        return 'Tiki (Young)'
    if arg.lower() == 'doot':
        return 'Delthea'
    if arg.lower() == 'thorp':
        return 'Tharja'
    if arg.lower() == 'gwendy':
        return 'Gwendolyn'
    if arg.lower() in ['boy', 'our boy']:
        return 'Roy (Brave Heroes)'

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
    print(table)
    stats = '`|' + '|'.join(['%8s' % key for key in table[0]]) + '|`'
    for set in table:
        stats += '\n`|' + '|'.join(['%8s' % set[key] for key in set]) + '|`'
    return stats


def calc_bst(stats_table):
    if len(stats_table) == 0:
        return None
    # get the 5* stats
    bst = 0
    for key in stats_table[-1]:
        if key == 'Rarity':
            continue
        if '-' in stats_table[-1][key] or '?' in stats_table[-1][key]:
            return None
        stat_arr = stats_table[-1][key].split('/')
        bst += int(stat_arr[1 if len(stat_arr) > 1 else 0])
    return bst


class Utilities:
    """I'll help you any way I can."""

    def __init__(self, bot):
        self.bot = bot

    @bot.command()
    async def lmr(self):
        """I will tell you which rod will net you the best Magikarp."""
        await self.bot.say(random.choice(['L', 'M', 'R']))

    @bot.command()
    async def feh(self, *, arg):
        """I will provide some information on a Fire Emblem Heroes topic."""
        arg = true_page(arg)
        if arg == INVALID_HERO:
            await self.bot.say("I'm afraid I couldn't find information on that.")
            return
        print(arg)
        message = discord.Embed(
            title=arg,
            url=feh_source % (urllib.parse.quote(arg)),
            color=0xe74c3c
        )
        categories = get_categories(arg)
        if 'Heroes' in categories:
            icon = get_icon(arg, "Icon_Portrait_")
            if not icon is None:
                message.set_thumbnail(url=icon)
            html = BSoup(get_text(arg), "lxml")
            stats = get_infobox(html)
            base_stats_table, max_stats_table = [extract_table(a)
                                                 for a in html.find_all("table", attrs={"class":"wikitable"})[1:3]]
            print(stats)
            rarity = ', '.join(a+'★' for a in stats['Rarities'] if a.isdigit())
            message.add_field(
                name="Rarities",
                value= rarity if rarity else 'N/A'
            )
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
            stats_table, learners_table = html.find_all("table", attrs={"class": "sortable"})
            stats = [a.get_text().strip() for a in stats_table.find_all("tr")[-1].find_all("td")] + \
                    [a.get_text().strip() for a in
                     stats_table.find_all("tr")[1].find_all("td")[(-2 if 'Passives' in categories else -1):]]
            stats = [a if a else 'Unknown' for a in stats]
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


def setup(bot):
    bot.add_cog(Utilities(bot))
