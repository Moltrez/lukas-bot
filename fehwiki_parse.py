import urllib.request, urllib.parse, json, io
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


def find_name(arg):
    # extra cases for common aliases
    if arg.lower() in aliases:
        return aliases[arg.lower()]

    arg = arg.title().replace('Hp', 'HP').replace('Atk', 'Attack').replace('Spd', 'Speed').replace(' Def', ' Defense').replace('Res', 'Resistance').\
        replace('Hp+', 'HP Plus').replace('Atk+', 'Attack Plus').replace('Spd+', 'Speed Plus').replace('Def+', 'Defense Plus').replace('Res+', 'Resistance Plus').\
        replace('Hp+', 'HP Plus').replace('Attack+', 'Attack Plus').replace('Speed+', 'Speed Plus').replace('Defense+', 'Defense Plus').replace('Resistance+', 'Resistance Plus').replace(' +', ' Plus')

    redirect = feh_source % "api.php?action=opensearch&search=%s&redirects=resolve&format=json" % (urllib.parse.quote(arg))
    info = get_page(redirect)
    if not info[1] or not info[1][0]:
        return INVALID_HERO
    else:
        return info[1][0]
    return arg


def get_heroes_list():
    html = get_page_text('Stats Table')
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


def get_page_text(arg):
    url = feh_source % "api.php?action=parse&page=%s&format=json" % (urllib.parse.quote(arg))
    info = get_page(url)
    return BSoup(info['parse']['text']['*'], "lxml")


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
    ivs = {'HP':'', 'ATK':'', 'SPD':'', 'DEF':'', 'RES':'', 'Total':''}
    rows = ''
    for set in table:
        rows += '\n`'
        for key in set:
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
    header = '`|' + '|'.join([format % (ivs[key] + key) if key != 'Rarity' else ' ★' for key in table[0]][:-1]) + '|`'
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
        skill_level = 5
        for i in range(len(l_data)):
            text = l_data[i].get_text()
            if skill_name in text:
                skill_chain_position = i
                skill_level = int(text[-1])
        learners[skill_level].append(l_data[0].find_all("a")[1].get_text())
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
        if l[i] in ['Ca', 'Mo', 'Mounted', 'Horse']:
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
            colours = list(filter(lambda x:x in ['Red', 'Blue', 'Green', 'Colourless'], l))
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
