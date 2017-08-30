import random


class Deck(object):
    def __init__(self):
        self.cards = [a + ' of ' + b for a in ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
                      for b in ['Diamonds', 'Clubs', 'Hearts', 'Spades']]

    def shuffle(self):
        """Shuffles the cards."""
        random.shuffle(self.cards)

    def deal(self, num_hands=4, hand_size=13):
        """returns num_hands hands of size hand_size"""
        ret = []
        for i in range(0, num_hands):
            ret.append(self.cards[i::int(len(self.cards) / hand_size)][:hand_size])
        return ret
