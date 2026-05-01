from dataclasses import dataclass
from enum import Enum


class Suit(Enum):
    HEARTS = "❤️"
    DIAMONDS = "♦️"
    CLUBS = "♣️"
    SPADES = "♠️"


class Rank(Enum):
    ACE = "A"
    TWO = "2"
    THREE = "3"
    FOUR = "4"
    FIVE = "5"
    SIX = "6"
    SEVEN = "7"
    EIGHT = "8"
    NINE = "9"
    TEN = "10"
    JACK = "J"
    QUEEN = "Q"
    KING = "K"


@dataclass(frozen=True)
class Card:
    rank: Rank
    suit: Suit

    def is_rank(self, rank: Rank) -> bool:
        return self.rank == rank

    def is_suit(self, suit: Suit) -> bool:
        return self.suit == suit

    def __str__(self) -> str:
        return f"`{self.rank.value} of {self.suit.value}`"

    def __eq__(self, value: object) -> bool:
        if isinstance(value, Card):
            return self.rank == value.rank and self.suit == value.suit
        return False


Cards = list[Card]
DECK: Cards = [Card(rank, suit) for suit in Suit for rank in Rank]

