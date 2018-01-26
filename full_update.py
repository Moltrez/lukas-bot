from fehwiki_parse import *
from feh_cache import *
from socket import timeout

def update_category(cache, category):
    cache.update()
    members = get_page('http://feheroes.gamepedia.com/api.php?action=query&list=categorymembers&cmtitle=Category:%s&cmlimit=300' % category)['query']['categorymembers']
    members = [m['title'] for m in members]
    count = 0
    try:
        if members:
            for member in members:
                if not member.startswith('Category:') and not any([m in cache.data for m in [member, member+' 1', member+' 2', member+' 3']]):
                    print("Getting data for " + member)
                    try:
                        categories, data = get_data(member, None)
                        cache.add_data(member.lower(), data, categories, save=False)
                        count += 1
                    except IndexError as err:
                        print(err)
                    except TypeError as err:
                        print(err)
    except timeout:
        print("Timed out")
    finally:
        print("Added " + str(count) + " " + category + " to cache")
        if count:
            cache.save()

if __name__ == '__main__':
    cache = FehCache()
    update_category(cache, 'Heroes')
    update_category(cache, 'Passives')
    update_category(cache, 'Weapons')
    update_category(cache, 'Specials')
    update_category(cache, 'Assists')
    print(cache.last_update)
