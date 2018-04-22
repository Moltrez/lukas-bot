from fehwiki_parse import *
from feh_cache import *
from socket import timeout


def update_category(cache, category):
    cache.update()
    members = get_page('http://feheroes.gamepedia.com/api.php?action=query&list=categorymembers&cmtitle=Category:%s&cmlimit=400' % category)['query']['categorymembers']
    members = [m['title'] for m in members]
    count = 0
    try:
        if members:
            for member in members:
                if not member.startswith('Category:') and\
                    not member.startswith('Template:') and\
                    not member.startswith('User talk:') and\
                        ((member not in cache.data) or member in cache.replacement_list):
                    print("Getting data for " + member)
                    try:
                        categories, data = get_data(member, None)
                        if member in cache.replacement_list:
                            cache.replacement_list.remove(member)
                        if any([c in categories for c in valid_categories]):
                            cache.add_data(member.lower(), data, categories, save=False)
                        while cache_log:
                            print(cache_log.pop())
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
    for c in valid_categories:
        update_category(cache, c)
    print(cache.last_update)
