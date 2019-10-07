import dlwiki_parse
import discord
from discord.ext import commands as bot


class DragaliaLost:

    def __init__(self, bot):
        self.bot = bot

    @bot.command(pass_context=True, aliases=['dlsearch', 'DL', 'DLSearch'])
    async def dl(self, ctx, *, arg):
        """Search Dragalia Lost Gamepedia wiki. Displays detailed information for:
    Adventurers
    """
        if str(ctx.message.author) != 'monkeybard#3663':
            await self.bot.say("Command in construction.")
            return

        # resolve name
        arg = dlwiki_parse.resolve_name(arg)
        # identify category
        category = dlwiki_parse.get_category(arg)
        print(category)
        # use the right query
        data = dlwiki_parse.search(category, arg)
        print(data)
        # display that shit

        message = discord.Embed(
            title=data['Embed Info']['Title'],
            url=data['Embed Info']['URL'],
            color=data['Embed Info']['Colour']
        )
        if data['Embed Info']['Icon']:
            message.set_thumbnail(url=data['Embed Info']['Icon'])
        if data['Embed Info']['Description']:
            message.description = '*' + data['Embed Info']['Description'] + '*'

        for key in data:
            if key not in ['Embed Info']:
                message.add_field(
                    name=key,
                    value=data[key][0],
                    inline=data[key][1]
                )

        if 'Message' in data:
            await self.bot.say(data['Message'].replace('. ', '.\n'), embed=message)
        else:
            await self.bot.say(embed=message)


    @bot.command(pass_context=True, aliases=['dlq', 'DLQ', 'DLQuick'])
    async def dlquick(self, ctx, *, arg):
        """Search Dragalia Lost Gamepedia wiki. Displays detailed information for:
    Adventurers
    """
        if str(ctx.message.author) != 'monkeybard#3663':
            await self.bot.say("Command in construction.")
            return

        # resolve name
        arg = dlwiki_parse.resolve_name(arg)
        # identify category
        category = dlwiki_parse.get_category(arg)
        print(category)
        # use the right query
        data = dlwiki_parse.search(category, arg)
        print(data)
        # display that shit

        message = discord.Embed(
            title=data['Embed Info']['Title'],
            url=data['Embed Info']['URL'],
            color=data['Embed Info']['Colour']
        )
        if 'Icon' in data['Embed Info']:
            message.set_thumbnail(url=data['Embed Info']['Icon'])

        quick_fields = {
            'Adventurers': ['Element', 'Weapon Type', 'Total Max HP', 'Total Max Str', 'Co-Ability', 'Abilities'],
            'Dragons': ['Element', 'Favorite Gift', 'Level 100 HP', 'Lvl 100 Str', 'Abilities']
        }

        for key in (quick_fields[category] if category in quick_fields else data):
            if key not in ['Embed Info']:
                message.add_field(
                    name=key,
                    value=data[key][0] if key != 'Abilities' else
                        ', '.join([f'**{d}**' if 'Res +' in d else d for d in data[key][0].split(', ')]),
                    inline=data[key][1]
                )
        for key in data:
            if 'Skill' in key:
                message.add_field(
                    name=key,
                    value=data[key][0],
                    inline=data[key][1]
                )

        if 'Message' in data:
            await self.bot.say(data['Message'].replace('. ', '.\n'), embed=message)
        else:
            await self.bot.say(embed=message)


def setup(bot):
    bot.add_cog(DragaliaLost(bot))