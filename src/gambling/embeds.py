from random import choice
from typing import Optional

from discord import Embed

from gambling.models import Card, Cards, Rank, Suit

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
        name="Cards Dealt:",
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
            name=f"You Win!  {random_win_emoji()}",
            value=f"*{diff_amount}* has has been added to your moners",
            inline=False,
        )
    else:
        a.add_field(
            name=f"You Lost  {random_lose_emoji()}",
            value=f"*{diff_amount}* has has been removed from your moners",
            inline=False,
        )

    if total_moners <= 0:
        a.set_footer(text=f"Balance: {total_moners} (Reload with `.bank reload`)")
    else:
        a.set_footer(text=f"Balance: {total_moners}")

    return a


def gambling_error(msg: str):
    a = Embed(
        title="Gambling Error! 😠",
        description=msg,
        color=0x7BD389,
    )

    return a
