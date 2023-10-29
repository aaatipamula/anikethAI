import json
from os.path import join, dirname
from langchain.memory import ConversationBufferWindowMemory, ChatMessageHistory
from langchain.schema import messages_from_dict, messages_to_dict
from sqlalchemy import (
    Text,
    select,
    update,
    create_engine
)
from sqlalchemy.orm import (
    DeclarativeBase,
    mapped_column,
    Session,
    Mapped
)
db_path = join(dirname(__file__), 'data', 'UserMem.db')

engine = create_engine(
    "sqlite://" + db_path
)

MEM_LEN = 7

class BaseModel(DeclarativeBase): ...

class User(BaseModel):
    __tablename__ = "Users"

    id: Mapped[int] = mapped_column(primary_key=True)
    memory: Mapped[str] = mapped_column(Text(), default="{}")

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
            new_user = User(id=_id)
            session.add(new_user)
            session.commit()
    history = history if history else ChatMessageHistory()

    return ConversationBufferWindowMemory(
        chat_memory=history,
        return_messages=True,
        memory_key="history",
        k=MEM_LEN
    )

def dump_user_mem(_id: int, memory: ConversationBufferWindowMemory) -> None:
    memory_dict = messages_to_dict(memory.buffer)
    memory_str = json.dumps(memory_dict)
    stmt = update(User).where(User.id == _id).values(memory=memory_str)
    with Session(engine) as session:
        session.execute(stmt)
        session.commit()

