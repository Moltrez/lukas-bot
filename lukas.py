import os, jsonpickle, json, re, random, numpy, cloudinary, cloudinary.uploader, cloudinary.api, urllib.request, urllib3

class Lukas(object):
    def __init__(self, statfile, force_new_boy=False):
        if not force_new_boy:
            urllib3.disable_warnings()
            cloudinary.config()
            try:
                web_lukas = cloudinary.api.resource(statfile[2:], resource_type='raw')['url']
                print(web_lukas)
                response = urllib.request.urlopen(web_lukas)
                print("A boy is loaded from the internet")
                loaded = jsonpickle.decode(json.load(response))
                self.copy(loaded)
                return
            except Exception as ex:
                if os.path.exists(statfile):
                    print("A boy is loaded.")
                    with open(statfile, 'r') as to_load:
                        loaded = jsonpickle.decode(json.load(to_load))
                        to_load.close()
                        self.copy(loaded)
                        return
        print("A new boy is born.")
        self.statfile = statfile
        self.stats = Stats()
        self.stamina = 500
        self.happiness = 0
        self.steps_taken = 0
        self.inventory = Inventory()
        self.save_stats()

    def save_stats(self):
        with open(self.statfile, 'w+') as save_to:
            json.dump(jsonpickle.encode(self), save_to)
            save_to.close()
            result = cloudinary.uploader.upload(self.statfile, resource_type='raw', public_id=self.statfile[2:], invalidate=True)

    def copy(self, other):
        self.statfile = other.statfile
        self.stats = other.stats
        self.stamina = other.stamina
        self.happiness = other.happiness
        self.steps_taken = other.steps_taken
        self.inventory = other.inventory

    def delete_status(self):
        """deletes all instances of a save file"""
        os.remove(self.statfile)
        cloudinary.api.delete_resources(self.statfile[2:], resource_type='raw')
        return Lukas(self.statfile, True)

    def new_lukas(self):
        """resets lukas"""
        print("A new boy is born.")
        self.stats = Stats()
        self.stamina = 500
        self.happiness = 0
        self.steps_taken = 0
        self.save_stats()

    def add_item(self, item):
        """adds an item to the inventory"""
        self.inventory.add_item(item)
        self.save_stats()

    def feed(self, item):
        """feeds specified item, returns false if item is insufficient or not found"""
        def dislike():
            self.stamina += 20
            self.affect_happiness(-20)
            self.modify_hp(5)
            return "I find this hard to palate..."

        def neutral():
            self.stamina += 30
            self.modify_hp(10)
            return "That was refreshing."

        def like():
            self.stamina += 50
            self.affect_happiness(20)
            self.modify_hp(15)
            return "Mmm, a fine meal."

        def love():
            self.stamina += 100
            self.affect_happiness(50)
            self.modify_hp(20)
            return "O-oh, now this is a treat!"
        switch = {
            'Sweet Cookie': love,
            'Blue Cheese': like,
            'Ham': neutral,
            'Flour': dislike
        }

        if self.stamina == 500:
            return "Thank you, but I am full."
        if item in self.inventory.items:
            if not item in switch:
                return "I don't think I can eat that!"
            elif self.inventory.consume(item):
                result = switch[item]()
                if (self.stamina > 500):
                    self.stamina = 500
                self.save_stats()
                return result
        return "I'm afraid we don't have any " + item + "."

    def modify_hp(self, hp):
        self.stats.current_hp += hp
        if self.stats.current_hp <= 0:
            self.new_lukas()
            return "i ded nao restart boop boop"
        if self.stats.current_hp > self.stats.hp_stat:
            self.stats.current_hp = self.stats.hp_stat
        return "Current HP: %2d/%2d" % (self.stats.current_hp, self.stats.hp_stat)

    def give_exp(self, exp):
        """awards exp, returns true if level up occurred"""
        result = self.stats.give_exp(exp)
        self.save_stats()
        return result

    def take_step(self, steps=1):
        """takes a step forward and consumes stamina, returns false if stamina is now 0"""
        self.steps_taken += steps
        self.stamina -= steps
        self.save_stats()
        if self.stamina <= 0:
            self.stamina = 0
            self.save_stats()
            return False
        return True

    def affect_happiness(self, happiness):
        """happiness setter"""
        self.happiness += happiness
        if (self.happiness > 500):
            self.happiness = 500
        if (self.happiness < 0):
            self.happiness = 0
        self.save_stats()

    def get_status(self):
        status_message = "This is my current status.\n"
        status_message += str(self.stats)
        status_message += '```' + format_status(vars(self)) + '```'
        return status_message

    def get_stats_array(self):
        return self.stats.array()

    def print_status(self):
        print(vars(self))

def format_status(dict):
    ret_string = ''
    for key in dict.keys():
        if (not key == 'statfile') and (not key == 'stats'):
            val = dict[key]
            ret_string += re.sub('_', ' ', key).capitalize() + ': ' + str(val) + '\n'

    return ret_string

class Inventory(object):
    def __init__(self):
        self.items = {'Sweet Cookie': 1, 'Ham': 3}

    def add_item(self, item):
        if item in self.items:
            self.items[item] += 1
        else:
            self.items[item] = 1

    def consume(self, item):
        if item in self.items:
            if self.items[item] > 0:
                self.items[item] -= 1
                return True
        return False

    def __str__(self):
        return "\n" + str(self.items)

class Stats(object):
    def __init__(self):
        self.unit_class = Class('Soldier', ['Knight'], 5, 5, 0, -10, -5, -5, 0)
        self.level = 1
        self.exp = 0
        self.current_hp = 22

        self.hp_stat = 22
        self.atk_stat = 10
        self.skl_stat = 4
        self.spd_stat = 4
        self.lck_stat = 2
        self.def_stat = 5
        self.res_stat = 4

        self.hp_growth = 50
        self.atk_growth = 30
        self.skl_growth = 40
        self.spd_growth = 25
        self.lck_growth = 30
        self.def_growth = 45
        self.res_growth = 20

    def levelup(self):
        if self.level != 20:
            self.level += 1
            if random.randrange(0, 100) <= (self.hp_growth + self.unit_class.hp_growth):
                self.increase('hp')
            if random.randrange(0, 100) <= (self.atk_growth + self.unit_class.atk_growth):
                self.increase('atk')
            if random.randrange(0, 100) <= (self.skl_growth + self.unit_class.skl_growth):
                self.increase('skl')
            if random.randrange(0, 100) <= (self.spd_growth + self.unit_class.spd_growth):
                self.increase('spd')
            if random.randrange(0, 100) <= (self.lck_growth + self.unit_class.lck_growth):
                self.increase('lck')
            if random.randrange(0, 100) <= (self.def_growth + self.unit_class.def_growth):
                self.increase('def')
            if random.randrange(0, 100) <= (self.res_growth + self.unit_class.res_growth):
                self.increase('res')

    def increase(self, stat):
        def hp():
            self.hp_stat += 1 if self.hp_stat < 52 else 0
        def atk():
            self.atk_stat += 1 if self.atk_stat < 40 else 0
        def skl():
            self.skl_stat += 1 if self.skl_stat < 40 else 0
        def spd():
            self.spd_stat += 1 if self.spd_stat < 38 else 0
        def lck():
            self.lck_stat += 1 if self.lck_stat < 40 else 0
        def df():
            self.def_stat += 1 if self.def_stat < 42 else 0
        def res():
            self.res_stat += 1 if self.res_stat < 40 else 0
        switch = {
            'hp' : hp,
            'atk' : atk,
            'skl' : skl,
            'spd' : spd,
            'lck' : lck,
            'def' : df,
            'res' : res
        }
        switch[stat]()

    def give_exp(self, exp):
        if self.level < 20:
            self.exp += exp
            if self.exp >= 100:
                self.levelup()
                if self.level == 20:
                    self.exp = 0
                else:
                    self.exp -= 100
                return True
        return False

    def array(self):
        return numpy.array([self.hp_stat, self.atk_stat, self.skl_stat, self.spd_stat, self.lck_stat, self.def_stat, self.res_stat])

    def __str__(self):
        return '```Class: ' + str(self.unit_class) + '    Lvl: ' + str(self.level) + '    Exp: ' + str(self.exp) + """
 HP: %2d/%2d
 HP|ATK|SKL|SPD|LCK|DEF|RES
%3d|%3d|%3d|%3d|%3d|%3d|%3d```""" % (self.current_hp, self.hp_stat, self.hp_stat, self.atk_stat, self.skl_stat, self.spd_stat, self.lck_stat, self.def_stat, self.res_stat)

class Class(object):
    def __init__(self, name, promotes_to, hp, atk, skl, spd, lck, df, res):
        self.name = name
        self.promotes_to = promotes_to

        self.hp_growth = hp
        self.atk_growth = atk
        self.skl_growth = skl
        self.spd_growth = spd
        self.lck_growth = lck
        self.def_growth = df
        self.res_growth = res

    def __str__(self):
        return self.name
