import os, pickle, re, random

class Lukas(object):
    def __init__(self, statfile):
        print("A new boy is born.")
        self.statfile = statfile
        self.stats = Stats()
        self.stamina = 500
        self.happiness = 0
        self.steps_taken = 0
        self.inventory = Inventory()

    def new_lukas(self):
        """resets lukas"""
        print("A new boy is born.")
        self.stats = Stats()
        self.stamina = 500
        self.happiness = 0
        self.steps_taken = 0
        self.save_stats()

    def feed(self, item):
        """feeds specified item, returns false if item is insufficient or not found"""
        if self.inventory.consume(item):
            switch = {

            }
            switch[item]()
            if (self.stamina > 500):
                self.stamina = 500
            self.save_stats()
            return True
        return False

    def give_exp(self, exp):
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
        self.save_stats()

    def save_stats(self):
        print("A boy is saved.")
        with open(self.statfile, 'wb+') as save_to:
            pickle.dump(self, save_to, pickle.HIGHEST_PROTOCOL)
            self.print_status()

    def get_status(self):
        status_message = "This is my current status.\n"
        status_message += str(self.stats)
        status_message += '```' + format_status(vars(self)) + '```'
        return status_message

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
        self.items = dict()

    def check_item(self, item):
        return item in self.items

    def consume(self, item):
        if self.check_item(item):
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


    def __str__(self):
        return '```Class: ' + str(self.unit_class) + '    Lvl: ' + str(self.level) + '    Exp: ' + str(self.exp) + """
HP/ATK/SKL/SPD/LCK/DEF/RES
""" + "%2d/%3d/%3d/%3d/%3d/%3d/%3d```" % (self.hp_stat, self.atk_stat, self.skl_stat, self.spd_stat, self.lck_stat, self.def_stat, self.res_stat)

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
