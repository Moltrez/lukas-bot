import os, jsonpickle, json, numpy, cloudinary, cloudinary.uploader, cloudinary.api, urllib.request, urllib3
import jsonpickle.ext.numpy as jsonpickle_numpy
jsonpickle_numpy.register_handlers()
from feh_alias import *
from feh_personal import *
from fehwiki_parse import get_page, shorten_hero_name, feh_source, weapon_colours, valid_categories
from collections import deque

cache_log = deque([], 500)

filename = './data_cache.json'

class FehCache(object):
    def __init__(self):
        if not self.load():
            "Starting new cache..."
            self.aliases = aliases
            self.sons = sons
            self.waifus = waifus
            self.flaunts = flaunt
            self.python_preference = set()
            self.replacement_list = []
            self.data = {}
            self.categories = {}
            self.list = []
            self.last_update = '2017-11-27T00:00:00Z'
        aliases.update(self.aliases)
        self.aliases.update(aliases)

    def copy(self, other):
        self.aliases = aliases if 'aliases' not in dir(other) else other.aliases
        self.sons = sons if 'sons' not in dir(other) else other.sons
        self.waifus = waifus if 'waifus' not in dir(other) else other.waifus
        self.flaunts = flaunt if 'flaunts' not in dir(other) else other.flaunts
        self.python_preference = set() if 'python_preference' not in dir(other) else other.python_preference
        self.replacement_list = [] if 'replacement_list' not in dir(other) else other.replacement_list
        self.data = {} if 'data' not in dir(other) else other.data
        self.categories = {} if 'categories' not in dir(other) else other.categories
        self.list = [] if 'data' not in dir(other) else other.list
        self.last_update = '2017-11-27T00:00:00Z' if 'last_update' not in dir(other) else other.last_update

    def load(self):
        urllib3.disable_warnings()
        cloudinary.config()
        try:
            #assert(False) # force local load
            web_copy = cloudinary.api.resource(filename[2:], resource_type='raw')['url']
            response = urllib.request.urlopen(web_copy)
            print("Loaded from the internet.")
            loaded = jsonpickle.decode(json.load(response))
            self.copy(loaded)
            return True
        except Exception as ex:
            print(ex)
            if os.path.exists(filename):
                print("Loaded from local.")
                with open(filename, 'r') as to_load:
                    loaded = jsonpickle.decode(json.load(to_load))
                    self.copy(loaded)
                    return True
            else:
                return False


    def update(self):
        try:
            old_replacement_list = self.replacement_list
            changes = get_page('https://feheroes.gamepedia.com/api.php?action=query&list=recentchanges&rcprop=title|timestamp&rclimit=500&rcend=%s&rcnamespace=0|6' % self.last_update)['query']['recentchanges'][:-1]
            if changes:
                deleted = False
                self.last_update = changes[0]['timestamp']
                for change in changes:
                    title = change['title']
                    if title.startswith('File:'):
                        title = (' '.join(title.lstrip('File:').lstrip('Icon_Portrait_').lstrip('Weapon_').split('_'))).rstrip('.png').rstrip('.bmp').rstrip('.jpg').rstrip('.jpeg')
                    if title in self.data and title not in self.replacement_list:
                        self.replacement_list.append(title)
                        cache_log.appendleft('Set %s up for replacement.' % title)
                if old_replacement_list != self.replacement_list:
                    self.save()
        except Exception as ex:
            print(ex)

    def save(self):
        print("Saving cache and uploading to cloud...")
        with open(filename, 'w+') as save_to:
            json.dump(jsonpickle.encode(self), save_to)
            save_to.close()
            result = cloudinary.uploader.upload(filename, resource_type='raw', public_id=filename[2:], invalidate=True)
        print("Save complete!")

    def set_fam(self, type, user, title):
        if type == 'son':
            if title is None and user in self.sons:
                del self.sons[user]
            else:
                self.sons[user] = title
        if type == 'waifu':
            if title is None and user in self.waifus:
                del self.waifus[user]
            else:
                self.waifus[user] = title
        self.save()

    def set_flaunt(self, user, url):
        self.flaunts[user] = url
        self.save()

    def set_list(self, list):
        if isinstance(self.list, dict):
            self.list.update(list)
        else:
            self.list = list
        self.save()

    def add_alias(self, alias, name, save=True, resolve_conflicts=True):
        alias = alias.lower().replace(' ', '')
        if alias[-1] in ['1','2','3']:
            alias = alias[:-1]
        if alias not in ['son', 'my son', 'waifu', 'my waifu'] and '/' not in alias\
            and (alias not in self.aliases or
                    (alias in self.aliases and name != self.aliases[alias] and not resolve_conflicts)):
                self.aliases[alias] = name
                cache_log.appendleft('Added alias: %s -> %s' % (alias, name))
                if save:
                    self.save()
                else:
                    return True
        if alias in self.aliases and name != self.aliases[alias] and resolve_conflicts:
            # create an internal disambiguation page
            if alias in self.data:
                should_save = False
                # already an internal disambiguation page
                if name not in self.data[alias]['1Could refer to:'][0].split('\n'):
                    # add to the internal disambiguation page listings if not already in there
                    self.data[alias]['1Could refer to:'] = self.data[alias]['1Could refer to:'][0] + '\n' + name, False
                    cache_log.appendleft('Found alias conflict!\nAdded alias `%s`to disambiguation.' % alias)
                    should_save = True
                if self.aliases[alias] != alias:
                    self.aliases[alias] = alias
                    cache_log.appendleft('Linking alias `%s` to its disambiguation page.' % alias)
                    should_save = True
                if should_save:
                    if save:
                        self.save()
                    else:
                        return True
            else:
                # create an internal disambiguation page, links to current aliased-to-name with no epithet
                new_data = {'Embed Info': {'Colour':weapon_colours['Null'], 'Icon':None, 'Title':alias,
                                           'URL': feh_source % self.aliases[alias].split(':')[0]},
                            '1Could refer to:': (self.aliases[alias] + '\n' + name, False)}
                self.data[alias] = new_data
                self.categories[alias] = ['Disambiguation pages']
                self.aliases[alias] = alias
                cache_log.appendleft(
                    'Found alias conflict!\nCreated disambiguation page for `%s` and linked alias to page.' % alias)
                if save:
                    self.save()
                else:
                    return True
        return False

    def delete_alias(self, alias, save=True):
        if alias in self.aliases:
            cache_log.appendleft('Deleted alias: %s -> %s' % (alias, self.aliases[alias]))
            del self.aliases[alias]
            if save:
                self.save()

    def resolve_alias(self, alias, save=True):
        # replace old aliases to ones without spaces
        alias = alias.lower()
        if alias.lower() in self.aliases:
            result = self.aliases[alias]
            if ' ' in alias:
                self.add_alias(alias.replace(' ', ''), result, save=False)
                self.delete_alias(alias, save=save)
            return result
        alias = alias.replace(' ', '')
        if alias.lower() in self.aliases:
            return self.aliases[alias]
        return None

    def clear_category(self, category):
        to_delete = []
        for title in self.categories.keys():
            if category in self.categories[title]:
                to_delete.append(title)
        for title in to_delete:
            self.delete_data(title)
        self.save()

    def add_data(self, alias, data, categories, save=True, force_save=False):
        if not any([c in valid_categories for c in categories]):
            return False
        name = data['Embed Info']['Title']
        will_save = self.add_alias(alias, name, save=False, resolve_conflicts=False)
        will_save = self.add_alias(name, name, save=False) or will_save
        will_save = self.add_alias(name.replace('(', '').replace(')', ''), name, save=False) or will_save
        will_save = self.add_alias(name.replace("'", '').replace('(', '').replace(')', ''), name, save=False) or will_save
        if ':' in name:
            will_save = self.add_alias(shorten_hero_name(name), name, save=False) or will_save
            will_save = self.add_alias(shorten_hero_name(name).replace(':', ''), name, save=False) or will_save
            will_save = self.add_alias(shorten_hero_name(name).replace("'", ''), name, save=False) or will_save
            will_save = self.add_alias(shorten_hero_name(name).replace("'", '').replace(':', ''), name, save=False) or will_save

        will_save = self.add_alias(name.replace('Attack', 'atk').replace('Speed', 'spd')\
                                                    .replace('Defense', 'def').replace('Resistance', 'res')\
                                                    .replace('Plus', '+'),
                                                    name, save=False) or will_save
        will_save = self.add_alias(name.replace('Attack', 'atk').replace('Speed', 'spd')\
                                                    .replace('Defense', 'def').replace('Resistance', 'res'),
                                                    name, save=False) or will_save
        if name not in self.data or self.data[name] != data:
            will_save = True
            self.data[name] = data
            cache_log.appendleft('Added data for: %s' % data['Embed Info']['Title'])
        if name not in self.categories or self.categories[name] != categories:
            will_save = True
            self.categories[name] = categories
        if force_save:
            self.save()
        else:
            if will_save:
                if save:
                    self.save()
            return will_save

    def delete_data(self, title, save=True):
        if title in self.data:
            del self.data[title]
            del self.categories[title]
            cache_log.appendleft('Deleted data for: %s' % title)
            return True
        return False

    def toggle_preference(self, user):
        if user in self.python_preference:
            self.python_preference.remove(user)
        else:
            self.python_preference.add(user)
        self.save()
        if user in self.python_preference:
            return True
        else:
            return False
