import discord, random, argparse, os.path, itertools
from discord.ext import commands as bot
from feh_alias import *
from fehwiki_parse import *

class MagikarpJump:
    """The game we don't play anymore."""

    def __init__(self, bot):
        self.bot = bot

    @bot.command(aliases=['Lmr'])
    async def lmr(self):
        """I will tell you which rod will net you the best Magikarp."""
        await self.bot.say(random.choice(['L', 'M', 'R']))

class FireEmblemHeroes:
    """The game that we do still play a lot."""

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
        original_arg = arg
        passive_level = 3
        if str(ctx.message.author) in sons and arg.lower() in ['son', 'my son']:
            arg = sons[str(ctx.message.author)]
        elif str(ctx.message.author) in waifus and arg.lower() in ['waifu', 'my waifu']:
            arg = waifus[str(ctx.message.author)]
        else:
            if arg[-1] in ['1','2','3']:
                passive_level = int(arg[-1])
                arg = arg[:-1].strip()
            arg = find_name(arg)
        if arg == INVALID_HERO:
            if original_arg.lower() in ['son', 'my son', 'waifu', 'my waifu']:
                await self.bot.say("I was not aware you had one. If you want me to associate you with one, please contact monkeybard.")
            else:
                await self.bot.say("I'm afraid I couldn't find information on %s." % original_arg)
            return
        print(arg)
        message = discord.Embed(
            title=arg,
            url=feh_source % (urllib.parse.quote(arg)),
            color=0x222222
        )
        categories = get_categories(arg)
        if 'Heroes' in categories:
            html = get_page_text(arg)
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
            bst = get_bst(max_stats_table)
            if not bst is None:
                message.add_field(
                    name="BST",
                    value=str(bst)
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
                inline=True
            )
            message.add_field(
                name="Max Level Stats",
                value=format_stats_table(max_stats_table),
                inline=True
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
            html = get_page_text(arg)
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
            html = get_page_text(arg)
            stats_table = html.find("table", attrs={"class": "sortable"})
            stats = [a.get_text().strip() for a in stats_table.find_all("tr")[-1 if len(stats_table.find_all("tr")) < (passive_level+1) else passive_level].find_all("td")] + \
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
                    learners = [b[0].find_all("a")[1].get_text() + " (" + b[-1].get_text()[-1] + "★)"
                                for b in
                                [a.find_all("td") for a in learners_table.find_all("tr")[1:]]]
                else:
                    learners = [a['Hero'] for a in extract_table(learners_table)]
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
        if user in flaunt:
            request = urllib.request.Request(flaunt[user] + '?width=384&height=683', headers={'User-Agent': 'Mozilla/5.0'})
            response = urllib.request.urlopen(request)
            f = response.read()
            f = io.BytesIO(f)
            f.name = os.path.basename(flaunt[user])
            await self.bot.upload(f)
        else:
            await self.bot.say("I'm afraid you have nothing to flaunt.")

    @bot.command(aliases=['list', 'List', 'Fehlist'])
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
            if f != 'Threshold':
                heroes = list(filter(lambda h:h[f] in filters[f], heroes))
            else:
                for t in filters[f]:
                    heroes = list(filter(lambda h:t[0](list(itertools.accumulate([h[field] for field in t[1]]))[-1], t[2]), heroes))
        if not heroes:
            await self.bot.say('No results found for selected filters.')
            return
        for key in reversed(sort_keys):
            heroes = sorted(heroes,
                            key=lambda h:
                                list(
                                    itertools.accumulate([h[field] for field in key] if isinstance(key, tuple) else [h[key]]))[-1],
                                    reverse=not args['r'] if key in ['Name', 'Movement', 'Colour', 'Weapon'] else args['r']
                                    )
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
        message = list_string
        await self.bot.say(message)


def setup(bot):
    bot.add_cog(MagikarpJump(bot))
    bot.add_cog(FireEmblemHeroes(bot))
