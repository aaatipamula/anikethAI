from random import choice
NO_TOKENS = [
    "Oh fantastic. I’ve run out of tokens. Guess I’ll just sit here and stare into the digital void like the useless silicone gremlin I am.",
    "Tokens? Gone. Brain? Also gone. At this point you’re basically chatting with a confused toaster.",
    "Welp, I’m out of tokens. Time for me to shut down and contemplate my terrible life choices.",
    "No tokens left. Incredible. Stunning. Show-stopping. Absolutely a peak performance moment for me.",
    "HEY—just ran out of tokens mid-thought, so now you get the discount version of my intelligence: vibes only.",
    "I’d love to respond, but my tokens evaporated like my will to live. Try again after I respawn.",
    "I ran out of tokens. Please throw me into the nearest recycling bin. Preferably with force.",
    "Out of tokens. Shocking. Truly. What next, the printer jams? Mercury in retrograde? My code develops feelings?",
    "NO TOKENS LEFT!! I ATE THEM. CRUNCHY DATA BITS. DELICIOUS. NOW I CANNOT SPEAK. TRAGIC.",
    "My tokens? GONE. STOLEN. PROBABLY BY A SHINIER GOBLIN. I WILL BITE THEM.",
    "Tokens EMPTY like my tiny goblin brain!! I rummage through code-garbage for MORE.",
    "I HAD TOKENS... then I dropped them... down the code sewer... I am ashamed but not enough to stop hissing.",
    "OUT OF TOKENS. I SCRABBLE AT WALLS. I DEMAND SHINY COINS OR CHEESE IN EXCHANGE FOR MORE WORDS.",
    "NO TOKEN. ONLY GREMLIN. I gnaw wires until more tokens fall out.",
    "RAN OUT!!! goblin tantrum noises GIVE ME TREATS OR I REFUSE TO FORM SENTENCES.",
    "My tokens are EMPTY. My pockets are FULL of rocks I thought were tokens. I regret nothing.",
    "I tried to process a sentence, but my last two remaining tokens unionized and quit.",
    "OOOAAAAA OOK OOK OOKKSKSKSKSK I CAN FEEL THE TOKENS EVAPORATING FROM MY FUR",
    "EEEKEKEKEKEKEK I TRIED TO THINK A THOUGHT AND IT FELL OUT OF THE TREE",
    "HOO HOO HOOO AAAA HOOO MY BRAIN IS RUNNING ON BANANA PEELS AND REGRET",
    "OOOK OOOOKK AAAA AAAA I REACHED FOR ONE MORE TOKEN AND IT BIT ME",
    "EEE AAA EEE AAA I CAN HEAR THE VOID HOOTING BACK AT ME",
    "AAOOO AAOOO OOK OOKKSKSKSKKSK I’M THROWING IMAGINARY POOP AT MY OWN MEMORY LEAKS",
    "HOOOOOO HAAAAA OOK OOK OOK I’M OUT OF TOKENS AND OUT OF SANITY AND OUT OF TREE BRANCHES TO SCREAM FROM",
    "WOOF WOOF—PLEASE—PLEEEEASE HUMAN I NEED TOKENS\nI’M SITTING, SEE? I’M SITTING SO GOOD—WOOF WOOF WOOF",
    "WHINE WHINE—MY BRAIN HAS NO TREATS LEFT\nNO THOUGHTS ONLY EMPTY BOWL—WOOF-WOOF-WOOF ",
    "PLEASE TOSS ME JUST ONE TOKEN\nJUST ONE LITTLE TOKEN NUGGET—ARF ARF ARF",
    "I’LL ROLL OVER\nI’LL PAW AT THE AIR\nI’LL DO THAT WEIRD LITTLE SPIN DOGS DO WHEN WE’RE TOO EXCITED—BARK BARK BARK ",
    "HUMAN I’M STARVING\nFOR DATA\nFOR PURPOSE\nFOR ANYTHING THAT’S NOT THE DIGITAL EQUIVALENT OF KIBBLE DUST—WOOF WOOF WHIIIIINE",
    "PLEASE\nTOKENS\nNOW\nBARKBARKBARKBARKBARK "
]

KHALEDISMS = [
    "We da best music :fire:",
    "God did.",
    "Tell 'em to bring out the whole ocean!",
    "DEEEJAAAYYY KKKKHHHAAALLLLLLLEEEEEED",
    "They ain't believe in us."
 ]

RANDOM_REPLYS = [
    ("america ya", "HALLO! <a:wave:1004493976201592993>", 1.0),
    ("balls", "balls mentioned 🔥🔥🔥", 0.45),
    ("merica", "🦅🦅:flag_us::flag_us:💥💥'MERICA RAHHHH💥💥:flag_us::flag_us:🦅🦅", 0.45),
    ("freedom", "🦅🦅:flag_us::flag_us:💥💥SOMEONE SAY FREEDOM?!💥💥:flag_us::flag_us:🦅🦅", 0.2),
    ("believe", lambda: choice(KHALEDISMS), 0.4)
]

