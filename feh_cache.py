import os, jsonpickle, json, numpy, cloudinary, cloudinary.uploader, cloudinary.api, urllib.request, urllib3
import jsonpickle.ext.numpy as jsonpickle_numpy
jsonpickle_numpy.register_handlers()
from feh_alias import *
from feh_personal import *
from fehwiki_parse import get_page
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
            self.replacement_list = []
            self.data = {}
            self.categories = {}
            self.list = []
            self.last_update = '2017-11-27T00:00:00Z'
        self.aliases.update(aliases)
        self.save()

    def copy(self, other):
        self.aliases = aliases if 'aliases' not in dir(other) else other.aliases
        self.sons = sons if 'sons' not in dir(other) else other.sons
        self.waifus = waifus if 'waifus' not in dir(other) else other.waifus
        self.flaunts = flaunt if 'flaunts' not in dir(other) else other.flaunts
        self.replacement_list = [] if 'replacement_list' not in dir(other) else other.replacement_list
        self.data = {} if 'data' not in dir(other) else other.data
        self.categories = {} if 'categories' not in dir(other) else other.categories
        self.list = [] if 'data' not in dir(other) else other.list
        self.last_update = '2017-11-27T00:00:00Z' if 'last_update' not in dir(other) else other.last_update

    def load(self):
        urllib3.disable_warnings()
        cloudinary.config()
        try:
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
                if old_replacement_list == self.replacement_list:
                    self.save()
        except Exception as ex:
            print(ex)

    def save(self):
        print("Saving cache and uploading to cloud...")
        with open(filename, 'w+') as save_to:
            json.dump(jsonpickle.encode(self), save_to)
            save_to.close()
            result = cloudinary.uploader.upload(filename, resource_type='raw', public_id=filename[2:], invalidate=True)

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

    def add_alias(self, alias, name, save=True):
        alias = alias.lower().replace(' ', '')
        if alias not in ['son', 'my son', 'waifu', 'my waifu'] and alias not in self.aliases and '/' not in alias:
            self.aliases[alias] = name
            cache_log.appendleft('Added alias: %s -> %s' % (alias, name))
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

    def resolve_alias(self, alias):
        # replace old aliases to ones without spaces
        alias = alias.lower()
        if alias.lower() in self.aliases:
            result = self.aliases[alias]
            if ' ' in alias:
                self.add_alias(alias.replace(' ', ''), result, save=False)
                self.delete_alias(alias)
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
        name = data['Embed Info']['Title']
        will_save = self.add_alias(alias, name, save=False)
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


    def delete_data(self, title):
        if title in self.data:
            del self.data[t]
            del self.categories[t]
            cache_log.appendleft('Deleted data for: %s' % t)
            return True
        return False
