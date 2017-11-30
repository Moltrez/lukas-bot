import urllib.request, urllib.parse, json, io, operator
from socket import timeout
from bs4 import BeautifulSoup as BSoup
from feh_alias import *
from feh_personal import *

feh_source = "https://feheroes.gamepedia.com/%s"
INVALID_HERO = 'no'
GAUNTLET_URL = "https://support.fire-emblem-heroes.com/voting_gauntlet/current"

page_cache = {}
weapon_colours = {'Red':0xCC2844, 'Blue':0x2A63E6, 'Green':0x139F13, 'Colourless':0x54676E, 'Null':0x222222}
passive_colours = {1:0xcd914c, 2:0xa8b0b0, 3:0xd8b956}

def get_data(arg, passive_level=3, cache=None, save=True):
    categories, html = get_page_html(arg)
    if html is None:
        return None, None
    data = {}
    data['Embed Info'] = {'Title':arg, 'Icon':None}
    if 'Heroes' in categories:
        stats = get_infobox(html)
        base_stats_table, max_stats_table = get_heroes_stats_tables(html)
        colour = weapon_colours['Colourless']
        if 'Red' in stats['Weapon Type']:
            colour = weapon_colours['Red']
        if 'Blue' in stats['Weapon Type']:
            colour = weapon_colours['Blue']
        if 'Green' in stats['Weapon Type']:
            colour = weapon_colours['Green']
        data['Embed Info']['Colour'] = colour
        data['Embed Info']['URL'] = feh_source % (urllib.parse.quote(arg))
        icon = get_icon(arg, "Icon_Portrait_")
        if not icon is None:
            data['Embed Info']['Icon'] = icon
        rarity = '-'.join(a+'★' for a in stats['Rarities'] if a.isdigit())
        data['0Rarities'] = (rarity if rarity else 'N/A'), True
        data['1BST'] = get_bst(max_stats_table), True
        data['2Weapon Type'] = stats['Weapon Type'], True
        data['3Move Type'] = stats['Move Type'], True
        data['4Base Stats'] = base_stats_table, False
        data['5Max Level Stats'] = max_stats_table, False
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
            last_learned = None
            for row in table.find_all("tr")[(-2 if 'Might' in headings else None):]:
                slot = row.find("td", attrs={"rowspan":True}) # only passives have a rowspan data column
                if not slot is None:
                    skills = skills.rstrip(', ')
                    if not last_learned is None:
                        skills += last_learned
                    skills += '\n**' + slot.get_text() + '**: '
                skills += row.find("td").get_text().strip()
                if 'Type': # if we're in passives, get learned levels
                     last_learned = ' (%s★)' % row.find_all("td")[-2 if not slot is None else -1].get_text().strip()
                skills += ', '
            skills = skills.rstrip(', ') + last_learned + '\n'
        data['6Learnable Skills'] = skills, False
    elif 'Weapons' in categories:
        colour = weapon_colours['Null'] # for dragonstones, which are any colour
        if any(i in ['Swords', 'Red Tomes'] for i in categories):
            colour = weapon_colours['Red']
        elif any(i in ['Lances', 'Blue Tomes'] for i in categories):
            colour = weapon_colours['Blue']
        elif any(i in ['Axes', 'Green Tomes'] for i in categories):
            colour = weapon_colours['Green']
        elif any(i in ['Staves', 'Daggers', 'Bows'] for i in categories):
            colour = weapon_colours['Colourless']
        data['Embed Info']['Colour'] = colour
        data['Embed Info']['URL'] = feh_source % (urllib.parse.quote(arg))
        icon = get_icon(arg, "Weapon_")
        if not icon is None:
            data['Embed Info']['Icon'] = icon
        stats = get_infobox(html)
        data['0Might'] = stats['Might'], True
        data['1Range'] = stats['Range'], True
        data['2SP Cost'] = stats['SP Cost'], False
        data['3Exclusive?'] = stats['Exclusive?'], True
        if 'Special Effect' in stats:
            data['5Special Effect'] = stats[None], False
        learners_table = html.find("table", attrs={"class":"sortable"})
        learners = [a.find("td").find_all("a")[1].get_text() for a in learners_table.find_all("tr")]
        if learners:
            data['6Heroes with ' + arg] = ', '.join(learners), False
        refinery_table = html.find("table", attrs={"class":"wikitable default"})
        refinery_table = extract_table(refinery_table, True)
        if refinery_table:
            if 'Image' in refinery_table[0]:
                cost = refinery_table[0]['Cost'].split('|')
                cost_materials = cost[1:]
                cost = cost[0].split()
                cost[0] += ' SP'
                cost[1] = cost[1].strip().lstrip('SP') + ' ' + cost_materials[0].strip() + 's'
                cost[2] = cost[2].strip() + ' ' + cost_materials[1].strip() + 's'
                cost = ', '.join(cost)
                data['Evolution'] = refinery_table[0]['Name'].split('|')[0], False
                data['Refinery Cost'] = cost
            elif 'Type' in refinery_table[0]:
                data['Refine'] = []
                for r in refinery_table:
                    t = r['Type'].split('|')[1].rstrip(' W')
                    s = r['Stats'].split('|')[0]
                    e = r['Effect'].split('|')[0]
                    cost = r['Cost'].split('|')
                    cost_materials = cost[1:]
                    cost = cost[0].split(', ')
                    cost[1] = cost[1].strip() + ' ' + cost_materials[0].strip() + 's'
                    cost[2] = cost[2].strip() + ' ' + cost_materials[1].strip() + 's'
                    cost = ', '.join(cost)
                    data['Refine'].append({'Type':t, 'Stats':s, 'Effect':e})
                    data['Refinery Cost'] = cost
    elif 'Passives' in categories or 'Specials' in categories or 'Assists' in categories:
        stats_table = html.find("table", attrs={"class": "sortable"})
        # get the data from the appropriate row dictated by passive_level (if it exists)
        # append the inherit restriction (and slot)
        stats = [a.get_text().strip() for a in stats_table.find_all("tr")[-1 if len(stats_table.find_all("tr")) < (passive_level+1) else passive_level].find_all("td")] + \
                [a.get_text().strip() for a in
                 stats_table.find_all("tr")[1].find_all("td")[(-2 if 'Passives' in categories else -1):]]
        stats = [a if a else 'N/A' for a in stats]
        data['Embed Info']['Colour'] = 0xe8e1c9
        if 'Specials' in categories:
            data['Embed Info']['Colour'] = 0xf499fe
        elif 'Assists' in categories:
            data['Embed Info']['Colour'] = 0x1fe2c3

        skill_name = stats[1 if 'Passives' in categories else 0]

        learners = None
        # use learners table to figure out seal colour
        if 'Seal Exclusive Skills' not in categories:
            learners_table = html.find_all("table", attrs={"class": "sortable"})[-1]
            if learners_table != stats_table:
                skill_chain_position, learners = get_learners(learners_table, categories, skill_name)
                if 'Passives' in categories and skill_name[-1] in ['1', '2', '3'] and skill_chain_position > 0:
                    data['Embed Info']['Colour'] = passive_colours[skill_chain_position]
        else:
            if skill_name[-1] in ['1', '2', '3']:
                data['Embed Info']['Colour'] = passive_colours[int(skill_name[-1])]
        if skill_name[-1] not in ['1', '2', '3']:
            title = arg
        else:
            title = arg + ' ' + skill_name[-1]
        data['Embed Info']['Title'] = title
        data['Embed Info']['URL'] = feh_source % (urllib.parse.quote(arg))

        if 'Passives' in categories:
            icon = get_icon(stats[1])
            if not icon is None:
                data['Embed Info']['Icon'] = icon
            slot = stats_table.th.text[-2]
            data['0Slot'] = (slot + ('/S' if 'Sacred Seals' in categories and slot != 'S' else '')), True
            data['1SP Cost'] = stats[0].lstrip('30px'), True
        else:
            if 'Specials' in categories:
                data['0Cooldown'] = stats[1], True
            elif 'Assists' in categories:
                data['0Range'] = stats[1], True

            data['1SP Cost'] = stats[3], True
        data['2Effect'] = stats[2], False

        if 'Passives' in categories:
            inherit_r = ', '.join(map(lambda r:r.text, html.ul.find_all('li')))
        else:
            inherit_r = 'Only, '.join(stats[-2].split('Only'))[:(-2 if 'Only' in stats[-2] else None)]
        data['3Inherit Restrictions'] = inherit_r, True
        if learners:
            if 'Sacred Seals' in categories:
                learners = 'Available as Sacred Seal\n' + learners
            data['4Heroes with ' + arg] = learners, False
    else:
        data['Embed Info']['URL'] = feh_source % (urllib.parse.quote(arg))
        data['Embed Info']['Colour'] = weapon_colours['Null']
    cache.add_data(data, categories, save=save)
    return categories, data

def get_page(url, prop=''):
    print(url)
    query_url = url+('&prop='+prop if prop else '')+'&format=json'
    request = urllib.request.Request(query_url, headers={'User-Agent': 'Mozilla/5.0'})
    response = urllib.request.urlopen(request, timeout=5)
    print('Loading JSON...')
    info = json.load(response)
    if 'error' in info:
        return None
    return info


def find_name(arg, cache, sender = None):
    if sender:
        if sender in cache.sons and arg.lower() in ['son', 'my son']:
            return cache.sons[sender]
        elif sender in cache.waifus and arg.lower() in ['waifu', 'my waifu']:
            return cache.waifus[sender]
    if arg.lower() in ['son', 'my son', 'waifu', 'my waifu']:
        return INVALID_HERO
    # check cached aliases
    if arg.lower() in cache.aliases:
        return cache.aliases[arg.lower()]

    arg = arg.title().replace('Hp+', 'HP Plus').replace('Atk+', 'Attack Plus').replace('Spd+', 'Speed Plus').replace('Def+', 'Defense Plus').replace('Res+', 'Resistance Plus').\
        replace('Hp+', 'HP Plus').replace('Attack+', 'Attack Plus').replace('Speed+', 'Speed Plus').replace('Defense+', 'Defense Plus').replace('Resistance+', 'Resistance Plus').replace(' +', ' Plus')

    redirect = feh_source % "api.php?action=opensearch&search=%s&redirects=resolve" % (urllib.parse.quote(arg))
    info = get_page(redirect)
    if not info[1] or not info[1][0]:
        return INVALID_HERO
    else:
        return info[1][0]
    return arg


def get_heroes_list():
    categories, html = get_page_html('Stats Table')
    table = html.find('table')
    heroes_list = [list_row_to_dict(row) for row in table.find_all('tr')]
    heroes_list = list(filter(lambda h:h['BST'] != 0, heroes_list))
    return heroes_list


def list_row_to_dict(row):
    data = row.find_all('td')
    colour, weapon = row['data-weapon-type'].split()
    hero = {
        'Name':data[1].text,
        'Colour':colour,
        'Weapon':weapon,
        'Movement':row['data-move-type'],
        'HP':int(data[4].text) if data[4].text.isdigit() else 0, 'ATK':int(data[5].text) if data[5].text.isdigit() else 0,
        'SPD':int(data[6].text) if data[6].text.isdigit() else 0, 'DEF':int(data[7].text) if data[7].text.isdigit() else 0,
        'RES':int(data[8].text) if data[8].text.isdigit() else 0, 'BST':int(data[9].text) if data[9].text.isdigit() else 0
    }
    return hero


def get_icon(arg, prefix=""):
    url = feh_source %\
          "api.php?action=query&titles=File:%s%s.png" %\
          (prefix, urllib.parse.quote(arg.replace('+', '_Plus' + '_' if not prefix == "Weapon_" else '_Plus')))
    info = get_page(url, 'imageinfo&iiprop=url')
    if '-1' in info['query']['pages']:
        return None
    else:
        icon = info['query']['pages'][next(iter(info['query']['pages']))]['imageinfo'][0]['url']
        return icon


def get_page_html(arg):
    url = feh_source % "api.php?action=parse&page=%s" % (urllib.parse.quote(arg))
    info = get_page(url, 'text|categories')
    if info:
        categories = [' '.join(k['*'].split('_')) for k in info['parse']['categories']]
        soup = BSoup(info['parse']['text']['*'], "lxml")
        return categories, soup
    else:
        return None, None


def get_infobox(html):
    table = html.find("div", attrs={"class": "hero-infobox"}).find("table")
    return {a.find("th").get_text().strip() if not a.find("th") is None else None: a.find(
        "td").get_text().strip() if not a.find("td") is None else None for a in table.find_all("tr")}


def get_heroes_stats_tables(html):
    tables = html.find_all("table", attrs={"class":"wikitable"})
    if len(tables) < 4:
        return [None, None]
    elif 'skills-table' in tables[1]['class']:
        return [None, None]
    else:
        tables = tables[1:3]
    return [extract_table(a) for a in tables]


def extract_table(table_html, get_image_url=False):
    table = []
    headings = [a.get_text().strip() for a in table_html.find_all("th")]
    for learner in table_html.find_all("tr"):
        if len(learner.find_all("td")) == 0:
            continue
        data = [
            a.get_text().strip() +
            ('|' + (('|'.join([b['alt'].strip().rstrip('.png') for b in a.find_all('img')])) if a.find_all('img')
            else (a.a['title'].lstrip('File:').rstrip('.png') if a.a else '')) + '|'
            if get_image_url else '')
            for a in learner.find_all("td")
        ]
        table.append({headings[a]: data[a] for a in range(0, len(headings))})
    return table


def format_stats_table(table):
    if len(table) == 0:
        return None
    ivs = {'HP':'', 'ATK':'', 'SPD':'', 'DEF':'', 'RES':'', 'Total':''}
    keys = ['Rarity', 'HP', 'ATK', 'SPD', 'DEF', 'RES', 'Total']
    rows = ''
    for set in table:
        rows += '\n`'
        for key in keys:
            if key == 'Rarity':
                rows += '|' + set[key] + '★|'
                continue
            if key == 'Total':
                continue
            stats = set[key].split('/')
            neutral = stats[0]
            format = '%4s'
            if len(stats) == 3:
                neutral = stats[1]
                if neutral.isdigit():
                    if int(stats[2]) - int(stats[1]) == 4:
                        ivs[key] = '+'
                    if int(stats[1]) - int(stats[0]) == 4:
                        if ivs[key] == '+':
                            ivs[key] = '±'
                        else:
                            ivs[key] = '-'
            rows += format % neutral + '|'
        rows += '`'
    header = '`|' + '|'.join([format % (ivs[key] + key) if key != 'Rarity' else ' ★' for key in keys][:-1]) + '|`'
    ret = header + rows
    if '+' in list(ivs.values()) or '-' in list(ivs.values()):
        ret += "\n\n_Neutral stats.\n+4 boons are indicated by +, -4 banes are indicated by -._"
    return ret


def get_bst(stats_table):
    if len(stats_table) == 0:
        return None
    if 'Total' not in stats_table[-1]:
        return None
    return stats_table[-1]['Total']


def get_learners(learners_table, categories, skill_name):
    learners = {i+1:[] for i in range(5)}
    # l_data is one row in a 2D array representing the learners table
    skill_chain_position = -1
    for l_data in [a.find_all("td") for a in learners_table.find_all("tr")[(1 if 'Passives' in categories else 0):]]:
        # append a name to the appropriate level
        for i in range(len(l_data)):
            text = l_data[i].get_text()
            if skill_name in text:
                skill_chain_position = i
                learned_level = int(text[-1])
                learners[learned_level].append(l_data[0].find_all("a")[1].get_text())
                break
    learners = '\n'.join(['%d★: %s' % (level, ', '.join(learners[level])) for level in learners if len(learners[level]) != 0])
    return skill_chain_position, learners

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
        l[i] = l[i].title().rstrip('s') if l[i].title() not in ['Colourless', 'Colorless', 'Res'] else l[i].title()
        if l[i] == ['R', 'Re']:
            l[i] = 'Red'
        if l[i] in ['B', 'Bl']:
            l[i] = 'Blue'
        if l[i] in ['G', 'Gr']:
            l[i] = 'Green'
        if l[i] in ['C', 'Colourless', 'Colorless', 'Ne', 'N']:
            l[i] = 'Neutral'
        if l[i] == 'Sw':
            l[i] = 'Sword'
        if l[i] == 'La':
            l[i] = 'Lance'
        if l[i] == 'Ax':
            l[i] = 'Axe'
        if l[i] == 'Bo':
            l[i] = 'Bow'
        if l[i] in ['St', 'Stave']:
            l[i] = 'Staff'
        if l[i] == 'Br':
            l[i] = 'Breath'
        if l[i] in ['Da', 'Knife', 'Knive', 'Kn']:
            l[i] = 'Dagger'
        if l[i] == 'To':
            l[i] = 'Tome'
        if l[i] == 'In':
            l[i] = 'Infantry'
        if l[i] in ['Ca', 'Mo', 'Mounted', 'Horse', 'Cav', 'Cavalier']:
            l[i] = 'Cavalry'
        if l[i] in ['Ar', 'Armoured', 'Knight', 'Armour', 'Armor']:
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
        if l[i] in ['Total', 'Stat']:
            l[i] = 'BST'
        if l[i] == 'Na':
            l[i] = 'Name'
        if l[i] == 'Co':
            l[i] = 'Colour'
        if l[i] == 'We':
            l[i] = 'Weapon'
        if l[i] == 'Mov':
            l[i] = 'Movement'
        if '>' in l[i] or '<' in l[i] or '=' in l[i]:
            op = None
            filt = None
            if '>' in l[i] and '>=' not in l[i]:
                # greater than
                filt = l[i].split('>')
                op = operator.gt
            if '>=' in l[i]:
                # greater than or equal
                filt = l[i].split('>=')
                op = operator.ge
            if '<' in l[i] and '<=' not in l[i]:
                # less than
                filt = l[i].split('<')
                op = operator.lt
            if '<=' in l[i]:
                # less than or equal
                filt = l[i].split('<=')
                op = operator.le
            if '=' in l[i] and '!=' not in l[i] and '>=' not in l[i] and '<=' not in l[i]:
                # equal
                filt = l[i].split('=')
                if len(filt) == 3:
                    del filt[1]
                op = operator.eq
            if '!=' in l[i]:
                # not equal
                filt = l[i].split('!=')
                op = operator.ne
            if filt is None or operator is None:
                return None
            if len(filt) != 2:
                return None
            elif filt[0]:
                field, number = filt
            else:
                j=0
                for j in range(1, len(filt[1])):
                    if not filt[1][:j].isdigit():
                        break
                    j += 1
                number = filt[1][:j-1]
                field = filt[1][j-1:]
            field = standardize({'s':field if isinstance(field, list) else [field]}, 's')
            if field:
                if isinstance(field[0], tuple):
                    field = field[0]
                elif field[0] not in ['HP', 'ATK', 'SPD', 'DEF', 'RES', 'BST']:
                    return None
            else:
                return None
            l[i] = (op, field, int(number))
        if '+' in l[i]:
            fields = None
            if ',' in l[i] and '+' not in l[i]:
                fields = l[i].split(',')
            if '+' in l[i] and ',' not in l[i]:
                fields = l[i].split('+')
            if not fields or '' in fields:
                return None
            fields = standardize({'s':fields if isinstance(fields, list) else [fields]}, 's')
            if fields:
                for f in fields:
                    if f not in ['HP', 'ATK', 'SPD', 'DEF', 'RES', 'BST']:
                        return None
            else:
                return None
            l[i] = tuple(fields)
    if k == 'f':
        if bool(set(filter(lambda x:not isinstance(x, tuple), l)) - set(valid_filters)):
            return None
        else:
            colours = list(filter(lambda x:x in ['Red', 'Blue', 'Green', 'Neutral'], l))
            weapons = list(filter(lambda x:x in ['Sword', 'Lance', 'Axe', 'Bow', 'Staff', 'Dagger', 'Breath', 'Tome'], l))
            move = list(filter(lambda x:x in ['Infantry', 'Cavalry', 'Armored', 'Flying'], l))
            thresh = list(filter(lambda x:isinstance(x, tuple), l))
            filters = {}
            if colours:
                filters['Colour'] = colours
            if weapons:
                filters['Weapon'] = weapons
            if move:
                filters['Movement'] = move
            if thresh:
                filters['Threshold'] = thresh
            return filters
    if k == 's' and bool(set(filter(lambda x:not isinstance(x, tuple), l)) - set(valid_sorts)):
        return None
    return l
