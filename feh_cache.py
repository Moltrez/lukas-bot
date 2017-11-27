import os, jsonpickle, json, numpy, cloudinary, cloudinary.uploader, cloudinary.api, urllib.request, urllib3
import jsonpickle.ext.numpy as jsonpickle_numpy
jsonpickle_numpy.register_handlers()
from feh_alias import *
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
        self.data = {}
        self.categories = {}
        self.list = []
        self.last_update = '2017-11-27T00:00:00Z'
        self.save()

    def copy(self, other):
        self.aliases = other.aliases
        self.data = other.data
        self.categories = other.categories
        self.list = other.list
        if 'last_update' not in dir(other):
            self.last_update = '2017-11-27T00:00:00Z'
        else:
            self.last_update = other.last_update
        self.save()

    def update(self):
        try:
            changes = get_page('https://feheroes.gamepedia.com/api.php?action=query&list=recentchanges&rcprop=title|timestamp&rclimit=50&rcend=%s&rcnamespace=0|6' % self.last_update)['query']['recentchanges'][:-1]
            if changes:
                self.last_update = changes[0]['timestamp']
                for change in changes:
                    title = change['title']
                    if title.startswith('File:'):
                        title = (' '.join(title.lstrip('File:').lstrip('Icon_Portrait_').lstrip('Weapon_').split('_'))).rstrip('.png').rstrip('.bmp').rstrip('.jpg').rstrip('.jpeg')
                        self.delete_data(title)
                        if title == 'Stats Table':
                            self.list = []
        except Exception as ex:
            print(ex)

    def save(self):
        with open(filename, 'w+') as save_to:
            json.dump(jsonpickle.encode(self), save_to)
            save_to.close()
            result = cloudinary.uploader.upload(filename, resource_type='raw', public_id=filename[2:], invalidate=True)

    def get_list(self):
        self.save()
        return self.list

    def set_list(self, list):
        self.list = list
        self.save()

    def add_alias(self, alias, name):
        if alias.lower() in ['son', 'my son', 'waifu', 'my waifu']:
            return
        if alias in self.aliases:
            return
        self.aliases[alias] = name
        self.save()
        cache_log.appendleft('Added alias: %s -> %s' % (alias, name))

    def delete_alias(self, alias):
        if alias in self.aliases:
            cache_log.appendleft('Deleted alias: %s -> %s' % (alias, self.aliases[alias]))
            del self.aliases[alias]
        self.save()

    def add_data(self, data, categories):
        self.data[data['Embed Info']['Title']] = data
        self.categories[data['Embed Info']['Title']] = categories
        self.save()
        cache_log.appendleft('Added data for: %s' % data['Embed Info']['Title'])

    def delete_data(self, title):
        if title in self.data:
            del self.data[title]
            cache_log.appendleft('Deleted data for: %s' % title)
        if title in self.categories:
            del self.categories[title]
        self.save()
