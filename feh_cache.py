import os, jsonpickle, json, numpy, cloudinary, cloudinary.uploader, cloudinary.api, urllib.request, urllib3
import jsonpickle.ext.numpy as jsonpickle_numpy
jsonpickle_numpy.register_handlers()
from feh_alias import *
from feh_personal import *
from fehwiki_parse import get_page
from collections import deque

cache_log = deque([], 20)

filename = './data_cache.json'

class FehCache(object):
    def __init__(self):
        urllib3.disable_warnings()
        cloudinary.config()
        try:
            web_copy = cloudinary.api.resource(filename[2:], resource_type='raw')['url']
            response = urllib.request.urlopen(web_copy)
            print("Loaded from the internet.")
            loaded = jsonpickle.decode(json.load(response))
            self.copy(loaded)
            return
        except Exception as ex:
            print(ex)
            if os.path.exists(filename):
                print("Loaded from local.")
                with open(filename, 'r') as to_load:
                    loaded = jsonpickle.decode(json.load(to_load))
                    self.copy(loaded)
                    return
        "Starting new cache..."
        self.aliases = aliases
        self.sons = sons
        self.waifus = waifus
        self.flaunts = flaunt
        self.data = {}
        self.categories = {}
        self.list = []
        self.last_update = '2017-11-27T00:00:00Z'
        self.save()

    def copy(self, other):
        self.aliases = aliases if 'aliases' not in dir(other) else other.aliases
        self.sons = sons if 'sons' not in dir(other) else other.sons
        self.waifus = waifus if 'waifus' not in dir(other) else other.waifus
        self.flaunts = flaunt if 'flaunts' not in dir(other) else other.flaunts
        self.data = {} if 'data' not in dir(other) else other.data
        self.categories = {} if 'categories' not in dir(other) else other.categories
        self.list = [] if 'data' not in dir(other) else other.list
        self.last_update = '2017-11-27T00:00:00Z' if 'last_update' not in dir(other) else other.last_update
        self.save()

    def update(self):
        try:
            changes = get_page('https://feheroes.gamepedia.com/api.php?action=query&list=recentchanges&rcprop=title|timestamp&rclimit=100&rcend=%s&rcnamespace=0|6' % self.last_update)['query']['recentchanges'][:-1]
            if changes:
                deleted = False
                self.last_update = changes[0]['timestamp']
                for change in changes:
                    title = change['title']
                    if title.startswith('File:'):
                        title = (' '.join(title.lstrip('File:').lstrip('Icon_Portrait_').lstrip('Weapon_').split('_'))).rstrip('.png').rstrip('.bmp').rstrip('.jpg').rstrip('.jpeg')
                    if self.delete_data(title, save=False):
                        deleted = True
                if deleted:
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
        self.list = list
        self.save()

    def add_alias(self, alias, name, save=True):
        alias = alias.lower()
        if alias not in ['son', 'my son', 'waifu', 'my waifu'] and alias not in self.aliases and '/' not in alias:
            self.aliases[alias] = name
            cache_log.appendleft('Added alias: %s -> %s' % (alias, name))
        if save:
            self.save()

    def delete_alias(self, alias, save=True):
        if alias in self.aliases:
            cache_log.appendleft('Deleted alias: %s -> %s' % (alias, self.aliases[alias]))
            del self.aliases[alias]
        if save:
            self.save()

    def clear_category(self, category):
        to_delete = []
        for title in self.categories.keys():
            if category in self.categories[title]:
                to_delete.append(title)
        for title in to_delete:
            self.delete_data(title, save=False)
        self.save()

    def add_data(self, data, categories, save=True):
        self.data[data['Embed Info']['Title']] = data
        self.categories[data['Embed Info']['Title']] = categories
        if save:
            self.save()
        cache_log.appendleft('Added data for: %s' % data['Embed Info']['Title'])

    def delete_data(self, title, save=True):
        deleted = False
        if title in self.data:
            del self.data[title]
            del self.categories[title]
            cache_log.appendleft('Deleted data for: %s' % title)
            deleted = True
        if save:
            self.save()
        return deleted
