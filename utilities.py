import discord, asyncio, random, urllib.request, urllib3, json
from discord.ext import commands as bot

feh_source = "https://feheroes.gamepedia.com/%s"


def get_icon(arg):
    url = feh_source % "api.php?action=query&titles=File:Icon_Portrait_%s.png&prop=imageinfo&iiprop=url&format=json" % arg
    print(url)
    response = urllib.request.urlopen(url)
    info = json.load(response)
    print(info)
    return info['query']['pages'][next(iter(info['query']['pages']))]['imageinfo'][0]['url']


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
        arg = arg.title()
        arg = arg.replace(' ', '%20')
        message = discord.Embed(
            title=arg.replace('%20', ' '),
            url=feh_source % arg,
        )
        message.set_thumbnail(url=get_icon(arg))
        message.add_field(name="Test", value="Testing", inline=False)
        await self.bot.say(embed=message)


def setup(bot):
    bot.add_cog(Utilities(bot))