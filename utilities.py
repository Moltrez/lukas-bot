import discord, asyncio, random, urllib.request, urllib3, json
from discord.ext import commands as bot
from bs4 import BeautifulSoup as BSoup

feh_source = "https://feheroes.gamepedia.com/%s"
INVALID_HERO = 'no'


def sanitize_url(url):
    return url.replace(' ', '%20').replace('(', '%28').replace(')', '%29').replace('+', '%2B').replace("'S", '%27s')


def get_page(url):
    url = sanitize_url(url)
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

    # convert arg to title case, in the case of (A), (F), (BB), etc. convert stuff in parentheses to upper
    arg = arg.split('(')
    arg[0] = arg[0].title()
    if len(arg) > 1:
        if len(arg[1]) <= 3:
            arg[1] = arg[1].upper()
        else:
            arg[1] = arg[1].title()
    arg = '('.join(arg)

    redirect = feh_source % "api.php?action=query&titles=%s&redirects=true&format=json" % arg
    info = get_page(redirect)
    if '-1' in info['query']['pages']:
        return INVALID_HERO
    if 'redirects' in info['query']:
        return info['query']['redirects'][0]['to']
    return arg.replace("'S", "'s")


def get_icon(arg, prefix=""):
    url = feh_source %\
          "api.php?action=query&titles=File:%s%s.png&prop=imageinfo&iiprop=url&format=json" %\
          (prefix, arg.replace('+', "_Plus"))
    info = get_page(url)
    return info['query']['pages'][next(iter(info['query']['pages']))]['imageinfo'][0]['url']


def get_category(arg):
    url = feh_source % "api.php?action=query&titles=%s&prop=categories&format=json" % arg
    info = get_page(url)
    categories = info['query']['pages'][next(iter(info['query']['pages']))]['categories']
    if len(categories) > 1:
        return categories[1]['title']
    else:
        return categories[0]['title']


def get_text(arg):
    url = feh_source % "api.php?action=parse&page=%s&format=json" % arg
    info = get_page(url)
    return info['parse']['text']['*']


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
        category = get_category(arg)
        message = discord.Embed(
            title=arg,
            url=sanitize_url(feh_source % arg)
        )
        if category == 'Category:Heroes':
            message.set_thumbnail(url=get_icon(arg, "Icon_Portrait_"))
        elif category == 'Category:Weapons':
            message.set_thumbnail(url=get_icon(arg, "Weapon_"))
            html = BSoup(get_text(arg), "html.parser")
            table = html.find("div", attrs={"class":"hero-infobox"}).find("table")
            stats = { a.find("th").get_text().strip() if not a.find("th") is None else None : a.find(
                "td").get_text().strip() if not a.find("td") is None else None for a in table.find_all("tr") }
            print(stats)
            message.add_field(
                name = "Might",
                value = stats['Might'],
                inline=True
            )
            message.add_field(
                name = "Range",
                value = stats['Range'],
                inline=True
            )
            message.add_field(
                name = "SP Cost",
                value = stats['SP Cost'],
                inline=True
            )
            message.add_field(
                name = "Exclusive?",
                value = stats['Exclusive?'],
                inline=True
            )
            if 'Special Effect' in stats:
                message.add_field(
                    name = "Special Effect",
                    value = stats[None],
                    inline=True
                )
            learners_table = html.find("table", attrs={"class":"sortable"})
            learners = [a.find("td").find_all("a")[1].get_text() for a in learners_table.find_all("tr")]
            message.add_field(
                name = "Heroes with " + arg,
                value = ', '.join(learners),
                inline=False
            )
        elif category == 'Category:Passives' or category == 'Category:Assists' or category == 'Category:Specials':
            html = BSoup(get_text(arg), "html.parser")
            stats_table, learners_table = html.find_all("table", attrs={"class": "sortable"})
            stats = [a.get_text().strip() for a in stats_table.find_all("tr")[-1].find_all("td")] + \
                    [a.get_text().strip() for a in
                     stats_table.find_all("tr")[1].find_all("td")[(-2 if category == 'Category:Passives' else -1):]]
            print(stats)
            if category == 'Category:Passives':
                message.set_thumbnail(url=get_icon(stats[1]))
                message.add_field(
                    name="Effect",
                    value=stats[2],
                    inline=False
                )
                message.add_field(
                    name="SP Cost",
                    value=stats[3],
                    inline=True
                )
                message.add_field(
                    name="Slot",
                    value=stats[-1],
                    inline=True
                )
                message.add_field(
                    name="Inherit Restrictions",
                    value=stats[-2],
                    inline=False
                )
            learners = [b[0].find_all("a")[1].get_text() + (" (" + b[-1].get_text() + "\*)"
                                                            if category == 'Category:Passives' else "")
                        for b in [a.find_all("td")
                        for a in learners_table.find_all("tr")[1:]]]
            message.add_field(
                name = "Heroes with " + arg,
                value = ', '.join(learners),
                inline=False
            )
        await self.bot.say(embed=message)


def setup(bot):
    bot.add_cog(Utilities(bot))