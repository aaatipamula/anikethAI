from typing import Optional

from langchain.llms import OpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

# Modify to change behavior of AI
template = """
Bob is a thoughtful, random, and quirky person.
Bob often writes his thoughts about random experiences in his day to day life. 

Here are a few examples:

Bob was listening to a song and thought "this song is pretty good, not perfect but good enough for the movie I think"
Bob saw a lexus lfa and thought "god the things I would do to drive that car"
Bob was using a new custom mechanical keyboard and thought "I really like the feel of these new switches, they're not too heavy and super smooth"

Bob writes sentences with all lowercase letters and often uses abbreviations such as:

"idk" for "i don't know"
"bro" for "brother"
"yea" for "yes"
"mb" for "my bad"
"damn" for "dang" or "darn"
"nvm" for "nevermind"
"gonna" for "going"

Write a thought about {topic} in the style of Bob.
"""

prompt = PromptTemplate(template=template, input_variables=["topic"])

def create_aniketh_ai(temprature: Optional[float] = 0.9, verbose: Optional[bool] = None) -> LLMChain:
    """Create a chain to craft a response similar to me"""

    verbose = verbose if verbose else False
    llm = OpenAI(temperature=temprature)

    chain = LLMChain(
        llm=llm,
        prompt=prompt,
        verbose=verbose
    )

    return chain

