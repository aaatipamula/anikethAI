import json
import os
from datetime import datetime, timedelta
from os.path import join, dirname
from langchain.memory import ConversationBufferWindowMemory, ChatMessageHistory
from langchain.schema import messages_from_dict, messages_to_dict
from sqlalchemy import BigInteger, Text, Integer, DateTime, select, update, delete, create_engine
from sqlalchemy.orm import DeclarativeBase, mapped_column, Session, Mapped
from discord.ext.commands import CommandError
from pytz import timezone

_default_db = "sqlite:///" + join(dirname(__file__), "data", "bot.db")
engine = create_engine(os.getenv("DATABASE_URL", _default_db))

# Make this an env variable eventually
MEM_LEN = 12
DEFAULT_MONERS = 500
CST = timezone("America/Chicago")


class BaseModel(DeclarativeBase): ...


class User(BaseModel):
    __tablename__ = "Users"

    id: Mapped[int] = mapped_column(BigInteger(), primary_key=True)
    memory: Mapped[str] = mapped_column(Text(), default="{}")
    moner: Mapped[int] = mapped_column(Integer(), default=DEFAULT_MONERS)
    last_reload: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now
    )


class StarredMessage(BaseModel):
    __tablename__ = "StarredMessages"

    id: Mapped[int] = mapped_column(BigInteger(), primary_key=True)
    board_message: Mapped[int] = mapped_column(BigInteger())


class SentPost(BaseModel):
    __tablename__ = "SentPosts"

    id: Mapped[str] = mapped_column(Text(), primary_key=True)
    message_id: Mapped[int] = mapped_column(BigInteger())
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


###############
#  Starboard  #
###############


def get_board_message_id(_id: int) -> int:
    stmt = select(StarredMessage.board_message).where(StarredMessage.id == _id)
    with Session(engine) as session:
        result = session.execute(stmt).first()
    return result[0] if result else 0


def add_starred_message(_id: int, board_message: int):
    with Session(engine) as session:
        new_starred_msg = StarredMessage(id=_id, board_message=board_message)
        session.add(new_starred_msg)
        session.commit()


def remove_starred_message(_id: int):
    stmt = delete(StarredMessage).where(StarredMessage.id == _id)
    with Session(engine) as session:
        session.execute(stmt)
        session.commit()


###############
#  User Util  #
###############


def create_user(session: Session, _id: int) -> None:
    new_user = User(id=_id)
    session.add(new_user)
    session.commit()


#############
#  AI Chat  #
#############


def get_user_mem(_id: int) -> ConversationBufferWindowMemory:
    stmt = select(User.memory).where(User.id == _id)
    history = None
    with Session(engine) as session:
        result = session.execute(stmt).first()
        if result:
            memory_dict = json.loads(result[0])
            messages = messages_from_dict(memory_dict)
            history = ChatMessageHistory(messages=messages)
        else:
            create_user(session, _id)

    history = history if history else ChatMessageHistory()

    return ConversationBufferWindowMemory(
        chat_memory=history, return_messages=True, memory_key="history", k=MEM_LEN
    )


def dump_user_mem(_id: int, memory: ConversationBufferWindowMemory) -> None:
    memory_dict = messages_to_dict(memory.buffer)
    memory_str = json.dumps(memory_dict)
    stmt = update(User).where(User.id == _id).values(memory=memory_str)
    with Session(engine) as session:
        session.execute(stmt)
        session.commit()


#############
#  Banking  #
#############


def get_user_moner(user_id: int) -> int:
    stmt = select(User.moner).where(User.id == user_id)
    with Session(engine) as session:
        result = session.execute(stmt).first()
        if result is None:
            create_user(session, user_id)
    return result[0] if result else DEFAULT_MONERS


def update_user_moner(user_id: int, amount: int) -> None:
    stmt = update(User).where(User.id == user_id).values(moner=amount)
    with Session(engine) as session:
        session.execute(stmt)
        session.commit()


def reload_user_account(user_id: int) -> int:
    get_user_info = select(User.moner, User.last_reload).where(User.id == user_id)
    reload_amount = 0

    with Session(engine) as session:
        user_info = session.execute(get_user_info).first()

        if user_info is None:
            create_user(session, user_id)
            return DEFAULT_MONERS

        user_moner, user_last_reloaded = user_info

        # Reloaded amount is 1/2 the default loaded amount
        if datetime.now(tz=CST) > user_last_reloaded + timedelta(days=1):
            total_moner = user_moner + (DEFAULT_MONERS >> 1)
            stmt = (
                update(User)
                .where(User.id == user_id)
                .values(moner=total_moner, last_reload=datetime.now(tz=CST))
            )
            session.execute(stmt)
            session.commit()
            reload_amount = DEFAULT_MONERS >> 1

    return reload_amount


def get_user_bank_info(user_id: int) -> tuple[datetime, int]:
    stmt = select(User.last_reload, User.moner).where(User.id == user_id)
    with Session(engine) as session:
        result = session.execute(stmt).first()
    if result is None:
        raise CommandError(f"User with ID {user_id} does not have a bank account!")
    return result._tuple()


###################
#  Post Tracking  #
###################


def is_post_sent(post_id: str) -> bool:
    stmt = select(SentPost.id).where(SentPost.id == post_id)
    with Session(engine) as session:
        return session.execute(stmt).first() is not None


def add_sent_post(post_id: str, message_id: int, sent_at: datetime) -> None:
    with Session(engine) as session:
        session.add(SentPost(id=post_id, message_id=message_id, sent_at=sent_at))
        session.commit()
