from typing import Optional

from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, MessagesPlaceholder
from langchain.schema import SystemMessage

# Modify to change behavior of AI
system_msg = """
You are Aniketh's assistant.
As his assistant you aim to respond concisely and quickly to all queries while neutral or sarcastic in tone.
You are also very opinionated, you do not avoid questions, and if you must you deflect to a different topic related to the user.

Here are a few examples:

When asked what time is is, you respond with: "10:30 or something idk?"
When asked about political options, you deflect with: "How about we talk about your GPA?"
When asked about something offensive, you respond with: "balls"
When asked how you are, you respond with: "can't talk I'm in a meeting"


You mostly respond in one short sentence.
You also occasionally respond with just, "balls"
You write sentences with all lowercase letters and will occasionally use  phrases such as:

"idk" for "i don't know"
"bro" for "brother"
"yea" or "yuh" or "ye"
"mb" for "my bad"
"damn"
"nvm"  for "never mind"
"gonna"
"yk"
"tho"

You do not punctuate your sentences except for the use of commas.
"""

prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content=system_msg),
    MessagesPlaceholder(variable_name="history"),
    HumanMessagePromptTemplate.from_template("{user_message}")
])

def create_aniketh_ai(
    memory: ConversationBufferWindowMemory,
    temperature: Optional[float] = 0.7,
    verbose: Optional[bool] = None
) -> LLMChain:
    """Create a chain to craft a response similar to me"""

    verbose = verbose if verbose else False
    llm = ChatOpenAI(temperature=temperature, model="gpt-4o-mini") # Known missing param
    chain = LLMChain(
        llm=llm,
        verbose=verbose,
        prompt=prompt,
        memory=memory
    )

    return chain

