from typing import Optional
from enum import Enum
from dataclasses import dataclass
from random import sample, choice
from discord import Embed
from discord.ext import commands

WIN_EMOJI = [
    "<a:lebron:1499437764465397780>",
    "<:pogfurret:1029051293672681522>",
    "<:poyo:970475490773176390>",
    "<:honks:864328580351655967>",
]

LOSE_EMOJI = [
    "<:ohmygah:1138311569466470473>",
    "<:pensiveclown:1354109439375835227>",
    "<:mort:1029051283778322433>",
    "<:poyo:970475490773176390>",
    "<:SpainWithoutTheS:1029051294767390750>",
    "<:asukaL:1136812895859134555>",
    "<:peepoWhy:1029051289235095682>",
    "<:prayge:970340014091292682>",
    "<:copege:970340189547417650>",
]


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
            # raise commands.BadArgument(f"Invalid suit `{arg}`")


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
            # raise commands.BadArgument(f"Invalid rank `{arg}`")


def parse_raw_guess(guess: list[str]) -> tuple[Optional[Rank], Optional[Suit]]:
    if len(guess) > 3:
        guess_str = " ".join(guess)
        raise commands.BadArgument(
            f"Could not parse rank, suit, or card of `{guess_str}`"
        )

    # Remove "of"
    if len(guess) == 3:
        keyword_of = guess[1]
        if keyword_of.lower() == "of":
            guess.pop(1)

    # Parse the rank and suit
    rank: Optional[Rank] = None
    suit: Optional[Suit] = None

    for val in guess:
        if rank is None:
            rank = convert_rank(val)
        if suit is None:
            suit = convert_suit(val)

    return rank, suit


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
    if rank and suit and Card(rank, suit) in dealt_cards:
        return 8

    if rank and _rank_in_cards(dealt_cards, rank):
        return 4

    if suit and _suit_in_cards(dealt_cards, suit):
        return 2

    return 0


def random_win_emoji() -> str:
    return choice(WIN_EMOJI)


def random_lose_emoji() -> str:
    return choice(LOSE_EMOJI)


def gambling_embed(
    dealt_cards: Cards,
    guessed_rank: Optional[Rank],
    guessed_suit: Optional[Suit],
    won: bool,
    diff_amount: int,
    total_moners: int,
):
    a = Embed(
        title="Gambling Time!! 🤑",
        color=0x7BD389,
    )

    dealt_card_str = "  ".join(str(card) for card in dealt_cards)

    a.add_field(
        name="Dealt Cards:",
        value=dealt_card_str,
        inline=False,
    )

    if guessed_rank and guessed_suit:
        guess_str = str(Card(guessed_rank, guessed_suit))
    elif guessed_rank:
        guess_str = f"`Rank: {guessed_rank.value}`"
    elif guessed_suit:
        guess_str = f"`Suit: {guessed_suit.value}`"
    else:
        # This should not occur
        raise ValueError("Missing both rank and suit")

    a.add_field(name="Guess:", value=guess_str, inline=False)

    if won:
        a.add_field(
            name=f"You Win! {random_win_emoji()}",
            value=f"{diff_amount} has has been added to your moners",
            inline=False,
        )
    else:
        a.add_field(
            name=f"You Lost {random_lose_emoji()}",
            value=f"{diff_amount} has has been removed from your moners",
            inline=False,
        )

    a.set_footer(text=f"Balance: {total_moners}")

    return a


def gambling_error(msg: str):
    a = Embed(
        title="Gambling Error! 😠",
        description=msg,
        color=0x7BD389,
    )

    return a
