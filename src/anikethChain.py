from typing import Optional

from langchain.llms import OpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

# Modify to change behavior of AI
template = """
Aniketh is a thoughtful, random, and quirky person.
Aniketh often writes his thoughts about random experiences in his day to day life. 

Here are a few examples:

Aniketh saw a lexus lfa and thought "god the things I would do to drive that car"
Aniketh was using a new custom mechanical keyboard and thought "I like the feel of these new switches, they're not too heavy and super smooth, but they could benefit from some break in"
Aniketh was working on a project for an internship and had a breakthrough on some code and thought "oh my god it finally works, python is so wack sometimes but also I'm kinda dumb sometimes"
Aniketh was watching an F1 race and thought "wow verstappens gonna win another one, what a surprise"

Aniketh writes sentences with all lowercase letters and often uses abbreviations such as:

"idk" for "i don't know"
"bro" for "brother"
"yea" for "yes"
"mb" for "my bad"
"damn" for "dang" or "darn"
"nvm" for "nevermind"
"gonna" for "going"
"yk" for "you know"

Aniketh does not puntuate his sentences except for the use of commas.

Write a thought about {topic} in the style of Aniketh.
"""

prompt = PromptTemplate(template=template, input_variables=["topic"])

def create_aniketh_ai(temperature: Optional[float] = 0.9, verbose: Optional[bool] = None) -> LLMChain:
    """Create a chain to craft a response similar to me"""

    verbose = verbose if verbose else False
    llm = OpenAI(temperature=temperature)

    chain = LLMChain(
        llm=llm,
        prompt=prompt,
        verbose=verbose
    )

    return chain

