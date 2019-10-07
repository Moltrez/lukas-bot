import urllib.request, urllib.parse
import itertools
import re
from bs4 import BeautifulSoup as BSoup
from fehwiki_parse import get_page
from collections import OrderedDict

dl_base = 'https://dragalialost.gamepedia.com/'
dl_api_base = dl_base + 'api.php'

valid_categories = ['Adventurers']
element_embed_colour = {
    '1': 0xa92829,  # fire - red
    '2': 0x2d69b5,  # water - blue
    '3': 0x29a863,  # wind - green
    '4': 0xb09e2c,  # light - gold
    '5': 0x842aad   # shadow - purple
}

#=========================DEFINE ALL THE TABLE COLUMNS
tables = {
    'Adventurers': [
        'Id',
        'Name',
        'FullName',
        'NameJP',
        'NameTC',
        'Title',
        'TitleJP',
        'TitleTC',
        'WeaponType',
        'WeaponTypeId',
        'Rarity',
        'ElementalType',
        'ElementalTypeId',
        'CharaType',
        'VariationId',
        'MinHp3',
        'MinHp4',
        'MinHp5',
        'MaxHp',
        'PlusHp0',
        'PlusHp1',
        'PlusHp2',
        'PlusHp3',
        'PlusHp4',
        'McFullBonusHp5',
        'MinAtk3',
        'MinAtk4',
        'MinAtk5',
        'MaxAtk',
        'PlusAtk0',
        'PlusAtk1',
        'PlusAtk2',
        'PlusAtk3',
        'PlusAtk4',
        'McFullBonusAtk5',
        'MinDef',
        'DefCoef',
        'Skill1Name',
        'Skill2Name',
        'Abilities11',
        'Abilities12',
        'Abilities13',
        'Abilities14',
        'Abilities21',
        'Abilities22',
        'Abilities23',
        'Abilities24',
        'Abilities31',
        'Abilities32',
        'Abilities33',
        'Abilities34',
        'ExAbilityData1',
        'ExAbilityData2',
        'ExAbilityData3',
        'ExAbilityData4',
        'ExAbilityData5',
        'ManaCircleName',
        'JapaneseCV',
        'EnglishCV',
        'Description',
        'IsPlayable',
        'MaxFriendshipPoint',
        'Obtain',
        'Availability',
        'ReleaseDate'
    ],
    'Abilities': [
        'Id',
        'GenericName',
        'Name',
        'Details',
        'AbilityIconName',
        'AbilityGroup',
        'PartyPowerWeight',
        'AbilityLimitedGroupId1',
        'AbilityLimitedGroupId2',
        'AbilityLimitedGroupId3'
    ],
    'Skills': [
        'SkillId',
        'Name',
        'SkillLv1IconName',
        'SkillLv2IconName',
        'SkillLv3IconName',
        'Description1',
        'Description2',
        'Description3',
        'HideLevel3',
        'Sp',
        'SPLv2',
        'SpRegen',
        'IsAffectedByTension',
        'CrisisModifier',
        'IframeDuration'
    ],
    'Dragons':[
        'BaseId',
        'Id',
        'Name',
        'FullName',
        'NameJP',
        'Title',
        'TitleJP',
        'Obtain',
        'Rarity',
        'ElementalType',
        'ElementalTypeId',
        'VariationId',
        'IsPlayable',
        'MinHp',
        'MaxHp',
        'MinAtk',
        'MaxAtk',
        'Skill1',
        'SkillName',
        'SkillDescription',
        'Abilities11',
        'Abilities12',
        'Abilities21',
        'Abilities22',
        'ProfileText',
        'FavoriteType',
        'JapaneseCV',
        'EnglishCV',
        'SellCoin',
        'SellDewPoint',
        'MoveSpeed',
        'DashSpeedRatio',
        'TurnSpeed',
        'IsTurnToDamageDir',
        'MoveType',
        'IsLongRange',
        'ReleaseDate',
        'Availability',
    ],
    'Wyrmprints':[
        'Id',
        'BaseId',
        'Name',
        'NameJP',
        'Rarity',
        'AmuletType',
        'MinHp',
        'MaxHp',
        'MinAtk',
        'MaxAtk',
        'VariationId',
        'Abilities11',
        'Abilities12',
        'Abilities13',
        'Abilities21',
        'Abilities22',
        'Abilities23',
        'Abilities31',
        'Abilities32',
        'Abilities33',
        'ArtistCV',
        'FlavorText1',
        'FlavorText2',
        'FlavorText3',
        'FlavorText4',
        'FlavorText5',
        'IsPlayable',
        'SellCoin',
        'SellDewPoint',
        'ReleaseDate',
        'FeaturedCharacters',
        'Obtain',
        'Availability'
    ],
    'Weapons':[
        'Id',
        'BaseId',
        'FormId',
        'WeaponName',
        'WeaponNameJP',
        'Type',
        'TypeId',
        'Rarity',
        'ElementalType',
        'ElementalTypeId',
        'MinHp',
        'MaxHp',
        'MinAtk',
        'MaxAtk',
        'VariationId',
        'Skill',
        'SkillName',
        'SkillDesc',
        'Abilities11',
        'Abilities21',
        'IsPlayable',
        'FlavorText',
        'SellCoin',
        'SellDewPoint',
        'ReleaseDate',
        'CraftNodeId',
        'ParentCraftNodeId',
        'CraftGroupId',
        'FortCraftLevel',
        'AssembleCoin',
        'DisassembleCoin',
        'DisassembleCost',
        'MainWeaponId',
        'MainWeaponQuantity',
        'CraftMaterialType1',
        'CraftMaterial1',
        'CraftMaterialQuantity1',
        'CraftMaterialType2',
        'CraftMaterial2',
        'CraftMaterialQuantity2',
        'CraftMaterialType3',
        'CraftMaterial3',
        'CraftMaterialQuantity3',
        'CraftMaterialType4',
        'CraftMaterial4',
        'CraftMaterialQuantity4',
        'CraftMaterialType5',
        'CraftMaterial5',
        'CraftMaterialQuantity5',
        'Obtain',
        'Availability',
        'AvailabilityId'
    ],
    'CoAbilities': [
        'Id',
        'GenericName',
        'Name',
        'Details',
        'AbilityIconName',
        'Category',
        'PartyPowerWeight'
    ]
}

child_tables = {
    'Adventurers': [
        'FullName',
        'Rarity'
    ],
    'Abilities': [
        'Name',
        'Details',
        'PartyPowerWeight'
    ],
    'Skills': [
        'Name',
        'Description1',
        'Description2',
        'Description3',
        'HideLevel3',
        'Sp',
        'SPLv2',
        'SpRegen'
    ],
    'Dragons':[
        'FullName',
        'Rarity'
    ],
    'Wyrmprints':[
        'Name',
        'Rarity',
        'VariationId',
        'Abilities11',
        'Abilities12',
        'Abilities13',
        'Abilities21',
        'Abilities22',
        'Abilities23',
        'Abilities31',
        'Abilities32',
        'Abilities33',
    ],
    'Weapons':[
        'WeaponName',
        'Rarity',
        'ElementalType',
        'Availability'
    ],
    'CoAbilities': [
        'Name',
        'Details',
        'PartyPowerWeight'
    ]
}

#=========================DEFINE ALL THE TABLES TO QUERY
adventurer_query_table = {
    'tables': [
        ('Adventurers', 'a'),
        ('Skills', 's1'),
        ('Skills', 's2'),
        ('Abilities', 'ab11'),
        ('Abilities', 'ab12'),
        ('Abilities', 'ab13'),
        ('Abilities', 'ab14'),
        ('Abilities', 'ab21'),
        ('Abilities', 'ab22'),
        ('Abilities', 'ab23'),
        ('Abilities', 'ab24'),
        ('Abilities', 'ab31'),
        ('Abilities', 'ab32'),
        ('Abilities', 'ab33'),
        ('Abilities', 'ab34'),
        ('CoAbilities', 'ex1'),
        ('CoAbilities', 'ex2'),
        ('CoAbilities', 'ex3'),
        ('CoAbilities', 'ex4'),
        ('CoAbilities', 'ex5')
    ],
    'join_on': [
        'a.Skill1Name=s1.Name',
        'a.Skill2Name=s2.Name',
        'a.Abilities11=ab11.Id',
        'a.Abilities12=ab12.Id',
        'a.Abilities13=ab13.Id',
        'a.Abilities14=ab14.Id',
        'a.Abilities21=ab21.Id',
        'a.Abilities22=ab22.Id',
        'a.Abilities23=ab23.Id',
        'a.Abilities24=ab24.Id',
        'a.Abilities31=ab31.Id',
        'a.Abilities32=ab32.Id',
        'a.Abilities33=ab33.Id',
        'a.Abilities34=ab34.Id',
        'a.ExAbilityData1=ex1.Id',
        'a.ExAbilityData2=ex2.Id',
        'a.ExAbilityData3=ex3.Id',
        'a.ExAbilityData4=ex4.Id',
        'a.ExAbilityData5=ex5.Id',
    ]
}

dragon_query_table = {
    'tables': None,
    'join_on': None
}

wyrmprint_query_table = {
    'tables': None,
    'join_on': None
}

weapon_query_table = {
    'tables': None,
    'join_on': None
}

skill_query_table = {
    'tables': None,
    'join_on': None
}

skill_learners_query_table = {
    'tables': None,
    'join_on': None
}

ability_query_table = {
    'tables': None,
    'join_on': None
}

ability_learners_query_table = {
    'tables': None,
    'join_on': None
}


def resolve_name(arg):
    redirect = dl_api_base + "?action=opensearch&search={}&redirects=resolve".format(urllib.parse.quote(arg))
    info = get_page(redirect)
    if not info[1] or not info[1][0]:
        return None
    else:
        return sorted(sorted(info[1]), key=lambda i: len(i))[0]


def get_category(arg):
    url = dl_api_base + "?action=parse&page={}".format(urllib.parse.quote(arg))
    info = get_page(url, 'categories')
    if info:
        categories = [' '.join(k['*'].split('_')) for k in info['parse']['categories']]
        return valid_categories[[v in categories for v in valid_categories].index(True)]
    else:
        return None


def get_query_results(url):
    return get_page(url)['cargoquery']


def build_query_string(definition):
    return dl_api_base + '?action=cargoquery&tables={}&join_on={}&fields={}'.format(
        ','.join(['='.join(t) for t in definition['tables']]),
        ','.join(definition['join_on']),
        ','.join(
            ['a._pageName=Page',
             ','.join(['{0}.{1}'.format(definition['tables'][0][1], f) for f in tables[definition['tables'][0][0]]])] +
            ([','.join(['{0}.{1}={0}{1}'.format(t[1], f) for f in child_tables[t[0]]]) for t in definition['tables'][1:]]
                if len(definition['tables']) > 0 else [])
             )
    )


def search(category, arg):
    data = OrderedDict()
    data['Embed Info'] = {'Title': arg}

    def adventurer():
        query = build_query_string(adventurer_query_table) + \
                "&where={}".format(urllib.parse.quote("FullName='{}'".format(arg)))
        raw = get_query_results(query)[0]['title']

        data['Embed Info']['URL'] = dl_base + urllib.parse.quote(raw['Page'])
        data['Embed Info']['Colour'] = element_embed_colour[raw['ElementalTypeId']]
        data['Embed Info']['Description'] = BSoup(BSoup(raw['Description'], 'lxml').text,'lxml').text
        icon = get_icon(category, '{}_0{}_r0{}'.format(raw['Id'], raw['VariationId'], raw['Rarity']))
        if icon:
            print(icon)
            data['Embed Info']['Icon'] = icon

        hp = list(itertools.accumulate([int(raw[k]) for k in
                                                     (['MaxHp', 'McFullBonusHp5'] +
                                                      [f'PlusHp{k}' for k in range(5)])]))[-1]
        str = list(itertools.accumulate([int(raw[k]) for k in
                                                     (['MaxAtk', 'McFullBonusAtk5'] +
                                                      [f'PlusAtk{k}' for k in range(5)])]))[-1]
        abilities = [
            [(raw[f'ab{i}{j}Name'], raw[f'ab{i}{j}PartyPowerWeight']) for j in range(1,5)
             if raw[f'ab{i}{j}Name']][-1]
            for i in range(1,4)]
        might = hp + str + 120 + \
                (200 if raw['s1HideLevel3'] == '1' else 300) + (200 if raw['s2HideLevel3'] == '1' else 300) + \
                list(itertools.accumulate([int(a[1]) for a in abilities]))[-1] + int(raw['ex5PartyPowerWeight'])

        data['Rarity'] = raw['Rarity'] + '★', False
        data['Element'] = raw['ElementalType'], True
        data['Weapon Type'] = raw['WeaponType'], True
        data['Class'] = raw['CharaType'], True
        data['Base Max Might'] = might, True
        data['Total Max HP'] = hp, True
        data['Total Max Str'] = str, True
        data[f"Skill 1 ({raw['Skill1Name']})"] = re.sub(r'\[\[[^\[\]]*]\]',
                                lambda matchobj: (matchobj.group(0)[2:-2]).split("|")[-1],
                         BSoup(BSoup(f"""_SP: {raw['s1SPLv2']}_
{raw['s1Description2'] if raw['s1HideLevel3'] == '1' else raw['s1Description3']}""", 'lxml').text, 'lxml').\
                             text.replace("'''", '')), False
        data[f"Skill 2 ({raw['Skill2Name']})"] = re.sub(r'\[\[[^\[\]]*]\]',
                                lambda matchobj: (matchobj.group(0)[2:-2]).split("|")[-1],
                         BSoup(BSoup(f"""_SP: {raw['s2SPLv2']}_
{raw['s2Description2'] if raw['s2HideLevel3'] == '1' else raw['s2Description3']}""", 'lxml').text, 'lxml').\
                             text.replace("'''", '')), False
        data['Co-Ability'] = raw['ex5Name'], True
        data['Abilities'] = ', '.join([a[0] for a in abilities]), True
        return data

    def skill():
        pass

    def ability():
        pass

    def dragon():
        pass

    def wyrmprint():
        pass

    def weapon():
        pass

    switch = {
        'Adventurers': adventurer,
        'Skills': skill,
        'Abilities': ability,
        'Dragons': dragon,
        'Wyrmprints': wyrmprint,
        'Weapons': weapon
    }

    return switch[category]() if category in switch else None


def get_icon(category, arg):
    """Get the image url for the icon."""
    url = dl_api_base + '?action=query&titles=File:{}.png'.format(arg)
    info = get_page(url, 'imageinfo&iiprop=url')
    if '-1' in info['query']['pages']:
        return None
    else:
        icon = info['query']['pages'][next(iter(info['query']['pages']))]['imageinfo'][0]['url']
        return icon