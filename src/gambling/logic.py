from random import sample
from typing import Optional

from discord.ext import commands

from gambling.models import Card, Cards, DECK, Rank, Suit


def convert_suit(argument: str) -> Suit | None:
    arg = argument.lower()

    print("Suit Arg: ", arg)

    match arg:
        case "spade" | "spades" | "♠️":
            return Suit.SPADES
        case "diamond" | "diamonds" | "♦️":
            return Suit.DIAMONDS
        case "club" | "clubs" | "♣️":
            return Suit.CLUBS
        case "heart" | "hearts" | "❤️":
            return Suit.HEARTS
        case _:
            return None


def convert_rank(argument: str) -> Rank | None:
    arg = argument.lower()

    print("Rank Arg: ", arg)

    match arg:
        case "a" | "ace":
            return Rank.ACE
        case "2" | "two":
            return Rank.TWO
        case "3" | "three":
            return Rank.THREE
        case "4" | "four":
            return Rank.FOUR
        case "5" | "five":
            return Rank.FIVE
        case "6" | "six":
            return Rank.SIX
        case "7" | "seven":
            return Rank.SEVEN
        case "8" | "eight":
            return Rank.EIGHT
        case "9" | "nine":
            return Rank.NINE
        case "10" | "nine":
            return Rank.TEN
        case "j" | "jack":
            return Rank.JACK
        case "q" | "queen":
            return Rank.QUEEN
        case "k" | "king":
            return Rank.KING
        case _:
            return None


def parse_raw_guess(guess: list[str]) -> tuple[Optional[Rank], Optional[Suit], bool]:
    if len(guess) > 4:
        guess_str = " ".join(guess)
        raise commands.BadArgument(
            f"Could not parse rank, suit, or card of `{guess_str}`"
        )

    rank: Optional[Rank] = None
    suit: Optional[Suit] = None
    all_in = False

    for val in guess:
        if val.lower() in ("shove", "allin", "everything"):
            all_in = True
            continue
        elif val.lower() == "of":
            continue

        if rank is None:
            rank = convert_rank(val)

        if suit is None:
            suit = convert_suit(val)

    return rank, suit, all_in


def deal_cards(n: int) -> Cards:
    return sample(DECK, n)


def _rank_in_cards(cards: Cards, rank: Rank) -> bool:
    return any(c.is_rank(rank) for c in cards)


def _suit_in_cards(cards: Cards, suit: Suit) -> bool:
    return any(c.is_suit(suit) for c in cards)


def get_multiplier(
    dealt_cards: Cards,
    rank: Optional[Rank] = None,
    suit: Optional[Suit] = None,
) -> int:
    if rank and suit:
        if Card(rank, suit) in dealt_cards:
            return 8
        return 0

    if rank and _rank_in_cards(dealt_cards, rank):
        return 4

    if suit and _suit_in_cards(dealt_cards, suit):
        return 2

    return 0
