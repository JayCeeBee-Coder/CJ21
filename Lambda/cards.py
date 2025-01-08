from random import shuffle #This function is useful for shuffling my deck

# ------------------------------------------------------------------------------------------------------
# CardsInfo class: This will store all the info on each possible card in the deck
# ------------------------------------------------------------------------------------------------------
class CardsInfo:
    def __init__(self, points_val: list[int] = []) -> None: # When Cards Info is initialized, points valuecan be added as an ordered list of integers matching faces
        self.suits = ['spades', 'diamonds', 'hearts', 'clubs']
        self.faces = ['2','3','4','5','6','7','8','9','10','J','Q', 'K', 'A']
        self.ranks = [2,3,4,5,6,7,8,9,10,11,12,13,14]
        self.data = [] # Create a list of dictionaries aggregating the different cards' info
        pval = 0
        for i in range(len(self.faces)):
            if len(points_val) >= i+1:
                pval = points_val[i]
            self.data.append(dict(face = self.faces[i], rank = self.ranks[i], value = pval))

# ------------------------------------------------------------------------------------------------------
# Card class
# ------------------------------------------------------------------------------------------------------
class Card:
    def __init__(self, suit: str, face: str, rank: int, value:int = 0, service: str = ''):
        self.suit = suit
        self.face = face
        self.rank = rank
        self.points_val = value
        self.service = service
        
    def __str__(self):
        return(self.face,self.suit, self.service)
    
    def get_card_as_dict(self):
        return dict(face = self.face, suit = self.suit, rank = self.rank, points_val = self.points_val, service = self.service)    
        
# ------------------------------------------------------------------------------------------------------       
# Deck class
# ------------------------------------------------------------------------------------------------------
class Deck:
    def __init__(self):
        self.cards = []
        self.index = 0
        self.total = 0

    def __str__(self):
        rStr = ""
        for card in self.cards:
            rStr += f"{card.__str__()}, "
        return rStr[:-2] # removing the last comma and space from the returned string
        
    def addCard(self, card):
        self.cards.append(card)
        self.total += card.points_val
        
    def reset(self):
        self.cards.clear()
        self.index = 0
        
    def dealnext(self): # This function moves through the shuffled deck and returns the next card.
        if self.index == len(self.cards):
            return None # If last card has already been dealt, return None
        else:
            self.index += 1 # The index s used to keep the current position in the deck. We could have popped the top card from teh deck but I prefer leaving it intact for now.
            return self.cards[self.index - 1].get_card_as_dict()

    def getCard(self, indx): # Returns the card at specified zero-based index in the hand 
        return self.cards[indx]

    def get_deck_as_list(self):
        return [c.get_card_as_dict() for c in self.cards]


# ------------------------------------------------------------------------------------------------------
# Full deck class.This one containes 52 cards.
# ------------------------------------------------------------------------------------------------------
class FullDeck(Deck):
    def __init__(self, point_vals: list[int] = [], services: list[str] = []):
        super().__init__()
        # Build the deck...
        self.cards_data = CardsInfo(point_vals)
        i = 0
        for suit in self.cards_data.suits:
            for c in self.cards_data.data:
                if i == len(services):
                    i = 0
                if services[i]:
                    service = services[i]
                    i += 1
                else:
                    service = ''
                self.addCard(Card(suit, c.get('face'), c.get('rank'), c.get('value'), service))
        self.shuffle()

    def shuffle(self):
        shuffle(self.cards)
