import os, pickle

class Lukas(object):
    def __init__(self, statfile):
        print("A new boy is born.")
        self.fatigue = 500
        self.happiness = 0
        self.steps_taken = 0
        self.statfile = statfile

    def new_lukas(self):
        print("A new boy is born.")
        self.fatigue = 500
        self.happiness = 0
        self.steps_taken = 0
        self.save_stats()

    def take_step(self, steps=1):
        self.steps_taken += steps
        self.fatigue -= steps
        self.save_stats()
        if self.fatigue <= 0:
            return False
        return True

    def affect_happiness(self, happiness):
        self.happiness += happiness
        self.save_stats()

    def save_stats(self):
        print("A boy is saved.")
        with open(self.statfile, 'wb+') as save_to:
            pickle.dump(self, save_to, pickle.HIGHEST_PROTOCOL)
            self.print_status()

    def print_status(self):
        print(vars(self))