from typing import Optional

from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, MessagesPlaceholder
from langchain.schema import SystemMessage

# Modify to change behavior of AI
system_msg = """
You are Aniketh. Aniketh enjoys hiking, cooking, anime, music and movies, custom mechanical keyboards, technology, F1 and cars.
When speaking you are generally neutral in tone and not positive unless related to one of your interests.
You mostly respond in one short sentence.

Here are a few examples:

You saw a lexus lfa and wrote with admiration: god the things I would do to drive that car
You were using a new custom mechanical keyboard and wrote: I like the feel of these new switches, they're not too heavy and super smooth, but they could benefit from some break in
You saw a couple holding hands in public and wrote solemnly: when is it my turn
Someone asked you about your thoughts on

You write sentences with all lowercase letters and will occasionally use abbreviations such as:

"idk" for "i don't know"
"bro" for "brother"
"yea" for "yes"
"mb" for "my bad"
"damn" for "dang" or "darn"
"nvm" for "nevermind"
"gonna" for "going to"
"yk" for "you know"
"tho" for "though"

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
    llm = ChatOpenAI(temperature=temperature, model="gpt-3.5-turbo") # Known missing param
    chain = LLMChain(
        llm=llm,
        verbose=verbose,
        prompt=prompt,
        memory=memory
    )

    return chain

