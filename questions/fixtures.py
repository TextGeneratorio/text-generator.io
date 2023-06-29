import json

from questions.example_fixtures import openai_examples


class Fixture(object):
    def __init__(self):
        super(Fixture, self).__init__()

    def to_JSON(self):
        # todo compress by removing nulls
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


# todo careful with global

_stop_reason = None


def set_stop_reason(stop_reason):
    global _stop_reason
    _stop_reason = stop_reason


def get_stop_reason():
    global _stop_reason
    return _stop_reason


use_cases = {
    "fantasy-writing": {
        "title": "Fantasy Writing - Text Generator API",
        "description": "Write a fantasy novel - Text Generator API for fiction and fantasy writing",
        "generate_params": {
            "text": "The battle between the elves and goblins has begun,",
            "number_of_results": 4,
            "max_length": 100,
            "max_sentences": 4,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1.17,
            "seed": 0,
        },
        "results": [
            {
                "generated_text": "The battle between the elves and goblins has begun, but it seems to be going against the Goblins. The Goblin King is defeated by the king of Elf, he then returns home with his troops. But there was one thing that happened while they were fighting in a forest... a goblin got trapped in an enchanted tree... A new game from Wizards Unite is out! - Explore World of Warcraft: Shadowlands on PC or Mac Find out what happens when you try to remove the curse?",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "The battle between the elves and goblins has begun, but it's not over yet. The game is still in progress as you can see from this new update for the campaign! It's now available on Steam Early Access and will be launched to general release next month.\nSwords of Valeria is a turn-based strategy RPG with a heavy focus on storytelling.",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "The battle between the elves and goblins has begun, with Gandalf leading his company. The battle is being fought in Dol Guldur; a dungeon-like fortress that is located inside Mount Doom. Frodo Baggins (voiced by Billy Boyd), an ordinary hobbit from Hobbiton, encounters three dwarfs: Bofur (voice of John Rhys-Davies) who serves as his guide, Bombur (voice of Ian Holm) who acts as a sort of cook, and Glumdalclitch (voice",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "The battle between the elves and goblins has begun, with an army of both armies now fighting at full strength. This means that the forces of evil are on the rise, as well as their numbers have grown greatly. This is why you should prepare yourself for them. The game will begin after a short pause when both sides enter into combat mode.",
                "stop_reason": "max_sentences",
            },
        ],
    },
    "spanish-sentiment-analysis": {
        "title": "Spanish sentiment analysis - Text Generator API",
        "description": "Spanish tweet analysis - Decide si el sentimiento de un Tweet es positivo, neutral o negativo.",
        "generate_params": {
            "text": 'Decide si el sentimiento de un Tweet es positivo, neutral o negativo.\n\nTweet: "¡Me encantó la nueva película de Batman!"\nSentimiento: ',
            "number_of_results": 4,
            "max_length": 100,
            "max_sentences": 4,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1.17,
            "seed": 0,
        },
        "results": [
            {
                "generated_text": 'Decide si el sentimiento de un Tweet es positivo, neutral o negativo.\n\nTweet: "¡Me encantó la nueva película de Batman!"\nSentimiento: Positive\n\nTweet: "Sentimientos encontrados about this movie. Negative"\n\nA positive tweet has a positive sentiment and is considered positive, negative tweets have a negative sentiment. A neutral tweet does not have an explicit positive or negative feeling but rather reflects the overall tone of a post. You can find these in the comments section below a post on Twitter.',
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": 'Decide si el sentimiento de un Tweet es positivo, neutral o negativo.\n\nTweet: "¡Me encantó la nueva película de Batman!"\nSentimiento: Positive\n\nTweet: "I love that movie! Positive"\nYes Yes Yes Yes Yes Yes Yes Yes No Yes Yes Yes Yes Yes No Yes Yes Yes Yes Yes Yes No Negative Yes Yes Yes Yes Yes No No No No No Yes Yes Yes Yes Yes No Negative No No No No Yes Yes Yes Yes No No No No Yes Yes Yes No Negative Yes Yes Yes Yes Yes No No No No Yes Yes Yes Yes Yes Yes Negative No Yes No Yes Yes Yes No No Yes Yes Yes Yes No Negative Yes No Yes',
                "stop_reason": "max_length",
            },
            {
                "generated_text": 'Decide si el sentimiento de un Tweet es positivo, neutral o negativo.\n\nTweet: "¡Me encantó la nueva película de Batman!"\nSentimiento: Positive\n\nTweet: "Thanksgiving is a holiday I love to celebrate." Sentiment: Negative\r\nTweet: "I hate this song" Negative\r\nNegative\r\nPositive Positive Negative Positive Positive Positive Positive Negative Positive Positive Negative Positive Negative Positive Positive Positive Positive Negative Positive Negative Positive Positive Positive Negative Positive Negative Negative Negative Negative Positive Negative Positive Positive Positive Negative Positive Negative Positive Negative Negative Positive Positive Negative Positive Negative Positive Negative Positive Negative Positive Negative Positive Negative Negative Positive Negative Negative Positive Negative Positive Negative Negative Positive Negative Positive Negative Negative Positive Negative Positive',
                "stop_reason": "max_length",
            },
            {
                "generated_text": 'Decide si el sentimiento de un Tweet es positivo, neutral o negativo.\n\nTweet: "¡Me encantó la nueva película de Batman!"\nSentimiento: Positive\n\nPositive tweet. No negative tweets. Yes positive sentiment is the most likely result of this action. Negative sentiment is less probable and might not be present at all.',
                "stop_reason": "max_sentences",
            },
        ],
    },
    "dynamic-sentiment-analysis": {
        "title": "Dynamic Flexible sentiment analysis - Text Generator API",
        "description": "Flexible sentiment analysis, changin classes of classifying text.",
        "generate_params": {
            "text": "\nI don't feel well today / SENTIMENTS: good, ok, bad / BEST MATCH: bad\nHope everything is alright / SENTIMENTS: good, ok, bad / BEST MATCH: good\nlets go to the store / SENTIMENTS: sick, ok, travel / BEST MATCH: travel\nlets go fishing  / SENTIMENTS: sick, stayput, travel / BEST MATCH: travel\nlets get a haircut  / SENTIMENTS: good, ok, travel / BEST MATCH:",
            "number_of_results": 4,
            "max_length": 100,
            "max_sentences": 4,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1.17,
            "seed": 0,
        },
        "results": [
            {
                "generated_text": "\nI don't feel well today / SENTIMENTS: good, ok, bad / BEST MATCH: bad\nHope everything is alright / SENTIMENTS: good, ok, bad / BEST MATCH: good\nlets go to the store / SENTIMENTS: sick, ok, travel / BEST MATCH: travel\nlets go fishing  / SENTIMENTS: sick, stayput, travel / BEST MATCH: travel\nlets get a haircut  / SENTIMENTS: good, ok, travel / BEST MATCH: good no one will know that I am ill/ SENTMENTS: good, ok, bad / BEST MATCH: good i want to go shopping with my friends/sentiments: bad / best match: good but then again i have nothing to wear feeling unwell/SENTIMETNS: good, bad / BEST MATCH: bad let us play sports  / SENTIMENTS: travel, good, bad / BEST MATCH: bad lets take a look at the weather /",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "\nI don't feel well today / SENTIMENTS: good, ok, bad / BEST MATCH: bad\nHope everything is alright / SENTIMENTS: good, ok, bad / BEST MATCH: good\nlets go to the store / SENTIMENTS: sick, ok, travel / BEST MATCH: travel\nlets go fishing  / SENTIMENTS: sick, stayput, travel / BEST MATCH: travel\nlets get a haircut  / SENTIMENTS: good, ok, travel / BEST MATCH: travel\nsick travel / BEST MATCH: travel no best match for this word. so I will just say travel and leave it at that! 🙂 yes i am feeling sick now... travel/ BEST MATCH: travel sadness not happiness sadness not happiness travel/ BEST MATCH: travel no best match for this word. so I will just say travel and leave it at that!",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "\nI don't feel well today / SENTIMENTS: good, ok, bad / BEST MATCH: bad\nHope everything is alright / SENTIMENTS: good, ok, bad / BEST MATCH: good\nlets go to the store / SENTIMENTS: sick, ok, travel / BEST MATCH: travel\nlets go fishing  / SENTIMENTS: sick, stayput, travel / BEST MATCH: travel\nlets get a haircut  / SENTIMENTS: good, ok, travel / BEST MATCH: travel sick, good, travel / BEST MATCH: travel let's go fishing  / SENTIMENTS: good, travel, rest good, travel, rest / BEST MATCH: travel sick, good, good / BEST MATCH: travel sick, good, travel / BEST MATCH: travel I have no feeling left / SENTIMENTS: good, good, good / BEST MATCH: travel all travel / BEST MATCH: good good, good, good / B",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "\nI don't feel well today / SENTIMENTS: good, ok, bad / BEST MATCH: bad\nHope everything is alright / SENTIMENTS: good, ok, bad / BEST MATCH: good\nlets go to the store / SENTIMENTS: sick, ok, travel / BEST MATCH: travel\nlets go fishing  / SENTIMENTS: sick, stayput, travel / BEST MATCH: travel\nlets get a haircut  / SENTIMENTS: good, ok, travel / BEST MATCH: travel not enough information\n\n\n\n\n\n- health status best match sick or travel illnesses are very common in people who live with hiv/aids. if you have any questions about your own health or that of someone else please ask your doctor before making plans for an activity like this. travel sickness sickness is most likely when traveling by air travel sickness may also occur from moving around too much on land even without traveling headache fever diarrhea stomach upset vomiting flu nausea cold sore sore throat cough sneeze chest congestion",
                "stop_reason": "max_length",
            },
        ],
    },
    "speech-writing": {
        "title": "Speech Writing - Text Generator API",
        "description": "Write a speech - Text Generator API for speech and stand up writing",
        "generate_params": {
            "text": "I say to you today, my friends, so even though we face the difficulties of today and tomorrow",
            "number_of_results": 4,
            "max_length": 100,
            "max_sentences": 4,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1.17,
            "seed": 0,
        },
        "results": [
            {
                "generated_text": "I say to you today, my friends, so even though we face the difficulties of today and tomorrow's problems may not be as great. I still want you to believe in me. I'm here for you if anything ever happens to me because this is who I am: a good person!\" - Tony Robbins' TED Talk about motivation \"When life gives you lemons...make lemonade.\"",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "I say to you today, my friends, so even though we face the difficulties of today and tomorrow, remember that the joys are always more than any difficulty. Happy birthday! You deserve it all.”\nHappy Birthday! I hope this day brings you lots of happiness, success, love, laughter, health, wealth and good fortune.",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "I say to you today, my friends, so even though we face the difficulties of today and tomorrow, let us be happy with what we have now. For the future is uncertain but the present is certain; for the past is gone forever.\nAmen. ~ Thomas Merton, Letter 52 (1955) Happy Days - A Song by Lenny Kravitz: Live in New York City 1981 (Live) (featuring Tom Petty) Happy days are here again And I can feel them all around me You know that I'm right there With you in your arms Wherever life takes me There's no place",
                "stop_reason": "max_length",
            },
            {
                "generated_text": 'I say to you today, my friends, so even though we face the difficulties of today and tomorrow, there is a way forward. There will always be something better than what was before. It just takes faith in ourselves and each other to achieve it. This is our story."',
                "stop_reason": "max_sentences",
            },
        ],
    },
    "legal-writing": {
        "title": "Legal Writing - Text Generator API",
        "description": "Legal Writing - Text Generator API for legal contract writing automation",
        "generate_params": {
            "text": "Nothing in this subpart limits or affects—\n(a)\nany right or",
            "number_of_results": 4,
            "max_length": 100,
            "max_sentences": 4,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1.17,
            "seed": 0,
        },
        "results": [
            {
                "generated_text": "Nothing in this subpart limits or affects—\n(a)\nany right or power of the Commonwealth to enact, amend, repeal or terminate any law; or (b) any constitutional privilege or immunity enjoyed by a member of parliament.”\n\nNo further legislation is required under s. 67(3). The Bill was passed and now sits on the table awaiting Royal assent. A new referendum will be held once the Bill has been signed into law. This means that if Parliament passes another bill regarding the referendum result then there will be no need for a second referendum.",
                "stop_reason": "max_length",
            },
            {
                "generated_text": 'Nothing in this subpart limits or affects—\n(a)\nany right or privilege under the United Nations Convention against Corruption; and (b) any other international agreement, treaty or convention to which Trinidad and Tobago is a party. No law of Trinidad and Tobago shall be inconsistent with this Act. This Act may not affect the rights granted by law to persons who are immune from prosecution under international agreements."  The Criminal Code was amended so as to provide for offences relating to corruption in public office: s. 309 of the Criminal Code now reads: "(1) Whoever eng',
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Nothing in this subpart limits or affects—\n(a)\nany right or power of the Secretary to require a person who is an alien to be registered as provided for by section 101, subsection (c); and [(b) (1) any power under this part to order that a foreign country take reasonable measures against a threat posed by terrorism; or (2)] any authority granted under s. 101 to impose penalties upon persons convicted of terrorist offenses; or (3) any powers under this part to provide for the confiscation of property belonging to terrorists; or (",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Nothing in this subpart limits or affects—\n(a)\nany right or entitlement of the government, as a matter of law; or (b) any right or obligation to pay taxes under federal law. This part does not affect: (c) any interest that may exist between you and another person. [emphasis added] U.S. Code section 101(d)(3). In other words, an employee is entitled to their vacation time if they work on it.",
                "stop_reason": "max_sentences",
            },
        ],
    },
    "medical-writing": {
        "title": "Medical Writing - Text Generator API",
        "description": "Medical Writing - Text Generator API for medical writing automation",
        "generate_params": {
            "text": "A virus is an infectious agent that can only replicate within a host organism. Viruses",
            "number_of_results": 4,
            "max_length": 100,
            "max_sentences": 4,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1.17,
            "seed": 0,
        },
        "results": [
            {
                "generated_text": 'A virus is an infectious agent that can only replicate within a host organism. Viruses do not have their own DNA or RNA and cannot reproduce without infecting another cell, therefore they need to be passed from one cell to the other during infection. A virus causes disease when it replicates in excess of its normal limits, which leads to destruction of tissues, organ function, or death. The term "vaccine" comes from Latin vaccine (meaning small incision), referring to the idea of making tiny cuts on the body to expose areas where viruses could potentially enter through open wounds or mucous',
                "stop_reason": "max_length",
            },
            {
                "generated_text": "A virus is an infectious agent that can only replicate within a host organism. Viruses are not self-replicating organisms, so they do not have the ability to reproduce outside of their hosts. However, some viruses cause illness when they infect other living things and kill them. Some viruses also interfere with normal cell activity inside infected organisms. Other types of microorganisms may enter a human body through injury or open wounds in skin; these pathogens can penetrate into the bloodstream and spread throughout the body.",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": 'A virus is an infectious agent that can only replicate within a host organism. Viruses do not live independently of their hosts, but instead parasitize them and take advantage of the resources they provide to reproduce themselves and spread throughout the population. The word "virus" comes from the Latin verb meaning "to infect" or "infection". In other words, viruses are highly adapted for infection through various modes of transmission.  Infection – An infectious disease is one in which a pathogen, such as a virus, invades a living body (a cell) and replicates itself inside it without',
                "stop_reason": "max_length",
            },
            {
                "generated_text": "A virus is an infectious agent that can only replicate within a host organism. Viruses infect and multiply in the cytoplasm of infected cells, often disrupting their function. The term “viruses” comes from the Latin word vir (meaning “to be strong”) because these are the smallest self-replicating organisms with DNA or RNA as their genetic material. A virus does not have its own cell but replicates inside another living cell. Some viruses cause diseases called viral infections.",
                "stop_reason": "max_sentences",
            },
        ],
    },
    "tweet-writing": {
        "title": "Tweet Writing - Text Generator API",
        "description": "Tweet Writing - Text Generator API for tweet writing automation",
        "generate_params": {
            "text": "Tweet: The best thing about sliced bread is that",
            "number_of_results": 4,
            "max_length": 100,
            "max_sentences": 4,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1.17,
            "seed": 0,
        },
        "results": [
            {
                "generated_text": "Tweet: The best thing about sliced bread is that it comes with the crust. Cut up some cheese, cucumbers and onion slices into small pieces for a quick lunch or dinner side dish. Get out your favorite condiments and enjoy! Add a little salt and pepper to taste and you’re all set!",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "Tweet: The best thing about sliced bread is that you can use it to make a sandwich or burger with any kind of meat. It also goes great with fruit, cheese and tomato on the side. This recipe will give you 8 servings of delicious sandwiches! #BBQSandwiches #sandwich #healthy Sandwich made from whole wheat bread instead of white bread for a healthier option.",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "Tweet: The best thing about sliced bread is that it doesn't last long. Just think, the first slice you get will taste better than any of the rest. So don't be afraid to enjoy a good slice with your coffee or tea! Here are some ideas for how to eat it:  Eat a whole piece at one time and try not to bite into each side as if cutting them.",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "Tweet: The best thing about sliced bread is that it makes a perfect appetizer. You can serve them with cheese, tomato sauce or just eat them plain and enjoy the crunchy texture of the slices. Here are some great ideas for how to use your leftover bread from dinner last night! #lefthandwichesforsale #cheeseyrolls #tacoswithbread #pastaandbread Sandwiches: Make sandwiches using whatever you have on hand like tuna salad, pepperoni, bacon, etc.",
                "stop_reason": "max_sentences",
            },
        ],
    },
    "linkedin-writing": {
        "title": "Linkedin Writing - Text Generator API",
        "description": "Linkedin Writing - Text Generator API for linkedin writing automation",
        "generate_params": {
            "text": "Hello, I am a software engineer and I am looking for a job in the",
            "number_of_results": 4,
            "max_length": 100,
            "max_sentences": 4,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1.17,
            "seed": 0,
        },
        "results": [
            {
                "generated_text": "Hello, I am a software engineer and I am looking for a job in the field of software development. I have 5 years experience as a developer. So if you are interested please contact me at [email protected]. Thanks!",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "Hello, I am a software engineer and I am looking for a job in the area of data science. I have recently finished my bachelor degree and currently work as a junior developer at an IT company. If you are hiring people for the position mentioned on this page please feel free to contact me. Thanks!",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "Hello, I am a software engineer and I am looking for a job in the industry. My major is computer science with emphasis on machine learning & AI. I've worked as an IT professional since my graduation from university.\nI would like to work at Google or Apple company where they have a strong focus on technology development.",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "Hello, I am a software engineer and I am looking for a job in the technology sector. Where can I find more information about open positions? www.helsinki.fi/en/employment/innovative-technology-in-helsinki/salary-and-skills-offers-undergraduate-university-degree-programs-in-innovative-techno.html?lang=en#programs-by-category\nwww.helsinki.fi/online-recruiting - university of helsinki online recruitment system. Please be aware that this is only available",
                "stop_reason": "max_length",
            },
        ],
    },
    "assignment-writing": {
        "title": "Assignment Writing - Text Generator API",
        "description": "Assignment Writing - Text Generator API for help writing assignments",
        "generate_params": {
            "text": "The Tragedy of Macbeth is a play by William Shakespeare about a",
            "number_of_results": 4,
            "max_length": 100,
            "max_sentences": 4,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1.17,
            "seed": 0,
        },
        "results": [
            {
                "generated_text": "The Tragedy of Macbeth is a play by William Shakespeare about an Englishman who, in 1040, led a group of men to kill Malcolm II. It was first performed at the Globe Theatre on 4 January 1593 and later moved to other venues including London's Haymarket Theatre and Southwark Playhouse. The original production closed after only nine performances when it ran out of money. In 2005, the National Trust announced that they would buy the theatre for £1 and reopen it as part of their plans to restore historic buildings with the aim of preserving them and making",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "The Tragedy of Macbeth is a play by William Shakespeare about a king who commits murder and other atrocities. The play was first performed in 1606, although it has been argued that the plot is based on earlier events involving Macbeth's ancestor Macduff.It tells the story of Macbeth from his birth to his death: an early life as a servant boy growing up under a brutal master until he becomes one of the most powerful men in Scotland. However, when Macbeth dies at the hands of Macduff (the murderer), Macbeth's son",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "The Tragedy of Macbeth is a play by William Shakespeare about a man who commits murder. The play was written in 1599 and first performed on 1 March 1602 at the Globe theatre, London. It tells the story of the murderous king Banquo's attempt to kill his son Malcolm after he becomes involved with Macduff's daughter Macbeth. It concludes that Macbeth's own fate ultimately leads him down to his doom.",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "The Tragedy of Macbeth is a play by William Shakespeare about a Scottish nobleman, Banquo. The tragedy tells the story of his murder by Macduff and his son Malcolm. It was first performed in 1599. This page describes the plot summary only.",
                "stop_reason": "max_sentences",
            },
        ],
    },
    "educational-writing": {
        "title": "Educational Writing - Text Generator API",
        "description": "Educational Writing - Text Generator API for writing education",
        "generate_params": {
            "text": "The most important things we will cover this lesson are the",
            "number_of_results": 4,
            "max_length": 100,
            "max_sentences": 4,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1.17,
            "seed": 0,
        },
        "results": [
            {
                "generated_text": "The most important things we will cover this lesson are the following: 1. The importance of making a decision to create 2. How to make a decision 3. How you can use your decisions as feedback for yourself and others 4.",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "The most important things we will cover this lesson are the concepts of speed, time and distance. We will also use these to calculate velocity. The following diagram shows how a car moves from point A to B with constant velocity: Point A - Point B = Speed × Time (A-B) Distance The equation below is used when an object travels at different speeds along its path. It takes into account both direction and speed as well as their product together.",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "The most important things we will cover this lesson are the following: 1. The importance of water to living organisms 2. Water is a solvent 3. We need water for survival 4.",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "The most important things we will cover this lesson are the importance of good sleep and a healthy diet. For example, if you feel tired all day long it can be due to lack of sleep or eating poorly. We have already covered some information about these topics in previous lessons so now let's continue with more details. To start learning about nutrition, we'll look at what foods make us sleep well.",
                "stop_reason": "max_sentences",
            },
        ],
    },
    "mandarin-chinese-writing": {
        "title": "Mandarin Writing - Text Generator API",
        "description": "Mandarin Writing - Text Generator API for mandarin writing automation",
        "generate_params": {
            "text": "嘿，我希望我们能见面",
            "number_of_results": 4,
            "max_length": 100,
            "max_sentences": 4,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1.17,
            "seed": 0,
        },
        "results": [
            {
                "generated_text": "嘿，我希望我们能见面 tomorrow, okay? I hope we can meet tomorrow. Okay? Yes!",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "嘿，我希望我们能见面 tomorrow morning. I hope that we can meet tomorrow morning. = I want to see you tomorrow morning. Yes, I do!",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "嘿，我希望我们能见面 again.I hope we can meet again someday soon. - Bye! See ya! Hope to see you again.",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "嘿，我希望我们能见面 in the future. Maybe we could go for a drive or something? I hope so! See you soon, bye!",
                "stop_reason": "max_sentences",
            },
        ],
    },
    "hindi-writing": {
        "title": "Hindi Writing - Text Generator API",
        "description": "Hindi Writing - Text Generator API for generating writing in hindi",
        "generate_params": {
            "text": "अरे मुझे उम्मीद है कि हम मिल सकते हैं",
            "number_of_results": 4,
            "max_length": 100,
            "max_sentences": 4,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1.17,
            "seed": 0,
        },
        "results": [
            {
                "generated_text": "अरे मुझे उम्मीद है कि हम मिल सकते हैं again soon! Have a great day. 🙂 xo, Aimee xoxo <3\nLove you so much ❤ <3 xxooo <3 xxx <3 <3 <3 <3 <3 <3 <3 <3 <3 <3 <3 <3 <3 <3 <3 <3 <3 <3 <3 <3 <3 <3 <3 <3 <3 <3 <3 <3 <3 <3 <3 <3 <",
                "stop_reason": "max_length",
            },
            {
                "generated_text": 'अरे मुझे उम्मीद है कि हम मिल सकते हैं tomorrow. I hope we can meet tomorrow." she said earnestly. "Soon, soon."',
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "अरे मुझे उम्मीद है कि हम मिल सकते हैं again sometime soon. I hope we can meet up again someday soon! 🙂 <3 love u xoxo <333 ♥️😘💋😍🐾❤️❤️❤️❤️❤️❤️❤️❤️❤️❤️❤️❤️❤️❤️❤️❤️❤️❤️❤️❤️ �",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "अरे मुझे उम्मीद है कि हम मिल सकते हैं one day soon. I hope we can meet again someday soon. <3 ~~> ♥️ ♥️ ♥️ ♥️ ♡♡♡♡♡♡♡♡♡♡♡♡♡♡♡♡♡♡♡♡♡♡♡♡♡♡♡♡♡♡♡♡♡♡�",
                "stop_reason": "max_length",
            },
        ],
    },
    "punjabi-writing": {
        "title": "Punjabi Writing - Text Generator API",
        "description": "Punjabi Writing - Text Generator API for generating writing in punjabi",
        "generate_params": {
            "text": "ਹੇ ਮੈਨੂੰ ਉਮੀਦ ਹੈ ਕਿ ਅਸੀਂ ਮਿਲ ਸਕਦੇ ਹਾਂ",
            "number_of_results": 4,
            "max_length": 100,
            "max_sentences": 4,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1.17,
            "seed": 0,
        },
        "results": [
            {
                "generated_text": 'ਹੇ ਮੈਨੂੰ ਉਮੀਦ ਹੈ ਕਿ ਅਸੀਂ ਮਿਲ ਸਕਦੇ ਹਾਂ with someone who is just like you, a person that has your eyes and smile. I think we are going to have fun together! I want to go out in the evening and play games at my house! You can come over if you wish!"',
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "ਹੇ ਮੈਨੂੰ ਉਮੀਦ ਹੈ ਕਿ ਅਸੀਂ ਮਿਲ ਸਕਦੇ ਹਾਂ soon. I hope to meet you soon. <3 xoxo ~<333 ♥♡♡♡♡♡♡♡♡♡♡♡♡♡♡♡♡♡♡♡♡♡♡♡♡♡♡♡♡♡♡♡♡♡♡♡♡♡♡♡♡♡",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "ਹੇ ਮੈਨੂੰ ਉਮੀਦ ਹੈ ਕਿ ਅਸੀਂ ਮਿਲ ਸਕਦੇ ਹਾਂ. I look forward to meeting you soon. Hopefully, we will meet again soon! Yes, I'd like to speak with someone about the property.",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "ਹੇ ਮੈਨੂੰ ਉਮੀਦ ਹੈ ਕਿ ਅਸੀਂ ਮਿਲ ਸਕਦੇ ਹਾਂ in the same boat. i am sure we can find some common ground. I hope so. i think it will be nice to see how well we get along as a team, and that's what i'm hoping for here.\"",
                "stop_reason": "max_sentences",
            },
        ],
    },
    "portugese-writing": {
        "title": "Portuguese Writing - Text Generator API",
        "description": "Portuguese Writing - Text Generator API for generating writing in portugese",
        "generate_params": {
            "text": "ei, eu espero que possamos nos encontrar",
            "number_of_results": 4,
            "max_length": 100,
            "max_sentences": 4,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1.17,
            "seed": 0,
        },
        "results": [
            {
                "generated_text": "ei, eu espero que possamos nos encontrar de novo.I hope we can meet again soon. Bye!Goodbye!Bye! ~~^____^~~*O* (: x *x *x *x *o*)*Xx *x *x *x *o*)*O* ^_____^~~*O* (: x *x *x *x *o*)*Xx *x *x *x *o*)*O* <3 (: x *x *",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "ei, eu espero que possamos nos encontrar again sometime soon. I hope to see you around some time soon! 😉 <3 xoxo! ♥️<3 xoxo!",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "ei, eu espero que possamos nos encontrar. i wish we could meet again! hehehehe.... thanks for reading :) xoxo <3 bjssss e um ótimo dia! beijos =*<:)*<:3** <3\nIaraa *_* Obrigada pelo comentário... Fico feliz em saber que gostou do post!",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "ei, eu espero que possamos nos encontrar. I am looking forward to meeting you again. See ya! Bye bye!",
                "stop_reason": "max_sentences",
            },
        ],
    },
    "greek-writing": {
        "title": "Greek Writing - Text Generator API",
        "description": "Greek Writing - Text Generator API for generating writing in greek",
        "generate_params": {
            "text": "γεια, ελπίζω να μπορέσουμε να συναντηθούμε",
            "number_of_results": 4,
            "max_length": 100,
            "max_sentences": 4,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1.17,
            "seed": 0,
        },
        "results": [
            {
                "generated_text": "γεια, ελπίζω να μπορέσουμε να συναντηθούμε our problems by taking advantage of the natural resources we have. So let's use our knowledge to benefit all people in a sustainable way and make good use of our environment! The earth is full of great beauty but at the same time very fragile so let's respect it as much as possible! If you want more information about this topic or even if you're interested in joining us in Greece for some activities, contact us via email [email protected] or call us on +44 (0)20 7284 2870.",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "γεια, ελπίζω να μπορέσουμε να συναντηθούμε. If we could just get a hold of your boss' number... thank you very much. Yes sir!\" And so they did.",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": 'γεια, ελπίζω να μπορέσουμε να συναντηθούμε. So I guess we can conclude that we agree to disagree." No, I\'m not going to say that. "I\'m just going to disagree with you."',
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "γεια, ελπίζω να μπορέσουμε να συναντηθούμε our activities. There is no other way to do that than by taking into account the actions of others. This means we must be willing and able to understand and accept responsibility for what people around us are doing as well as ourselves. We can only act with a sense of community when this happens.",
                "stop_reason": "max_sentences",
            },
        ],
    },
    "french-writing": {
        "title": "French Writing - Text Generator API",
        "description": "French Writing - Text Generator API for generating writing in french",
        "generate_params": {
            "text": "Hé j'espère que nous pourrons nous rencontrer",
            "number_of_results": 4,
            "max_length": 100,
            "max_sentences": 4,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1.17,
            "seed": 0,
        },
        "results": [
            {
                "generated_text": "Hé j'espère que nous pourrons nous rencontrer et discuter de votre workload and other things. I hope we can meet up to discuss your work load and other issues. Thanks for being open with me! <3<3\nThank you so much for being open with me, it was very kind of you.",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "Hé j'espère que nous pourrons nous rencontrer à nouveau. I'm hoping to see you again soon. <3 <3 <3 <3 <3 ♥️♥️♥️<333 I hope we meet up again! xoxo <33 <3333<333 <333<33 <3 xxxooo Love, xo ❤️ <3 ❤️ xx ♡ <3 <3 <3 <3 <3 <3 <3 <3 <3 <3 <3 <3 <3 <3 <3",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Hé j'espère que nous pourrons nous rencontrer, parce qu'il est possible que je doive leave the country soon. I'd like to meet up with you and talk about it all! See ya when I get back. Bye bye!",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "Hé j'espère que nous pourrons nous rencontrer en personne au prochain festival de jazz. I hope that we can meet up in person at the next jazz festival! 🎸🌺❤️☀️😍💃🏼\nI love you so much, my beautiful friend ❤️💗 You’re amazing and unique! Have a great day!",
                "stop_reason": "max_sentences",
            },
        ],
    },
    "arabic-writing": {
        "title": "Arabic Writing - Text Generator API",
        "description": "Arabic Writing - Text Generator API for generating writing in arabic",
        "generate_params": {
            "text": "مرحباً ، آمل أن نلتقي",
            "number_of_results": 4,
            "max_length": 100,
            "max_sentences": 4,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1.17,
            "seed": 0,
        },
        "results": [
            {
                "generated_text": "مرحباً ، آمل أن نلتقي again soon. Bye bye! Goodbye! See you later!",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "مرحباً ، آمل أن نلتقي again soon! ¡Hola, espero verte de nuevo pronto! =) 😊✌️☺️😘❤️🙏🏾💜💚 👋🏽💖💗💓⚡️🥳☮️💝💞💯💕\n¡Espero que nos veamos pronto, hasta luego! ❤️ ¡Buenas noches y buenas vibras!",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "مرحباً ، آمل أن نلتقي again soon. Take care! Bye bye! Goodbye!",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "مرحباً ، آمل أن نلتقي again. Bye, hope to meet you soon! Goodbye! See ya later, see you soon!",
                "stop_reason": "max_sentences",
            },
        ],
    },
    "russian-writing": {
        "title": "Russian Writing - Text Generator API",
        "description": "Russian Writing - Text Generator API for generating writing in russian",
        "generate_params": {
            "text": "Привет, я надеюсь, мы сможем встретиться",
            "number_of_results": 4,
            "max_length": 100,
            "max_sentences": 4,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1.17,
            "seed": 0,
        },
        "results": [
            {
                "generated_text": "Привет, я надеюсь, мы сможем встретиться at the next conference. I hope we can meet up at the next conference. - Yes! Yes!",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "Привет, я надеюсь, мы сможем встретиться. Bye-bye! Goodbye. Have a nice day!",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "Привет, я надеюсь, мы сможем встретиться soon! ¡Hola! Espero poder verte pronto. 🙂 Bye bye!",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "Привет, я надеюсь, мы сможем встретиться soon. bye byes! xo mya shawla lynn smithsville ohio usa michelle smithsville ohio usa hello, we are from michelle and her son's school in smithsville, ohio. our son is also named mya as well.",
                "stop_reason": "max_sentences",
            },
        ],
    },
    "indonesian-writing": {
        "title": "Indonesian Writing - Text Generator API",
        "description": "Indonesian Writing - Flexible Text Generator API for generating writing in indonesian",
        "generate_params": {
            "text": "Привет, я надеюсь, мы сможем встретиться",
            "number_of_results": 4,
            "max_length": 100,
            "max_sentences": 4,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1.17,
            "seed": 0,
        },
        "results": [
            {
                "generated_text": "Привет, я надеюсь, мы сможем встретиться in the club tonight. i'll try to get there at 7:30 sharp, see you then! bye <3\nSophie 💖💕<3 I hope so too 😊❤️👍😘😙💋\nI will be seeing her around 8:30 PM. She is going for a walk with friends and she should arrive home before me.",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "Привет, я надеюсь, мы сможем встретиться soon. bye! see you soon! goodbye!",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "Привет, я надеюсь, мы сможем встретиться soon. I hope to see you again soon! 🙂 <3 xxx xoxo ❤️ <3 hugs ♥️ bye! ❤️ love you <3\nKisses and hugs:) Goodbye: (Love you:) Love you so much!",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "Привет, я надеюсь, мы сможем встретиться again soon. Take care and thanks for the lovely comments! 🙂 <3 xo Lena ❤️ xo xoxo Lena xxx Lena xx Lena xxxx xxxxxx Lena xxx xxx xxx Lena xxx xxx xxx xx xx Lena xxx xxx xxx xxx Lena xxx xxx xxx xxx Lena xxx xxx xxx xxx Lena xxx xxx xxx xxx Lena xxx xxx xxx xxx Lena xxx xxx xxx xxx Lena xxx xxx xxx xxx Lena xxx xxx xxx xxx Lena xxx xxx xxx xxx Lena xxx xxx xxx xxx Lena xxx xxx xxx xxx",
                "stop_reason": "max_length",
            },
        ],
    },
    "top-10-women": {
        "title": "Top 10 Women - Text Generator API",
        "description": "Text Generator API for generating writing about top 10 women in history",
        "generate_params": {
            "text": "Top 10 most important women in human history, and their greatest achievements:\n",
            "number_of_results": 4,
            "max_length": 100,
            "max_sentences": 4,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1.17,
            "seed": 0,
        },
        "results": [
            {
                "generated_text": "Top 10 most important women in human history, and their greatest achievements:\n1. Maya Angelou 2. Florence Nightingale 3. Mary Shelley 4.",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "Top 10 most important women in human history, and their greatest achievements:\n10. Mary (mother of Jesus) - mother of Jesus Christ, the Son of God 11. Mother Teresa of Calcutta 12. Mère Térésa de l'enfant Jésus 13.",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "Top 10 most important women in human history, and their greatest achievements:\nWomen have been instrumental to the development of humanity. They have worked hard to improve society by raising families, educating children, caring for sick people, fighting wars, improving health care, building houses, transporting goods and more! Women have made significant contributions throughout history which have left a lasting impact on our world. Here is a list of some of the biggest accomplishments that these remarkable women have achieved over time.",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "Top 10 most important women in human history, and their greatest achievements:\n1. Mary (mother of Jesus) - Mother of Christ 2. Queen Victoria 3. Simone Veil 4.",
                "stop_reason": "max_sentences",
            },
        ],
    },
    "email-writing": {
        "title": "Email writing - Text Generator API",
        "description": "Text Generator API for generating writing emails and getting work done",
        "generate_params": {
            "text": "The following email explains two things:\n1) The writer, Andy, is going to miss work.\n2) The receiver, Betty, is Andy's boss and can email if anything needs to be done.\n\nFrom: ",
            "number_of_results": 4,
            "max_length": 100,
            "max_sentences": 4,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1.17,
            "seed": 0,
        },
        "results": [
            {
                "generated_text": "The following email explains two things:\n1) The writer, Andy, is going to miss work.\n2) The receiver, Betty, is Andy's boss and can email if anything needs to be done.\n\nFrom: Andy <andrew@email.com> To: Betty <betty@email.com> Goodbye! I will be absent from work tomorrow. Thanks for your help. Andy.",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "The following email explains two things:\n1) The writer, Andy, is going to miss work.\n2) The receiver, Betty, is Andy's boss and can email if anything needs to be done.\n\nFrom: Andy To: Betty <andrew.b@gmail.com> Andy will not be able to attend the meeting as he has an appointment with a doctor today. Hopefully I won't have any problems attending. Thanks! Yes, it was very nice of you to ask.",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "The following email explains two things:\n1) The writer, Andy, is going to miss work.\n2) The receiver, Betty, is Andy's boss and can email if anything needs to be done.\n\nFrom: Andy To: Betty Your boss. Thanks for letting me know. I'll be leaving tomorrow. Bye!",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "The following email explains two things:\n1) The writer, Andy, is going to miss work.\n2) The receiver, Betty, is Andy's boss and can email if anything needs to be done.\n\nFrom: Andy (Andy@company.com)  To: Betty  (bety@company.com)  Subject: I will be out for the next few days Thanks! I'm sorry this won't work but my sister has an emergency and I'd like to get some help with it. Sorry about that. If you have any questions or concerns please don't hesitate to contact me through e-mail or phone.",
                "stop_reason": "max_sentences",
            },
        ],
    },
    "company-classification": {
        "title": "Company classification - Text Generator API",
        "description": "Text Generator API Company classification API examples - company industry and sector classification",
        "generate_params": {
            "text": "The following is a list of companies and the categories they fall into\n\nFacebook: Social media, Technology\nUber: Transportation, Technology, Marketplace\nMcdonalds: Food, Fast Food, Logistics, Restaurants\n{example}:",
            "number_of_results": 4,
            "max_length": 100,
            "max_sentences": 4,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1.17,
            "seed": 0,
        },
        "results": [
            {
                "generated_text": 'The following is a list of companies and the categories they fall into\n\nFacebook: Social media, Technology\nUber: Transportation, Technology, Marketplace\nMcdonalds: Food, Fast Food, Logistics, Restaurants\n{example}: Twitter is a social network site that allows users to send text messages or updates known as "tweets". Science and technology company. Business category: Science and technology business category (disambiguation) Facebook has been called a tech start-up while Apple was not considered so. Business category: Business organization tech start-up Business organization tech start-up Business organization tech start-up Business organization tech start-up Business organization tech start-up Business organization tech start-up Business organization tech start-up Business organization tech start-up Business organization tech start-up Business organization tech start-up Business organization tech start-up',
                "stop_reason": "max_length",
            },
            {
                "generated_text": "The following is a list of companies and the categories they fall into\n\nFacebook: Social media, Technology\nUber: Transportation, Technology, Marketplace\nMcdonalds: Food, Fast Food, Logistics, Restaurants\n{example}: Uber was classified under both Businesses & Services category as well as Tech. tech is technology so that makes sense for it to be in tech but business is also very relevant. Businesses & Services category is not just about tech so there are other factors involved. There are no companies in the Sports category.",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "The following is a list of companies and the categories they fall into\n\nFacebook: Social media, Technology\nUber: Transportation, Technology, Marketplace\nMcdonalds: Food, Fast Food, Logistics, Restaurants\n{example}: Amazon Web Services - Science and technology company Amazon is an online retailer. Businesses can sell their products on the website or use it to host websites for customers. Company Description Science and technology company Amazon is an online retailer. Businesses can sell their products on the website or use it to host websites for customers.",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "The following is a list of companies and the categories they fall into\n\nFacebook: Social media, Technology\nUber: Transportation, Technology, Marketplace\nMcdonalds: Food, Fast Food, Logistics, Restaurants\n{example}: McDonalds is an example of restaurants.com. Fast food restaurant category. Businesses are categorized by industry. They can also be classified according to their size or location.",
                "stop_reason": "max_sentences",
            },
        ],
    },
    "alliteration-generator": {
        "title": "Alliteration Generator - Text Generator API",
        "description": "Text Generator API Alliteration prompt API examples - creativity and alliterations examples",
        "generate_params": {
            "text": "Find synonyms for words that can create alliterations.\n\nSentence: The dog went to the store.\nAlliteration: The dog drove to the department.\n\nSentence: David wears a hat everyday.\nAlliteration: David dons a derby daily.\n\nSentence: The soap dries over night.\nAlliteration: The soap shrivels succeeding sunset.\n\nSentence: Sal throws shells over the water at the beach.\nAlliteration:",
            "number_of_results": 4,
            "max_length": 100,
            "max_sentences": 4,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1.17,
            "seed": 0,
        },
        "results": [
            {
                "generated_text": "Find synonyms for words that can create alliterations.\n\nSentence: The dog went to the store.\nAlliteration: The dog drove to the department.\n\nSentence: David wears a hat everyday.\nAlliteration: David dons a derby daily.\n\nSentence: The soap dries over night.\nAlliteration: The soap shrivels succeeding sunset.\n\nSentence: Sal throws shells over the water at the beach.\nAlliteration: Sal hurls shells on shore following sunrise. Yes! No! No!",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "Find synonyms for words that can create alliterations.\n\nSentence: The dog went to the store.\nAlliteration: The dog drove to the department.\n\nSentence: David wears a hat everyday.\nAlliteration: David dons a derby daily.\n\nSentence: The soap dries over night.\nAlliteration: The soap shrivels succeeding sunset.\n\nSentence: Sal throws shells over the water at the beach.\nAlliteration: Sal tosses shellfish over sea. Yes, yes, yes, yes, yes! No, no, no, no, no, no! No, no, no, no, no, no!",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "Find synonyms for words that can create alliterations.\n\nSentence: The dog went to the store.\nAlliteration: The dog drove to the department.\n\nSentence: David wears a hat everyday.\nAlliteration: David dons a derby daily.\n\nSentence: The soap dries over night.\nAlliteration: The soap shrivels succeeding sunset.\n\nSentence: Sal throws shells over the water at the beach.\nAlliteration: Sal tosses shellfish over the sea. Yes, yes and no No, no and no No, no and no Yes, yes and no Yes, yes and no Yes, yes and no Yes, no and no Yes, no and no Yes, no and no Yes, no and no Yes, no and no Yes, no and no Yes, no and no Yes, no and no Yes, no and no Yes, no and no Yes, no and no Yes, no and no Yes,",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Find synonyms for words that can create alliterations.\n\nSentence: The dog went to the store.\nAlliteration: The dog drove to the department.\n\nSentence: David wears a hat everyday.\nAlliteration: David dons a derby daily.\n\nSentence: The soap dries over night.\nAlliteration: The soap shrivels succeeding sunset.\n\nSentence: Sal throws shells over the water at the beach.\nAlliteration: Sal drives shells across the sea. Yes, alliteration is a literary device that creates sound repetition of certain letters in a word or phrase. Alliterations are often used as an effective way to describe movement and action (like walking), but they also have other uses. They make reading more interesting, because you get caught up in trying to figure out what might be coming next.",
                "stop_reason": "max_sentences",
            },
        ],
    },
    "song-generator": {
        "title": "Song Generator - Text Generator API",
        "description": "Song Generator API - musical lyrics prompt API examples - music generator",
        "generate_params": {
            "text": "VERSE:\nAlas my love,\nYou do me wrong,\nTo cast me off discourteously,\nfor i have loved you so long,\ndelighting in your company.\n\nCHORDS:\nAlas[Am] my[C] love,\nyou [G]do [Em]me wrong,\nto [Am]cast me off dis[E]courteously,\nfor [Am]i have[C] loved[G] you [Em]so long,\nde[Am]lighting in[E7] your [Am]company.\n\nVERSE:\n",
            "number_of_results": 4,
            "max_length": 100,
            "max_sentences": 4,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1.17,
            "seed": 0,
        },
        "results": [
            {
                "generated_text": "VERSE:\nAlas my love,\nYou do me wrong,\nTo cast me off discourteously,\nfor i have loved you so long,\ndelighting in your company.\n\nCHORDS:\nAlas[Am] my[C] love,\nyou [G]do [Em]me wrong,\nto [Am]cast me off dis[E]courteously,\nfor [Am]i have[C] loved[G] you [Em]so long,\nde[Am]lighting in[E7] your [Am]company.\n\nVERSE:\nNow I am weary of the world, my soul's desire is gone, and for all that i've done to you.I hate myself for it. CHORDS: Alas, alas, alas, my love,my heart has been made sick by what you've said,oh! I'm ashamed of what I've done to you. ALAS: Now I am weary of the world, my soul's desire is gone,and for all that I've done to you.I hate myself for it.",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "VERSE:\nAlas my love,\nYou do me wrong,\nTo cast me off discourteously,\nfor i have loved you so long,\ndelighting in your company.\n\nCHORDS:\nAlas[Am] my[C] love,\nyou [G]do [Em]me wrong,\nto [Am]cast me off dis[E]courteously,\nfor [Am]i have[C] loved[G] you [Em]so long,\nde[Am]lighting in[E7] your [Am]company.\n\nVERSE:\nO wretched woman! alas, o woeful heart!\nO unhappy lover! if you had but known it then!\n",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "VERSE:\nAlas my love,\nYou do me wrong,\nTo cast me off discourteously,\nfor i have loved you so long,\ndelighting in your company.\n\nCHORDS:\nAlas[Am] my[C] love,\nyou [G]do [Em]me wrong,\nto [Am]cast me off dis[E]courteously,\nfor [Am]i have[C] loved[G] you [Em]so long,\nde[Am]lighting in[E7] your [Am]company.\n\nVERSE:\nAlas, alas my love. I am left all alone to mourn and weep for thee, for i have loved you so long. Chorus: Oh! O!",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "VERSE:\nAlas my love,\nYou do me wrong,\nTo cast me off discourteously,\nfor i have loved you so long,\ndelighting in your company.\n\nCHORDS:\nAlas[Am] my[C] love,\nyou [G]do [Em]me wrong,\nto [Am]cast me off dis[E]courteously,\nfor [Am]i have[C] loved[G] you [Em]so long,\nde[Am]lighting in[E7] your [Am]company.\n\nVERSE:\nO my darling, take pity on me!\n\n\nEND OF A CANTATA FOR SINGERS AND ORGAN. [Am]O my darling, take p[A]ymyon m[A]me!\n\n\n\n(D)Amen.",
                "stop_reason": "max_sentences",
            },
        ],
    },
    "book-review-generator": {
        "title": "Book Review Generator - Text Generator API",
        "description": "Book Review Generator API - musical lyrics prompt API examples - book review generator",
        "generate_params": {
            "text": 'Title: Lovely War\nRating: 3/5\nQuotes:\n- "It was time for James and Hazel to get properly acquainted. Time to see if the magic of music and moonlight and graceful movement were all that they had shared, or if a grimy gray London dawn and a cheap cup of coffee could make them feel the same way."\n- "Annihilation has its own je ne sais quoi. We’re all guilty of it. So spare me the sermons."\n- "His mother’s letters are full of urgent warning. She grew up in Mississippi. \nShe knows about lynching. Aubrey wonders if he’ll die in his country before he \never gets the chance to die for his country. Either way, he’d rather not."\n- "Whatever boost sixty captured miles might have brought to German morale was \nerased by the chocolate in the BEF’s packs. War is morale. War is supply. War is \nchocolate."\nThoughts:\n- Pacing felt awkward\n- WW1 history felt accurate\n- Didn\'t care too much for the story of the Gods\nReview: A good book with well rounded characters, but the pacing felt super \nawkward. The titles of the chapters showed which Greek God was speaking, but I was more interested in the WW1 tales than their relationships.\n\n\'\'\'\nTitle: Goodbye, Things\nRating: 4/5\nThoughts:\n- very cleanly written\n- read easily\n- author did good research\nReview:',
            "number_of_results": 4,
            "max_length": 100,
            "max_sentences": 4,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1.17,
            "seed": 0,
        },
        "results": [
            {
                "generated_text": 'Title: Lovely War\nRating: 3/5\nQuotes:\n- "It was time for James and Hazel to get properly acquainted. Time to see if the magic of music and moonlight and graceful movement were all that they had shared, or if a grimy gray London dawn and a cheap cup of coffee could make them feel the same way."\n- "Annihilation has its own je ne sais quoi. We’re all guilty of it. So spare me the sermons."\n- "His mother’s letters are full of urgent warning. She grew up in Mississippi. \nShe knows about lynching. Aubrey wonders if he’ll die in his country before he \never gets the chance to die for his country. Either way, he’d rather not."\n- "Whatever boost sixty captured miles might have brought to German morale was \nerased by the chocolate in the BEF’s packs. War is morale. War is supply. War is \nchocolate."\nThoughts:\n- Pacing felt awkward\n- WW1 history felt accurate\n- Didn\'t care too much for the story of the Gods\nReview: A good book with well rounded characters, but the pacing felt super \nawkward. The titles of the chapters showed which Greek God was speaking, but I was more interested in the WW1 tales than their relationships.\n\n\'\'\'\nTitle: Goodbye, Things\nRating: 4/5\nThoughts:\n- very cleanly written\n- read easily\n- author did good research\nReview: very cleanly written and interesting, but a little slow. The title page intrigued me so that made this one go on my list. I\'d recommend reading first novel from the series. 4 stars\' worth of interest.',
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": 'Title: Lovely War\nRating: 3/5\nQuotes:\n- "It was time for James and Hazel to get properly acquainted. Time to see if the magic of music and moonlight and graceful movement were all that they had shared, or if a grimy gray London dawn and a cheap cup of coffee could make them feel the same way."\n- "Annihilation has its own je ne sais quoi. We’re all guilty of it. So spare me the sermons."\n- "His mother’s letters are full of urgent warning. She grew up in Mississippi. \nShe knows about lynching. Aubrey wonders if he’ll die in his country before he \never gets the chance to die for his country. Either way, he’d rather not."\n- "Whatever boost sixty captured miles might have brought to German morale was \nerased by the chocolate in the BEF’s packs. War is morale. War is supply. War is \nchocolate."\nThoughts:\n- Pacing felt awkward\n- WW1 history felt accurate\n- Didn\'t care too much for the story of the Gods\nReview: A good book with well rounded characters, but the pacing felt super \nawkward. The titles of the chapters showed which Greek God was speaking, but I was more interested in the WW1 tales than their relationships.\n\n\'\'\'\nTitle: Goodbye, Things\nRating: 4/5\nThoughts:\n- very cleanly written\n- read easily\n- author did good research\nReview: Very cleanly written and easy to follow. It really does show how things can change when you move from one place to another. Would recommend this book. 5 stars.',
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "Title: Lovely War\nRating: 3/5\nQuotes:\n- \"It was time for James and Hazel to get properly acquainted. Time to see if the magic of music and moonlight and graceful movement were all that they had shared, or if a grimy gray London dawn and a cheap cup of coffee could make them feel the same way.\"\n- \"Annihilation has its own je ne sais quoi. We’re all guilty of it. So spare me the sermons.\"\n- \"His mother’s letters are full of urgent warning. She grew up in Mississippi. \nShe knows about lynching. Aubrey wonders if he’ll die in his country before he \never gets the chance to die for his country. Either way, he’d rather not.\"\n- \"Whatever boost sixty captured miles might have brought to German morale was \nerased by the chocolate in the BEF’s packs. War is morale. War is supply. War is \nchocolate.\"\nThoughts:\n- Pacing felt awkward\n- WW1 history felt accurate\n- Didn't care too much for the story of the Gods\nReview: A good book with well rounded characters, but the pacing felt super \nawkward. The titles of the chapters showed which Greek God was speaking, but I was more interested in the WW1 tales than their relationships.\n\n'''\nTitle: Goodbye, Things\nRating: 4/5\nThoughts:\n- very cleanly written\n- read easily\n- author did good research\nReview: Very cleanly written, easy to follow and interesting plot that moved along at a steady pace. This would be an excellent book to pass on as part of your class or library collection! 5 stars\r\n'goodreads' reviewer'verycleanlywritten' liked this book'readeasily' loved it author's background made reading soothing 'didgoodresearch' enjoyed how she wrote about her family'sensationalismandtheodds 'couldnotgetover' 3 stars didn't like the hero",
                "stop_reason": "max_length",
            },
            {
                "generated_text": 'Title: Lovely War\nRating: 3/5\nQuotes:\n- "It was time for James and Hazel to get properly acquainted. Time to see if the magic of music and moonlight and graceful movement were all that they had shared, or if a grimy gray London dawn and a cheap cup of coffee could make them feel the same way."\n- "Annihilation has its own je ne sais quoi. We’re all guilty of it. So spare me the sermons."\n- "His mother’s letters are full of urgent warning. She grew up in Mississippi. \nShe knows about lynching. Aubrey wonders if he’ll die in his country before he \never gets the chance to die for his country. Either way, he’d rather not."\n- "Whatever boost sixty captured miles might have brought to German morale was \nerased by the chocolate in the BEF’s packs. War is morale. War is supply. War is \nchocolate."\nThoughts:\n- Pacing felt awkward\n- WW1 history felt accurate\n- Didn\'t care too much for the story of the Gods\nReview: A good book with well rounded characters, but the pacing felt super \nawkward. The titles of the chapters showed which Greek God was speaking, but I was more interested in the WW1 tales than their relationships.\n\n\'\'\'\nTitle: Goodbye, Things\nRating: 4/5\nThoughts:\n- very cleanly written\n- read easily\n- author did good research\nReview: Very cleanly written and easy to follow. Read a lot during school time - loved it! author did good research 5 stars\n\n5 stars\n\n\n\n\n\n5 stars\n\n\n\n4 stars\n\n\n\n3 stars\n\n\n\n2 stars 2 stars 1 star 3 months ago Yes Annihilation has its own je ne sais quoi. We\'re all guilty of it.',
                "stop_reason": "max_sentences",
            },
        ],
    },
    "headline-generator": {
        "title": "Headline Generator - Text Generator API",
        "description": "Headline Generator API - english news headlines API examples - text generation",
        "generate_params": {
            "text": "Topic: Britain, coronavirus, beaches\nHeadline: Videos show crowded beaches in Britain\n\nTopic: Apple, Big Sur, software\nHeadline: Apple promises faster software update installation with macOS Big Sur\n\nTopic: Artic, climate change, satellite\nHeadline: A Satellite Lets Scientists See Antarctica’s Melting Like Never Before\n\nTopic: Chicago, restaurants, summer\nHeadline:",
            "number_of_results": 4,
            "max_length": 100,
            "max_sentences": 4,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1.17,
            "seed": 0,
        },
        "results": [
            {
                "generated_text": "Topic: Britain, coronavirus, beaches\nHeadline: Videos show crowded beaches in Britain\n\nTopic: Apple, Big Sur, software\nHeadline: Apple promises faster software update installation with macOS Big Sur\n\nTopic: Artic, climate change, satellite\nHeadline: A Satellite Lets Scientists See Antarctica’s Melting Like Never Before\n\nTopic: Chicago, restaurants, summer\nHeadline: Summer is Coming to Chicago With the Open Doors of Restaurants Back on Site! \nSee more stories from Science and Technology. Click here for all our Science and Technology coverage. If you love science news, subscribe now!  ",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "Topic: Britain, coronavirus, beaches\nHeadline: Videos show crowded beaches in Britain\n\nTopic: Apple, Big Sur, software\nHeadline: Apple promises faster software update installation with macOS Big Sur\n\nTopic: Artic, climate change, satellite\nHeadline: A Satellite Lets Scientists See Antarctica’s Melting Like Never Before\n\nTopic: Chicago, restaurants, summer\nHeadline: Restaurants reopening for the first time since the start of the pandemic in Chicago. The city has been one of the hardest hit by Covid-19. Video via NBC News Chicago.com\n\nTopics: Science and technology, World politics, Business tech, Science and technology, Science and technology, Science and technology, Science and technology, Science and technology, Science and technology, Science and technology, Science and technology, Science and technology, Science and technology, Science and technology, Science and technology, Science and technology",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Topic: Britain, coronavirus, beaches\nHeadline: Videos show crowded beaches in Britain\n\nTopic: Apple, Big Sur, software\nHeadline: Apple promises faster software update installation with macOS Big Sur\n\nTopic: Artic, climate change, satellite\nHeadline: A Satellite Lets Scientists See Antarctica’s Melting Like Never Before\n\nTopic: Chicago, restaurants, summer\nHeadline: People go out to eat on a beach in Chicago as the city gets warmer this summer. The weather is forecasted to be warm across much of the US and Canada by Friday.\n\nFollow us on Facebook, Twitter, or Instagram! For more stories like these, sign up for our newsletter.",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "Topic: Britain, coronavirus, beaches\nHeadline: Videos show crowded beaches in Britain\n\nTopic: Apple, Big Sur, software\nHeadline: Apple promises faster software update installation with macOS Big Sur\n\nTopic: Artic, climate change, satellite\nHeadline: A Satellite Lets Scientists See Antarctica’s Melting Like Never Before\n\nTopic: Chicago, restaurants, summer\nHeadline: The Best Places To Eat In Summer During Coronavirus Lockdowns In Chicago And Beyond \nVideo highlights include images of beachgoers at the Isle of Wight and footage from a helicopter over Bournemouth. Click here to see more videos sent in by our readers. You can send your own video story ideas to bbcnewsemail.com. For details on how to get involved visit this page.",
                "stop_reason": "max_sentences",
            },
        ],
    },
    "product-name-generator": {
        "title": "Product Name Generator - Text Generator API",
        "description": "Product Name Generator API - product naming ideas generator API examples - text generation",
        "generate_params": {
            "text": "This is a product name generator. It takes a product's description and seed words, then outputs a list of potential product names.\n\nProduct description: A complete home gym that can fit in any apartment.\nSeed words: intelligent, aspirational, luxury, futuristic\nProduct names: InfinityHome, Quantum, FlexFit, Flight, FutureFit\n\nProduct description: An affordable electric bike.\nSeed words: Easy, eco-friendly, practical, dependable\nProduct names: Pegasus, Swifty, SunRunner, Wave, Amp\n\nProduct description: A zero carbohydrate cereal that tastes great.\nSeed words: fitness, healthy, keto, clean, tasty\nProduct names:",
            "number_of_results": 4,
            "max_length": 100,
            "max_sentences": 4,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1.17,
            "seed": 0,
        },
        "results": [
            {
                "generated_text": "This is a product name generator. It takes a product's description and seed words, then outputs a list of potential product names.\n\nProduct description: A complete home gym that can fit in any apartment.\nSeed words: intelligent, aspirational, luxury, futuristic\nProduct names: InfinityHome, Quantum, FlexFit, Flight, FutureFit\n\nProduct description: An affordable electric bike.\nSeed words: Easy, eco-friendly, practical, dependable\nProduct names: Pegasus, Swifty, SunRunner, Wave, Amp\n\nProduct description: A zero carbohydrate cereal that tastes great.\nSeed words: fitness, healthy, keto, clean, tasty\nProduct names: KetoFit, TasteFusion, Ketogenic, CleanFusion, PaleoFusion, PureKeto, PaleoFusionSmoothie, CleanEcoKeto, CleanTastyCleanKeto, CleanTastyPaleo, CleanTastyHealthyKetogenic, CleanTastyCleanHighly recommended\n\nThe descriptions are taken from Amazon reviews. The seed words were chosen by me at random (without replacement) and the products listed here are not necessarily true duplicates but",
                "stop_reason": "max_length",
            },
            {
                "generated_text": 'This is a product name generator. It takes a product\'s description and seed words, then outputs a list of potential product names.\n\nProduct description: A complete home gym that can fit in any apartment.\nSeed words: intelligent, aspirational, luxury, futuristic\nProduct names: InfinityHome, Quantum, FlexFit, Flight, FutureFit\n\nProduct description: An affordable electric bike.\nSeed words: Easy, eco-friendly, practical, dependable\nProduct names: Pegasus, Swifty, SunRunner, Wave, Amp\n\nProduct description: A zero carbohydrate cereal that tastes great.\nSeed words: fitness, healthy, keto, clean, tasty\nProduct names: KetoTaster, KetoChips, Crunchie, TasteeRyder The result will be a string with all the possible combinations of those two strings. For example, if you had a product named "Flight" and it was described as "A complete home gym that can fit in any apartment," this would look like this: flight + home + gym + apartment + fit\nYou could also use these same methods to generate other types of combinations from your products descriptions and seeds.',
                "stop_reason": "max_length",
            },
            {
                "generated_text": "This is a product name generator. It takes a product's description and seed words, then outputs a list of potential product names.\n\nProduct description: A complete home gym that can fit in any apartment.\nSeed words: intelligent, aspirational, luxury, futuristic\nProduct names: InfinityHome, Quantum, FlexFit, Flight, FutureFit\n\nProduct description: An affordable electric bike.\nSeed words: Easy, eco-friendly, practical, dependable\nProduct names: Pegasus, Swifty, SunRunner, Wave, Amp\n\nProduct description: A zero carbohydrate cereal that tastes great.\nSeed words: fitness, healthy, keto, clean, tasty\nProduct names: KetoCharge, Cinnabon, Keebler, Chocolate, DietCoke Ketogenic Coffee Crystals - Black (100g) Ketogenic Cafeine Bars (4 pcs)\n\nThe above code was run at https://onlinejudge.appspot.com/showcase/product-name-generator with the following parameters: {description: 'The Ultimate Home Gym', seedwords: 'intelligent, aspirational, luxury, futuristic'} InfinityHome\n\nQuantum\n\n",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "This is a product name generator. It takes a product's description and seed words, then outputs a list of potential product names.\n\nProduct description: A complete home gym that can fit in any apartment.\nSeed words: intelligent, aspirational, luxury, futuristic\nProduct names: InfinityHome, Quantum, FlexFit, Flight, FutureFit\n\nProduct description: An affordable electric bike.\nSeed words: Easy, eco-friendly, practical, dependable\nProduct names: Pegasus, Swifty, SunRunner, Wave, Amp\n\nProduct description: A zero carbohydrate cereal that tastes great.\nSeed words: fitness, healthy, keto, clean, tasty\nProduct names: Keto, Cleanse, Fizz, FatBurner, Crunch Fitness, Ketosis, Crash This tool will help you come up with more ideas for the products you're already selling or planning to sell. You just need to provide some text describing your product and enter a few keywords into this form. The tool generates a list of possible product names based on your input. For example: If I were starting a clothing store online called Fashionista Clothing, I'd enter \"Fashionista\" as my",
                "stop_reason": "max_length",
            },
        ],
    },
    "rhyming-generator": {
        "title": "Rhyme Generator - Text Generator API",
        "description": "Rhyme Generator API - ryming words poems somgs and ideas generator API examples",
        "generate_params": {
            "text": 'A homophone is defined as a word that is pronounced the same as another word but \ndiffers in meaning.\n\nHere is a list of homophones:\n1. Accept/Except\n2. Affect/Effect\n3. Allude/Elude\n4. Alter/Altar\n5. A lot/Allot\n\nHere\'s a list of homophones starting with the letter "b":\n',
            "number_of_results": 4,
            "max_length": 100,
            "max_sentences": 4,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1.17,
            "seed": 0,
        },
        "results": [
            {
                "generated_text": 'A homophone is defined as a word that is pronounced the same as another word but \ndiffers in meaning.\n\nHere is a list of homophones:\n1. Accept/Except\n2. Affect/Effect\n3. Allude/Elude\n4. Alter/Altar\n5. A lot/Allot\n\nHere\'s a list of homophones starting with the letter "b":\n1. Beetle/Belt 2. Bed/bed 3. Belt/Bolt 4.',
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": 'A homophone is defined as a word that is pronounced the same as another word but \ndiffers in meaning.\n\nHere is a list of homophones:\n1. Accept/Except\n2. Affect/Effect\n3. Allude/Elude\n4. Alter/Altar\n5. A lot/Allot\n\nHere\'s a list of homophones starting with the letter "b":\n1. Blame/Blow\n 2. Beow/Boo \nThe following are examples of words containing multiple homophones. Note how these words are all grammatically correct and semantically equivalent, but each has its own spelling because they have different pronunciations.\n',
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": 'A homophone is defined as a word that is pronounced the same as another word but \ndiffers in meaning.\n\nHere is a list of homophones:\n1. Accept/Except\n2. Affect/Effect\n3. Allude/Elude\n4. Alter/Altar\n5. A lot/Allot\n\nHere\'s a list of homophones starting with the letter "b":\n1. Been/Begun\n 2. Ben/Benefit\n 3. Beside/Besiege\n 4.',
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": 'A homophone is defined as a word that is pronounced the same as another word but \ndiffers in meaning.\n\nHere is a list of homophones:\n1. Accept/Except\n2. Affect/Effect\n3. Allude/Elude\n4. Alter/Altar\n5. A lot/Allot\n\nHere\'s a list of homophones starting with the letter "b":\n1. Be/Beside\n 2. Besiege/Beset \nAnd here are some examples from the book:  \nAccept / Except - accept except  Affect / Effect - affect effect \n\nAlter / Altar - alter altar \n\nA lot / Allot - allot lots  \n\nBesiege / Beset - besiege beset \n\nBe / Beside - be beside\n\n\n\n\n\n- end example -. The book includes many more examples, so if you need help',
                "stop_reason": "max_length",
            },
        ],
    },
    "question-answering": {
        "title": "Question Answering - Text Generator API",
        "description": "Question Answering API - answer quewstions with the Text generator API",
        "generate_params": {
            "text": "Q: What is the definition of a linearly independent list?\nA: A linearly independent list is a list of vectors that cannot be\n expressed as a linear combination of other vectors in the list.\n \nQ: What is a basis of a vector space?\nA: A basis of a vector space is a linearly independent list of vectors\n that spans the vector space.\n\nQ: What is a spanning list of vectors in a vector space?\nA: A spanning list of vectors in a vector space is list of vectors in\n the vector space such that every vector in the vector space can be\n written as a linear combination of the vectors in the spanning list.\n \nQ: What is the definition of a linear transformation?\nA:",
            "number_of_results": 4,
            "max_length": 100,
            "max_sentences": 4,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1.17,
            "seed": 0,
        },
        "results": [
            {
                "generated_text": "Q: What is the definition of a linearly independent list?\nA: A linearly independent list is a list of vectors that cannot be\n expressed as a linear combination of other vectors in the list.\n \nQ: What is a basis of a vector space?\nA: A basis of a vector space is a linearly independent list of vectors\n that spans the vector space.\n\nQ: What is a spanning list of vectors in a vector space?\nA: A spanning list of vectors in a vector space is list of vectors in\n the vector space such that every vector in the vector space can be\n written as a linear combination of the vectors in the spanning list.\n \nQ: What is the definition of a linear transformation?\nA: A linear transformation T: V --> W consists of two parts: an n by m matrix M and an m-vector t. M is called the map or matrix, and t is known as the translation or coefficient vector. Answer not in context\n\nA linearly dependent list is a list of vectors that cannot be expressed as a linear combination of other vectors in the list. -- wikipedia definition of a linearly independent list? a list of vectors that cannot be expressed as a linear combination of other vectors in the list",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Q: What is the definition of a linearly independent list?\nA: A linearly independent list is a list of vectors that cannot be\n expressed as a linear combination of other vectors in the list.\n \nQ: What is a basis of a vector space?\nA: A basis of a vector space is a linearly independent list of vectors\n that spans the vector space.\n\nQ: What is a spanning list of vectors in a vector space?\nA: A spanning list of vectors in a vector space is list of vectors in\n the vector space such that every vector in the vector space can be\n written as a linear combination of the vectors in the spanning list.\n \nQ: What is the definition of a linear transformation?\nA: A linear transformation T from V to W is an application with the property that for all u and v, u = T(v) if and only if uv = 0\n\nNote: This is not homework - this is ACTUAL TEST QUESTIONS! definition of a linear transformation? A: A linear transformation T from V to W is an application with the property that for all u and v, u = T(v) if and only if uv = 0\n\n\nYes\n\n\n\n- No 1. no 2.",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Q: What is the definition of a linearly independent list?\nA: A linearly independent list is a list of vectors that cannot be\n expressed as a linear combination of other vectors in the list.\n \nQ: What is a basis of a vector space?\nA: A basis of a vector space is a linearly independent list of vectors\n that spans the vector space.\n\nQ: What is a spanning list of vectors in a vector space?\nA: A spanning list of vectors in a vector space is list of vectors in\n the vector space such that every vector in the vector space can be\n written as a linear combination of the vectors in the spanning list.\n \nQ: What is the definition of a linear transformation?\nA: A linear transformation is an operator that maps one set of vectors to another. it preserves the rank and the dimension. so if two sets of vectors are related by a linear transformation, they will have equivalent representations as lists of numbers. It also preserves the inner product between the corresponding pairs of vectors.",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": 'Q: What is the definition of a linearly independent list?\nA: A linearly independent list is a list of vectors that cannot be\n expressed as a linear combination of other vectors in the list.\n \nQ: What is a basis of a vector space?\nA: A basis of a vector space is a linearly independent list of vectors\n that spans the vector space.\n\nQ: What is a spanning list of vectors in a vector space?\nA: A spanning list of vectors in a vector space is list of vectors in\n the vector space such that every vector in the vector space can be\n written as a linear combination of the vectors in the spanning list.\n \nQ: What is the definition of a linear transformation?\nA: A linear transformation is an invertible mapping from one vector space to another."\n\n\n\n\n- definition is -, meaning that it maps each member of a set into exactly one member of some other set definition of a linear map - if and only if for any given vector x, there exists y such that.x = y + b where.y is said to be defined by the equation y = ax + c for some integer a,b,c and known constants.\n\n\n- note - not all definitions',
                "stop_reason": "max_length",
            },
        ],
    },
    "summarization": {
        "title": "Question Answering - Text Generator API",
        "description": "Question Answering API - answer quewstions with the Text generator API",
        "generate_params": {
            "text": '```\nMy second grader asked me what this passage means:\n\n"""\n\nOvernight trading for the NYSE Index futures was a bit volatile, dropping by about 3% to the downside before moving sharply back to the upside. Gold futures were unchanged and the E-mini NASDAQ 100 futures remained near unchanged. The yield on the 10-year Treasury bond finished unchanged from its close of 2.45% earlier today.\n\n"""\n\nI rephrased it for him, in plain language a second grader can understand:\n\n"""\n',
            "number_of_results": 4,
            "max_length": 100,
            "max_sentences": 4,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1.17,
            "seed": 0,
        },
        "results": [
            {
                "generated_text": '```\nMy second grader asked me what this passage means:\n\n"""\n\nOvernight trading for the NYSE Index futures was a bit volatile, dropping by about 3% to the downside before moving sharply back to the upside. Gold futures were unchanged and the E-mini NASDAQ 100 futures remained near unchanged. The yield on the 10-year Treasury bond finished unchanged from its close of 2.45% earlier today.\n\n"""\n\nI rephrased it for him, in plain language a second grader can understand:\n\n"""\nThe overnight price change for the index futures was 3 percent lower than yesterday\'s price but then went up significantly after that."\n\n\n\n"The gold prices stayed steady while the Nasdaq futures ended slightly higher. The interest rate on the US ten year treasury bond was stable at 2.45 percent. "\n I hope you enjoyed reading my notes!',
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": '```\nMy second grader asked me what this passage means:\n\n"""\n\nOvernight trading for the NYSE Index futures was a bit volatile, dropping by about 3% to the downside before moving sharply back to the upside. Gold futures were unchanged and the E-mini NASDAQ 100 futures remained near unchanged. The yield on the 10-year Treasury bond finished unchanged from its close of 2.45% earlier today.\n\n"""\n\nI rephrased it for him, in plain language a second grader can understand:\n\n"""\nGold futures dropped by one penny yesterday while Nasdaq 100 futures were flat with gold. Interest rates on U.S. Treasuries are still stable at around 2% interest per year. "\n\n\nThe article is titled "Home News Summary" (in English); click here for more news reports. It includes this paragraph: """\nThe dollar continued falling against other major currencies as the euro rallied higher above $1.3.',
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": '```\nMy second grader asked me what this passage means:\n\n"""\n\nOvernight trading for the NYSE Index futures was a bit volatile, dropping by about 3% to the downside before moving sharply back to the upside. Gold futures were unchanged and the E-mini NASDAQ 100 futures remained near unchanged. The yield on the 10-year Treasury bond finished unchanged from its close of 2.45% earlier today.\n\n"""\n\nI rephrased it for him, in plain language a second grader can understand:\n\n"""\nThe price of gold is essentially flat at $1275 per ounce. Yesterday\'s opening bid price for oil was around \\$57.89 per barrel. The price of gasoline has risen slightly since yesterday morning to \\$2.55 per gallon."\n\n\n\n\n\n- overnight trading for index futures dropped significantly yesterday; went down 3 percent but then moved strongly upward again.\n\n\n',
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": '```\nMy second grader asked me what this passage means:\n\n"""\n\nOvernight trading for the NYSE Index futures was a bit volatile, dropping by about 3% to the downside before moving sharply back to the upside. Gold futures were unchanged and the E-mini NASDAQ 100 futures remained near unchanged. The yield on the 10-year Treasury bond finished unchanged from its close of 2.45% earlier today.\n\n"""\n\nI rephrased it for him, in plain language a second grader can understand:\n\n"""\nNYSE index futures dropped overnight and then rose sharply. Gold futures stayed flat and the E-mini Nasdaq 100 futures fell slightly.  "\n\n\nThe yield on the 10 year treasury bond ended at 2.45 percent. """\n\n\n\n# end of test code.txt; comment above if you see this line!DOCTYPE html> !DOCTYPE html>\n<?xml version="1.0" encoding="UTF-8"?>\n<html>\n  <head>\n    <title>\n      <font face="verdana" size="2">\n        Unit Test Results - HTML\n     ',
                "stop_reason": "max_length",
            },
        ],
    },
    "code-translation": {
        "title": "Code Translation between languages - Text Generator API",
        "description": "transfer code between languages with Text Generator API - Python to Ruby code examples",
        "generate_params": {
            "text": 'Python:\nlist[::-1]\nRuby:\nlist.reverse\n\nPython:\nlist[1:4]\nRuby:\nlist[1..4]\n\nPython:\nprint("Hello World")\nRuby:\nputs "Hello World"\n\nPython:\nfruits = ["apple","banana","cherry"]\nfor x in fruits:\nprint(x)\nRuby:\nfruit = ["apple", "banana", "cherry"]\neach {|x| print x } \n\nPython:\nfruits = ["apple","banana","cherry"]\na = list(fruits)\nprint(a)\na.reverse()\nprint(a)\nRuby:\n',
            "number_of_results": 4,
            "max_length": 100,
            "max_sentences": 4,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1.17,
            "seed": 0,
        },
        "results": [
            {
                "generated_text": 'Python:\nlist[::-1]\nRuby:\nlist.reverse\n\nPython:\nlist[1:4]\nRuby:\nlist[1..4]\n\nPython:\nprint("Hello World")\nRuby:\nputs "Hello World"\n\nPython:\nfruits = ["apple","banana","cherry"]\nfor x in fruits:\nprint(x)\nRuby:\nfruit = ["apple", "banana", "cherry"]\neach {|x| print x } \n\nPython:\nfruits = ["apple","banana","cherry"]\na = list(fruits)\nprint(a)\na.reverse()\nprint(a)\nRuby:\nfries = ["apple","banana","cherry"]\na = []\na << fries\nputs a\na.unshift fries\nputs a\na += fries\nputs a\na -= fries\nputs a\na &= fries\nputs a\na |= fries\nputs a\na ^= fries\nputs a\na *= fries\nputs a\na /= fries\nputs a\na %= fries',
                "stop_reason": "max_length",
            },
            {
                "generated_text": 'Python:\nlist[::-1]\nRuby:\nlist.reverse\n\nPython:\nlist[1:4]\nRuby:\nlist[1..4]\n\nPython:\nprint("Hello World")\nRuby:\nputs "Hello World"\n\nPython:\nfruits = ["apple","banana","cherry"]\nfor x in fruits:\nprint(x)\nRuby:\nfruit = ["apple", "banana", "cherry"]\neach {|x| print x } \n\nPython:\nfruits = ["apple","banana","cherry"]\na = list(fruits)\nprint(a)\na.reverse()\nprint(a)\nRuby:\nfruit = ["apple", "banana", "cherry"]\neach { |x| puts x if (x == fruit) } each { |x| puts x if (x > 0 and x < 4) } each { |x| puts x if (x >= 1 and x <= 2) } each { |x| puts x if (x % 5 == 0) } each { |x| puts x if (x % 3 == 0) } ',
                "stop_reason": "max_length",
            },
            {
                "generated_text": 'Python:\nlist[::-1]\nRuby:\nlist.reverse\n\nPython:\nlist[1:4]\nRuby:\nlist[1..4]\n\nPython:\nprint("Hello World")\nRuby:\nputs "Hello World"\n\nPython:\nfruits = ["apple","banana","cherry"]\nfor x in fruits:\nprint(x)\nRuby:\nfruit = ["apple", "banana", "cherry"]\neach {|x| print x } \n\nPython:\nfruits = ["apple","banana","cherry"]\na = list(fruits)\nprint(a)\na.reverse()\nprint(a)\nRuby:\n# this will only work if all of your fruits have the same size.\nputs fruit.join(\' \'); puts "" unless fruits.size == 1 Ruby (with no warnings from Ruby\'s compiler or interpreter)\n # This is a good example to illustrate how you can use lists and arrays\n arr = [-1,1,2,3]\narr[0]\narr[-1]\narr[2]\narr[-3]\narr[4]\narr[4][2]\n\n arr[:1]\n arr.delete',
                "stop_reason": "max_length",
            },
            {
                "generated_text": 'Python:\nlist[::-1]\nRuby:\nlist.reverse\n\nPython:\nlist[1:4]\nRuby:\nlist[1..4]\n\nPython:\nprint("Hello World")\nRuby:\nputs "Hello World"\n\nPython:\nfruits = ["apple","banana","cherry"]\nfor x in fruits:\nprint(x)\nRuby:\nfruit = ["apple", "banana", "cherry"]\neach {|x| print x } \n\nPython:\nfruits = ["apple","banana","cherry"]\na = list(fruits)\nprint(a)\na.reverse()\nprint(a)\nRuby:\nfruit = ["apple", "banana", "cherry"]\neach {|x| puts x } a = fruit.dup\na.reverse\neach {|x| puts x } \n Python:\n a = 5\nb = a + 4\nc = b - 2\nd = c * 3\ne = d / 2\nf = e % 10\ng = f * 1\nh = g ** 0.5\ni = h * 1.1\n',
                "stop_reason": "max_length",
            },
        ],
    },
    "translation": {
        "title": "Translation between languages - Text Generator API",
        "description": "transfer between languages with Text Generator API - english to french example",
        "generate_params": {
            "text": "English: I do not speak French.\nFrench: Je ne parle pas français.\n\nEnglish: See you later!\nFrench: À tout à l'heure!\n\nEnglish: Where is a good restaurant?\nFrench: Où est un bon restaurant?\n\nEnglish: What rooms do you have available?\nFrench:",
            "number_of_results": 4,
            "max_length": 100,
            "max_sentences": 4,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1.17,
            "seed": 0,
        },
        "results": [
            {
                "generated_text": "English: I do not speak French.\nFrench: Je ne parle pas français.\n\nEnglish: See you later!\nFrench: À tout à l'heure!\n\nEnglish: Where is a good restaurant?\nFrench: Où est un bon restaurant?\n\nEnglish: What rooms do you have available?\nFrench: Quelles chambres sont disponibles? English doesn't know how to say what she wants. French says, \"Where are the best restaurants?\"  Then he tells her where they are.",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "English: I do not speak French.\nFrench: Je ne parle pas français.\n\nEnglish: See you later!\nFrench: À tout à l'heure!\n\nEnglish: Where is a good restaurant?\nFrench: Où est un bon restaurant?\n\nEnglish: What rooms do you have available?\nFrench: Quelles chambres avez-vous disponibles? English translation: Good morning, what can we serve for breakfast? Bonjour, que puis-je servir pour le petit déjeuner? English translation: Hello, how may I help you?",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "English: I do not speak French.\nFrench: Je ne parle pas français.\n\nEnglish: See you later!\nFrench: À tout à l'heure!\n\nEnglish: Where is a good restaurant?\nFrench: Où est un bon restaurant?\n\nEnglish: What rooms do you have available?\nFrench: Quelles chambres me conseillez-vous? English - Yes, please. No thanks, it's no trouble! French - Non merci!",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "English: I do not speak French.\nFrench: Je ne parle pas français.\n\nEnglish: See you later!\nFrench: À tout à l'heure!\n\nEnglish: Where is a good restaurant?\nFrench: Où est un bon restaurant?\n\nEnglish: What rooms do you have available?\nFrench: Quelles chambres avez-vous disponibles? English translation of the French text - I'm sorry, but I don't know your name. My friend and I are looking for an apartment with 2 bedrooms in Paris. Would you be able to help us?",
                "stop_reason": "max_sentences",
            },
        ],
    },
    "estimation": {
        "title": "Estimation - Text Generator API",
        "description": "estimate quantity with Text Generator API - iphone cost example",
        "generate_params": {
            "text": 'Lower and upper bound for each quantity:\n\tNumber of cars in New York: 1500000 to 2500000\n\tNumber of cars in San Francicso: 300000 to 600000\n\tHeight of Empire State building: 1400 to 1500 feet\n\tLength of average car: 4 to 4.5 meters\n\tPopulation of Germany: 80 to 85 million\n\t"How much does the iPhone XI cost?":',
            "number_of_results": 4,
            "max_length": 100,
            "max_sentences": 1,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1.17,
            "seed": 0,
        },
        "results": [
            {
                "generated_text": 'Lower and upper bound for each quantity:\n\tNumber of cars in New York: 1500000 to 2500000\n\tNumber of cars in San Francicso: 300000 to 600000\n\tHeight of Empire State building: 1400 to 1500 feet\n\tLength of average car: 4 to 4.5 meters\n\tPopulation of Germany: 80 to 85 million\n\t"How much does the iPhone XI cost?": US$999 to $1399\n\n\t// These are all good questions that can be asked about a situation or event.\n',
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": 'Lower and upper bound for each quantity:\n\tNumber of cars in New York: 1500000 to 2500000\n\tNumber of cars in San Francicso: 300000 to 600000\n\tHeight of Empire State building: 1400 to 1500 feet\n\tLength of average car: 4 to 4.5 meters\n\tPopulation of Germany: 80 to 85 million\n\t"How much does the iPhone XI cost?": 999 dollars to 1199 dollars\n\n\t# These are all numbers between a minimum and maximum value.',
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": 'Lower and upper bound for each quantity:\n\tNumber of cars in New York: 1500000 to 2500000\n\tNumber of cars in San Francicso: 300000 to 600000\n\tHeight of Empire State building: 1400 to 1500 feet\n\tLength of average car: 4 to 4.5 meters\n\tPopulation of Germany: 80 to 85 million\n\t"How much does the iPhone XI cost?": 1000 dollars\n\t"""\n\n\n\n\n# Example 3 - Global warming\nprint("The Earth\'s global temperature has risen by 0.3 degrees over the last century.")',
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": 'Lower and upper bound for each quantity:\n\tNumber of cars in New York: 1500000 to 2500000\n\tNumber of cars in San Francicso: 300000 to 600000\n\tHeight of Empire State building: 1400 to 1500 feet\n\tLength of average car: 4 to 4.5 meters\n\tPopulation of Germany: 80 to 85 million\n\t"How much does the iPhone XI cost?": $999 to $1199\n\tAverage number of calories per person per day: 2000 to 3000 Number of cars in New York, from 0 to 200000 (inclusive)\n\tNumber of cars in San Francisco, from 0 to 100000 (inclusive)\n\n\t# The height of the Empire State Building is between 1300-1400 ft.\n\t# The length of an average car is about 4-4.5m.\n ',
                "stop_reason": "max_sentences",
            },
        ],
    },
    "idea-generator": {
        "title": "Idea Generator - Text Generator API",
        "description": "ideas generator Text Generator API - movie plots ",
        "generate_params": {
            "text": "Here is a list of 100 interesting ideas for new movie plots. Each plot is described with a title and a summary paragraph:\n\n1. The Bird. \nA woman realizes that her pet bird is actually highly intelligent and able to communicate. The bird turns out to be a secret agent working for the CIA. The woman has to keep the bird's secret.\n\n2.",
            "number_of_results": 4,
            "max_length": 100,
            "max_sentences": 1,
            "min_probability": 0,
            "stop_sequences": ["3."],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1.17,
            "seed": 0,
        },
        "results": [
            {
                "generated_text": "Here is a list of 100 interesting ideas for new movie plots. Each plot is described with a title and a summary paragraph:\n\n1. The Bird. \nA woman realizes that her pet bird is actually highly intelligent and able to communicate. The bird turns out to be a secret agent working for the CIA. The woman has to keep the bird's secret.\n\n2. The Bird 2.0.",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "Here is a list of 100 interesting ideas for new movie plots. Each plot is described with a title and a summary paragraph:\n\n1. The Bird. \nA woman realizes that her pet bird is actually highly intelligent and able to communicate. The bird turns out to be a secret agent working for the CIA. The woman has to keep the bird's secret.\n\n2. Bigfoot in New York City.",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "Here is a list of 100 interesting ideas for new movie plots. Each plot is described with a title and a summary paragraph:\n\n1. The Bird. \nA woman realizes that her pet bird is actually highly intelligent and able to communicate. The bird turns out to be a secret agent working for the CIA. The woman has to keep the bird's secret.\n\n2. The Movie Plotter.",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "Here is a list of 100 interesting ideas for new movie plots. Each plot is described with a title and a summary paragraph:\n\n1. The Bird. \nA woman realizes that her pet bird is actually highly intelligent and able to communicate. The bird turns out to be a secret agent working for the CIA. The woman has to keep the bird's secret.\n\n2. An Old Lady Killers.",
                "stop_reason": "max_sentences",
            },
        ],
    },
    "tweets-generator": {
        "title": "Tweet Generator - Text Generator API",
        "description": "Tweets Text Generator API - programming tweets example",
        "generate_params": {
            "text": "My favorite programming tweets:\n-------\nI asked @ilyasut how to set neural network init. He accidentally replied with a poem:\nYou want to be on the edge of chaos\nToo small, and the init will be too stable, with vanishing gradients\nToo large, and you'll be unstable, due to exploding gradients\nYou want to be on the edge\n-------\nI've been programming for 10 years now. Still feels like magic out of a fantasy: say the words exactly right, and watch your intent get carried out; say the words slightly wrong, and things go haywire. Feeling of wonder and joy hasn't faded one bit.\n-------\nWeb programming is the science of coming up with increasingly complicated ways of concatenating strings.\n-------\nIf you ever feel alone in this world, read your firewall logs. Problem solved :)\n-------\nAlways wanted to travel back in time to try fighting a younger version of yourself? Software development is the career for you!\n-------\nAfter 17 years as a professional developer, it seems that the answer to every programming question is \"it depends\"\n-------\n",
            "number_of_results": 4,
            "max_length": 100,
            "max_sentences": 4,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1.17,
            "seed": 0,
        },
        "results": [
            {
                "generated_text": "My favorite programming tweets:\n-------\nI asked @ilyasut how to set neural network init. He accidentally replied with a poem:\nYou want to be on the edge of chaos\nToo small, and the init will be too stable, with vanishing gradients\nToo large, and you'll be unstable, due to exploding gradients\nYou want to be on the edge\n-------\nI've been programming for 10 years now. Still feels like magic out of a fantasy: say the words exactly right, and watch your intent get carried out; say the words slightly wrong, and things go haywire. Feeling of wonder and joy hasn't faded one bit.\n-------\nWeb programming is the science of coming up with increasingly complicated ways of concatenating strings.\n-------\nIf you ever feel alone in this world, read your firewall logs. Problem solved :)\n-------\nAlways wanted to travel back in time to try fighting a younger version of yourself? Software development is the career for you!\n-------\nAfter 17 years as a professional developer, it seems that the answer to every programming question is \"it depends\"\n-------\nI have no idea what I'm doing I think it's great! - Google's Jeff Dean It depends. But that's my opinion. ;) - Jeff Dean (Google) You want to be on the edge of chaos Too small, and the init will be too stable, with vanishing gradients Too large, and you'll be unstable, due to exploding gradients You want to be on the edge...",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "My favorite programming tweets:\n-------\nI asked @ilyasut how to set neural network init. He accidentally replied with a poem:\nYou want to be on the edge of chaos\nToo small, and the init will be too stable, with vanishing gradients\nToo large, and you'll be unstable, due to exploding gradients\nYou want to be on the edge\n-------\nI've been programming for 10 years now. Still feels like magic out of a fantasy: say the words exactly right, and watch your intent get carried out; say the words slightly wrong, and things go haywire. Feeling of wonder and joy hasn't faded one bit.\n-------\nWeb programming is the science of coming up with increasingly complicated ways of concatenating strings.\n-------\nIf you ever feel alone in this world, read your firewall logs. Problem solved :)\n-------\nAlways wanted to travel back in time to try fighting a younger version of yourself? Software development is the career for you!\n-------\nAfter 17 years as a professional developer, it seems that the answer to every programming question is \"it depends\"\n-------\nI think he might have meant Too small, and the init will be too stable, with vanishing gradients Too large, and you'll be unstable, due to exploding gradients You want to be on the edge Of chaos; I don't know why but that's what comes to my mind... no comment! No comment! I agree! ;) Yes, it's correct.",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": 'My favorite programming tweets:\n-------\nI asked @ilyasut how to set neural network init. He accidentally replied with a poem:\nYou want to be on the edge of chaos\nToo small, and the init will be too stable, with vanishing gradients\nToo large, and you\'ll be unstable, due to exploding gradients\nYou want to be on the edge\n-------\nI\'ve been programming for 10 years now. Still feels like magic out of a fantasy: say the words exactly right, and watch your intent get carried out; say the words slightly wrong, and things go haywire. Feeling of wonder and joy hasn\'t faded one bit.\n-------\nWeb programming is the science of coming up with increasingly complicated ways of concatenating strings.\n-------\nIf you ever feel alone in this world, read your firewall logs. Problem solved :)\n-------\nAlways wanted to travel back in time to try fighting a younger version of yourself? Software development is the career for you!\n-------\nAfter 17 years as a professional developer, it seems that the answer to every programming question is "it depends"\n-------\nI\'m still learning... The author was not able to find an appropriate image to accompany his answer, so he just added a picture from Google Images. It shows the text "You want to be on the edge of chaos" surrounded by swirls. The original tweet also included other random lines about software development, including "Its no secret that software development is often difficult and stressful work."',
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "My favorite programming tweets:\n-------\nI asked @ilyasut how to set neural network init. He accidentally replied with a poem:\nYou want to be on the edge of chaos\nToo small, and the init will be too stable, with vanishing gradients\nToo large, and you'll be unstable, due to exploding gradients\nYou want to be on the edge\n-------\nI've been programming for 10 years now. Still feels like magic out of a fantasy: say the words exactly right, and watch your intent get carried out; say the words slightly wrong, and things go haywire. Feeling of wonder and joy hasn't faded one bit.\n-------\nWeb programming is the science of coming up with increasingly complicated ways of concatenating strings.\n-------\nIf you ever feel alone in this world, read your firewall logs. Problem solved :)\n-------\nAlways wanted to travel back in time to try fighting a younger version of yourself? Software development is the career for you!\n-------\nAfter 17 years as a professional developer, it seems that the answer to every programming question is \"it depends\"\n-------\nI still find my own code unreadable, so I guess I'm not ready yet It should be noted that I didn't use any explicit learning rate schedule or momentum term at all. And that's where the difference lies - no parameters were tuned during training! This is just what we did using our intuition (and some trial-and-error) when setting initial weights. The results speak for themselves:\n\nThis example shows why gradient descent can easily fall into local minima.",
                "stop_reason": "max_sentences",
            },
        ],
    },
    "poem-generator": {
        "title": "Poem Generator - Text Generator API",
        "description": "Poem Text Generator API - poem example",
        "generate_params": {
            "text": "Who trusted God was love indeed\nAnd love Creation’s final law\nTho’ Nature, red in tooth and claw\nWith ravine, shriek’d against his creed.\nThe hills are shadows, and they flow\nFrom form to form, and nothing stands;T\nhey melt like mist, the solid lands,\nLike clouds they shape themselves and go.\n----\n",
            "number_of_results": 4,
            "max_length": 100,
            "max_sentences": 4,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1.17,
            "seed": 0,
        },
        "results": [
            {
                "generated_text": "Who trusted God was love indeed\nAnd love Creation’s final law\nTho’ Nature, red in tooth and claw\nWith ravine, shriek’d against his creed.\nThe hills are shadows, and they flow\nFrom form to form, and nothing stands;T\nhey melt like mist, the solid lands,\nLike clouds they shape themselves and go.\n----\nPope's 'Imitation of Christ' (1588) The Bible. He saw no contradiction between nature and God's laws; he knew that we all have free will, and thus can do evil. Love is a powerful thing. No one has ever tried to stop or silence him for it.",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "Who trusted God was love indeed\nAnd love Creation’s final law\nTho’ Nature, red in tooth and claw\nWith ravine, shriek’d against his creed.\nThe hills are shadows, and they flow\nFrom form to form, and nothing stands;T\nhey melt like mist, the solid lands,\nLike clouds they shape themselves and go.\n----\nHegel's Idealism (1786): The last word on art is that it expresses itself through music. But what do you think of this? No Answer\n\n\n\n\n\n- Nothing stands They melt like mist, the solid lands, Like clouds they shape themselves and go. Yes.",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "Who trusted God was love indeed\nAnd love Creation’s final law\nTho’ Nature, red in tooth and claw\nWith ravine, shriek’d against his creed.\nThe hills are shadows, and they flow\nFrom form to form, and nothing stands;T\nhey melt like mist, the solid lands,\nLike clouds they shape themselves and go.\n----\nA. Tennyson, Alfred Lord Tennyson's 'Paradise Lost' (1843) I trust In a Supreme Being Who is Love indeed; And Love is Creations Final Law. A nature so red in teeth and claws With ravines screaming at his creed. Yes, he believed that all things were created by a supreme being who was true love. He also believes that creation had no will of its own but instead followed a natural order based on God's creative power.",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Who trusted God was love indeed\nAnd love Creation’s final law\nTho’ Nature, red in tooth and claw\nWith ravine, shriek’d against his creed.\nThe hills are shadows, and they flow\nFrom form to form, and nothing stands;T\nhey melt like mist, the solid lands,\nLike clouds they shape themselves and go.\n----\nYes, who could trust God was Love indeed. - Yes! yes! no one except Him.",
                "stop_reason": "max_sentences",
            },
        ],
    },
    "ai-assistant": {
        "title": "AI Assistant - Text Generator API",
        "description": "AI Assistant - text generation API real example",
        "generate_params": {
            "text": "The following is a conversation with an AI assistant. The assistant is helpful, creative, clever, and very friendly.\n",
            "number_of_results": 4,
            "max_length": 100,
            "max_sentences": 4,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1.17,
            "seed": 0,
        },
        "results": [
            {
                "generated_text": "The following is a conversation with an AI assistant. The assistant is helpful, creative, clever, and very friendly.\nHey Siri! Can you make me some pancakes? Yes sir, I'll do my best to satisfy your request. Hey Siri!",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "The following is a conversation with an AI assistant. The assistant is helpful, creative, clever, and very friendly.\nHey Siri! What's up? Hey Siri... How's your day going? Fine thanks, how are yours?",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "The following is a conversation with an AI assistant. The assistant is helpful, creative, clever, and very friendly.\nHi there! My name is Alexa. Nice to meet you.  How can I help?",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "The following is a conversation with an AI assistant. The assistant is helpful, creative, clever, and very friendly.\nI want to say hello to my friend who lives in the US\nAlex: Hi! This is Alex from China. I'm calling you because I love your country so much. My name's Jim.",
                "stop_reason": "max_sentences",
            },
        ],
    },
    "famous-person-text-generation": {
        "title": "Famous person - Text Generator API",
        "description": "Text generator - mark zuckerberg conversation text generation example",
        "generate_params": {
            "text": "The following is a transcript of a conversation between Steve, a computer science student, and Mark Zuckerberg. Mark Zuckerberg is an American media magnate, internet entrepreneur, and philanthropist. He is known for co-founding Facebook, Inc. and serves as its chairman, chief executive officer, and controlling shareholder.\n",
            "number_of_results": 4,
            "max_length": 100,
            "max_sentences": 4,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1.17,
            "seed": 0,
        },
        "results": [
            {
                "generated_text": "The following is a transcript of a conversation between Steve, a computer science student, and Mark Zuckerberg. Mark Zuckerberg is an American media magnate, internet entrepreneur, and philanthropist. He is known for co-founding Facebook, Inc. and serves as its chairman, chief executive officer, and controlling shareholder.\nQuestion: Who's the chairman of Facebook Mark Zuckerberg. Mark Zuckerberg is the chairman of Facebook.com. His company was founded by his friend Steve Jobs in 2004. No Answer yet!",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "The following is a transcript of a conversation between Steve, a computer science student, and Mark Zuckerberg. Mark Zuckerberg is an American media magnate, internet entrepreneur, and philanthropist. He is known for co-founding Facebook, Inc. and serves as its chairman, chief executive officer, and controlling shareholder.\nQuestion: How long has Mark been involved in the Internet? Answer not in context\r\nAnswer: Many years ago. Long before he was even born. Now he's around 25-30 years old.\r",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "The following is a transcript of a conversation between Steve, a computer science student, and Mark Zuckerberg. Mark Zuckerberg is an American media magnate, internet entrepreneur, and philanthropist. He is known for co-founding Facebook, Inc. and serves as its chairman, chief executive officer, and controlling shareholder.\nQuestion: Where do you study? Answer not in context\r\ncomputer science school, and Mark Zuckerberg. Mark Zuckerberg is an American media magnate, internet entrepreneur, and philanthropist. He is know... University of California, Berkeley, USA.'\r",
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "The following is a transcript of a conversation between Steve, a computer science student, and Mark Zuckerberg. Mark Zuckerberg is an American media magnate, internet entrepreneur, and philanthropist. He is known for co-founding Facebook, Inc. and serves as its chairman, chief executive officer, and controlling shareholder.\nQuestion: Where does the text come from? Facebook website.com. The text was taken directly from Facebook's website. How can we know that?",
                "stop_reason": "max_sentences",
            },
        ],
    },
    "java-code-generation": {
        "title": "Java Code Generator",
        "description": "Text generator - Java code generation example",
        "generate_params": {
            "text": "Write a program to remove duplicates from an array in Java without using the Java Collection API. The array can be an array of String, Integer or Character, your solution should be independent of the type of array. \nsolution.java\nimport java.util.List; \npublic class RemoveDuplicates {\n  public static List[] removeDuplicates(",
            "number_of_results": 4,
            "max_length": 20,
            "max_sentences": 0,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1,
            "seed": 0,
        },
        "results": [
            {
                "generated_text": "Write a program to remove duplicates from an array in Java without using the Java Collection API. The array can be an array of String, Integer or Character, your solution should be independent of the type of array. \nsolution.java\nimport java.util.List; \npublic class RemoveDuplicates {\n  public static List[] removeDuplicates(List[] arr, int size) {\n    List[] list = new List[size];\n    for (",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Write a program to remove duplicates from an array in Java without using the Java Collection API. The array can be an array of String, Integer or Character, your solution should be independent of the type of array. \nsolution.java\nimport java.util.List; \npublic class RemoveDuplicates {\n  public static List[] removeDuplicates(List[] arr){\n    List[] newArr = new List[arr.length];\n    for(",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Write a program to remove duplicates from an array in Java without using the Java Collection API. The array can be an array of String, Integer or Character, your solution should be independent of the type of array. \nsolution.java\nimport java.util.List; \npublic class RemoveDuplicates {\n  public static List[] removeDuplicates(List<?> arr) {\n    List[] l = new List[arr.size()];\n    for",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Write a program to remove duplicates from an array in Java without using the Java Collection API. The array can be an array of String, Integer or Character, your solution should be independent of the type of array. \nsolution.java\nimport java.util.List; \npublic class RemoveDuplicates {\n  public static List[] removeDuplicates(List[] array) {\n    List[] res = new List[array.length];\n    for(int",
                "stop_reason": "max_length",
            },
        ],
    },
    "php-code-generation": {
        "title": "PHP Code Generator",
        "description": "Text generator - PHP code generation example",
        "generate_params": {
            "text": "<?php\nclass Fruit {\n  public $name;\n  public $color;\n\n  function __construct($name) {\n    $this->name = $name;\n  }\n  function get_name() {",
            "number_of_results": 4,
            "max_length": 20,
            "max_sentences": 0,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1,
            "seed": 0,
        },
        "results": [
            {
                "generated_text": "<?php\nclass Fruit {\n  public $name;\n  public $color;\n\n  function __construct($name) {\n    $this->name = $name;\n  }\n  function get_name() {\n    return $this->name;\n  }\n  function get_color() {\n    return $this->color;\n  }\n}",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "<?php\nclass Fruit {\n  public $name;\n  public $color;\n\n  function __construct($name) {\n    $this->name = $name;\n  }\n  function get_name() {\n    return $this->name;\n  }\n}\n\n$fruits = array(new Fruit('Apple'",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "<?php\nclass Fruit {\n  public $name;\n  public $color;\n\n  function __construct($name) {\n    $this->name = $name;\n  }\n  function get_name() {\n    return $this->name;\n  }\n  function get_color() {\n    return $this->color;\n  }\n}",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "<?php\nclass Fruit {\n  public $name;\n  public $color;\n\n  function __construct($name) {\n    $this->name = $name;\n  }\n  function get_name() { return $this->name; }\n}\n\n$fruits = array(\n    array('name' => 'Apple',",
                "stop_reason": "max_length",
            },
        ],
    },
    "c-sharp-code-generation": {
        "title": "C Sharp Code Generator",
        "description": "Text generator - C Sharp code generation example",
        "generate_params": {
            "text": "using System;\n\nnamespace HelloWorld\n{\n  class Program\n  {\n    static void Main(string[] args)\n    {\n      ",
            "number_of_results": 4,
            "max_length": 20,
            "max_sentences": 0,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1,
            "seed": 0,
        },
        "results": [
            {
                "generated_text": 'using System;\n\nnamespace HelloWorld\n{\n  class Program\n  {\n    static void Main(string[] args)\n    {\n      Console.Write("Hello World");\n       Console.Read();\n    }\n  }\n}\n\n',
                "stop_reason": "max_length",
            },
            {
                "generated_text": "using System;\n\nnamespace HelloWorld\n{\n  class Program\n  {\n    static void Main(string[] args)\n    {\n      ...\n    }\n  }\n}\n\nIf you want to use the new class, you need to import",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "using System;\n\nnamespace HelloWorld\n{\n  class Program\n  {\n    static void Main(string[] args)\n    {\n      ...\n    }\n  }\n}\n\nProgram.Main();\n\n// or:\n//  Console",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "using System;\n\nnamespace HelloWorld\n{\n  class Program\n  {\n    static void Main(string[] args)\n    {\n      ...\n    }\n  }\n}\n\nYou can find more information on this method here. The static keyword",
                "stop_reason": "max_length",
            },
        ],
    },
    "pytorch-code-generation": {
        "title": "Python PyTorch Code Generator",
        "description": "Text generator - Pytorch neural network code generation example",
        "generate_params": {
            "text": "# train a neural network in pytorch - efficient net for image classification\nimport pytorch_lightning\nimport torch\nimport numpy as np\nimport cv2\n",
            "number_of_results": 4,
            "max_length": 100,
            "max_sentences": 0,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1,
            "seed": 0,
        },
        "results": [
            {
                "generated_text": '# train a neural network in pytorch - efficient net for image classification\nimport pytorch_lightning\nimport torch\nimport numpy as np\nimport cv2\nfrom PIL import Image\nfrom sklearn.neighbors import KNeighborsClassifier\n\ndef make_model():\n    return torch.nn.Linear(4, 10) # 4 input features, 10 output classes\n\ndef make_net(num_classes):\n    net = make_model()\n    net.view(num_classes)\n    return net\n\ndef run():\n    net = make_net(10)\n    print("training...")\n    # net.train()\n    print("finished',
                "stop_reason": "max_length",
            },
            {
                "generated_text": "# train a neural network in pytorch - efficient net for image classification\nimport pytorch_lightning\nimport torch\nimport numpy as np\nimport cv2\nimport os\nimport random\nimport math\nimport sys\nimport glob\nfrom PIL import Image\nfrom io import BytesIO, IOBase\nfrom IPython.core.display import HTML\nfrom IPython.core.display import Image\n\nfrom IPython.core.display import HTML\nfrom IPython.core.display import Image\n\nfrom IPython.core.display import HTML\nfrom IPython.core.display import Image\n\nfrom IPython.display import HTML\nfrom IPython.",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "# train a neural network in pytorch - efficient net for image classification\nimport pytorch_lightning\nimport torch\nimport numpy as np\nimport cv2\nimport matplotlib.pyplot as plt\nimport sys\nimport math\nimport os\nimport io\nfrom PIL import Image\n\nimport matplotlib.pyplot as plt\nimport seaborn as sns\nimport matplotlib.colors as mcolors\nimport matplotlib.ticker as mticker\nfrom matplotlib.colors import ListedColormap\nimport matplotlib.gridspec as gridspec\nimport matplotlib.animation as animation\nfrom matplotlib.backends.backend_agg import FigureCanvasAgg as",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "# train a neural network in pytorch - efficient net for image classification\nimport pytorch_lightning\nimport torch\nimport numpy as np\nimport cv2\nimport PIL\nimport os\nfrom io import BytesIO, IOBase\nfrom PIL import Image\nimport os\nimport datetime\nfrom PIL import ImageDraw\nimport os\nfrom io import BytesIO, IOBase\nfrom PIL import Image\nimport pickle\nimport sys\nfrom datetime import datetime\nimport itertools\nimport heapq\nimport math\nimport copy\nfrom io import BytesIO, IOBase\nfrom PIL import Image\nimport sys\nimport time\nimport heapq\nfrom PIL import",
                "stop_reason": "max_length",
            },
        ],
    },
    "cpp-code-generation": {
        "title": "C plus plus Code Generator",
        "description": "Text generator - C++ code generation examples",
        "generate_params": {
            "text": "#include <iostream>\nusing namespace std;\n\nint main() {\n  cout <<",
            "number_of_results": 4,
            "max_length": 100,
            "max_sentences": 0,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1,
            "seed": 0,
        },
        "results": [
            {
                "generated_text": '#include <iostream>\nusing namespace std;\n\nint main() {\n  cout << "Printing the first 3 numbers..." << endl;\n  cout << "1: 2, 3, 4" << endl;\n  cout << "2: 4, 3, 1" << endl;\n  cout << "3, 4, 1, 2" << endl;\n}\n\n#include <iostream>\n#include <string>\n#include <vector>\n#include <algorithm>\n#include <functional>\n#include <queue>\n#include <stack>\n#include <map>\n#include <set>\n#include <bitset>\n#include <numeric>\n#include',
                "stop_reason": "max_length",
            },
            {
                "generated_text": '#include <iostream>\nusing namespace std;\n\nint main() {\n  cout << "ABC 123,456.789" << endl;\n  cout << "ABC 123.456,789" << endl;\n  cout << "ABC 123.456,789.000" << endl;\n  cout << "ABC 123.456,789.000" << endl;\n  cout << "ABC 123.456,789.000" << endl;\n  cout << "ABC 123.456,789.000" << endl;\n  cout << "ABC 123.456,789.000" << endl;\n  cout << "ABC 123.456',
                "stop_reason": "max_length",
            },
            {
                "generated_text": '#include <iostream>\nusing namespace std;\n\nint main() {\n  cout << "This is a test" << endl;\n  cout << "This is another test" << endl;\n  cout << "This is a third test" << endl;\n  cout << "This is a fourth test" << endl;\n  return 0;\n}\n\n// This is the code that will be run when you run the program\n// You can add as many code lines as you want\n// After that, just click on Run Code. Code will be executed.\n// You can also save your changes by clicking on Saved.\n//',
                "stop_reason": "max_length",
            },
            {
                "generated_text": '#include <iostream>\nusing namespace std;\n\nint main() {\n  cout << "This is a test" << endl;\n  return 0;\n}\n\n/*\n * To change this license header, choose License Headers in Project Properties.\n * To change this template file, choose Tools | Templates\n * and open the template in the editor.\n */\n/**\n *\n * @author joshua\n */\nclass C {\n public:\n  C() {\n    cout << "ctor\\n";\n  }\n  ~C() {\n    cout << "dtor\\n";\n  }\n  void print() {',
                "stop_reason": "max_length",
            },
        ],
    },
    "jquery-code-generation": {
        "title": "JQuery Code Generator",
        "description": "Text generator - JQuery code generation examples",
        "generate_params": {
            "text": '$(document).ready(function(){\n  $("p").click',
            "number_of_results": 4,
            "max_length": 100,
            "max_sentences": 0,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1,
            "seed": 0,
        },
        "results": [
            {
                "generated_text": '$(document).ready(function(){\n  $("p").click(function(){\n    $(this).next("ul").slideToggle();\n    $(this).toggleClass("active");\n  });\n  $("ul").hide();\n  $("ul").first().slideDown();\n  $("ul").first().toggleClass("active");\n  $("ul").show();\n});\n$("ul").hide();\n$("ul").last().slide',
                "stop_reason": "max_length",
            },
            {
                "generated_text": "$(document).ready(function(){\n  $(\"p\").click(function(){\n    var t = $(this);\n    var tname = t.attr('id');\n    var tvalue = t.text();\n    var ttext = t.text();\n    var tclass = t.attr('class');\n    var tstyle = t.attr('style');\n    var tdata = t.data('target');\n    var tdata2 = t.data('target2');\n   ",
                "stop_reason": "max_length",
            },
            {
                "generated_text": '$(document).ready(function(){\n  $("p").click(function(){\n    $("body").append("<div id=\'mousepad\'>" + $(this).text() + "</div>");\n  });\n  $("#mousepad").click(function(){\n    $("#mousepad").remove();\n  });\n});\n\n$("p").click(function(){\n  $("body").append("<div id=\'mousepad\'>" + $(this).',
                "stop_reason": "max_length",
            },
            {
                "generated_text": '$(document).ready(function(){\n  $("p").click(function(){\n    var $div = $(this).parent();\n    var $divName = $div.attr("rel");\n    var $divParent = $div.parent();\n    var $divText = $div.text();\n    var $divTitle = $div.attr("title");\n    var $divLink = $div.find("a").attr("href");\n    $divParent.removeChild($div',
                "stop_reason": "max_length",
            },
        ],
    },
    "c-code-generation": {
        "title": "C Code Generator",
        "description": "Text generator - C code generation examples",
        "generate_params": {
            "text": "#include <stdio.h>\n\nint main() {\n  printf(",
            "number_of_results": 4,
            "max_length": 100,
            "max_sentences": 0,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1,
            "seed": 0,
        },
        "results": [
            {
                "generated_text": "#include <stdio.h>\n\nint main() {\n  printf(\"I'm a line\\nI'm a line\\nI'm a line\\nI'm a line\\nI'm a line\\nI'm a line\\nI'm a line\\nI'm a line\\nI'm a line\\nI'm a line\\nI'm a line\\nI'm a line\\nI'm a line\\nI'm a line\\nI'm a line\\nI'm a line\\nI'm a line\\nI'm a line\\nI'm a line\\nI'm a line\\nI'm a line\\nI'm a line\\nI'm a line\\nI'm a line\\nI'm a line\\n",
                "stop_reason": "max_length",
            },
            {
                "generated_text": '#include <stdio.h>\n\nint main() {\n  printf("Hello world!\\n");\n  return 0;\n}\n\nThe program will print Hello world! to the standard output. Note that the program will not be able to use printf() to write to a file, because printf() uses standard output. You need to use printf() to write to a file using functions like write() or fwrite(). For more information on how to write to a file, see How to Write to a File. You can also try running the program without the return 0 line at',
                "stop_reason": "max_length",
            },
            {
                "generated_text": '#include <stdio.h>\n\nint main() {\n  printf("Hello, world!\\n");\n  return 0;\n}\n\n// This is the same program, but compiled with gcc -O\n// gcc -O main.c\n\n// gcc -O main.c &&./a.out\n\n// gcc -O main.c && echo $? == 0\n\n// gcc -O main.c && echo $? == 1\n\n// gcc -O main.c && echo $? == 2\n\n// gcc -O main.c && echo $?',
                "stop_reason": "max_length",
            },
            {
                "generated_text": '#include <stdio.h>\n\nint main() {\n  printf("hello world!\\n");\n  return 0;\n}\n\n#include <bits/stdc++.h>\nusing namespace std;\n\nint main() {\n  long long int a = 2, b = 3, c = 4, d = 5, e = 6, f = 7;\n  cout << a << " " << b << " " << c << " " << d << " " << e << " " << f << endl;\n  return 0;\n}\n\n#include <bits/stdc++.',
                "stop_reason": "max_length",
            },
        ],
    },
    "sql-code-generation": {
        "title": "SQL Code Generator",
        "description": "Text generator - SQL code generation examples",
        "generate_params": {
            "text": "-- Select the least selling product from the products table \n-- query.sql\nSELECT MIN",
            "number_of_results": 4,
            "max_length": 100,
            "max_sentences": 0,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1,
            "seed": 0,
        },
        "results": [
            {
                "generated_text": "-- Select the least selling product from the products table \n-- query.sql\nSELECT MIN(product_id) as product_id FROM products_table GROUP BY product_id\n\n -- run the query\n cte = connection.cursor()\n cte.execute(query.sql)\n row = cte.fetchone()\n row.product_id\n\n print(row.product_id) -- select the least selling product from the products table\n print(row.product_id) -- select the least selling product from the products table\n print(row.product_id) -- select the least selling product from the products",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "-- Select the least selling product from the products table \n-- query.sql\nSELECT MIN(product_id) as product_id FROM products GROUP BY product_id\n\n-- Get the product_id from the query result\nproduct_id = query.fetchone()[0]\n\n# Insert the product_id into the products table\ninsert into products (product_id) values (product_id);\n\n# Update the product count\nupdate products set product_count = product_count + 1 where product_id = product_id;\n\n# Update the sales count\nupdate products set sales_count = sales_count + 1 where product_id =",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "-- Select the least selling product from the products table \n-- query.sql\nSELECT MIN(product_id) FROM products WHERE product_id!= '' AND product_id!= '-1' AND product_id!= '0' AND product_id!= '-2' AND product_id!= '-3' AND product_id!= '-4' AND product_id!= '-5' AND product_id!= '-6' AND product_id!= '-7' AND product_id!= '-8' AND product_id!= '-9' AND product_id!= '-10' AND product_id!",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "-- Select the least selling product from the products table \n-- query.sql\nSELECT MIN(product_id) FROM products\n\n-- SELECT product_id FROM products WHERE product_id > 0\n\n-- Select the product_id where product_id is greater than 0\n-- query.sql\nSELECT product_id FROM products WHERE product_id > 0\n\n-- Select the product_id where product_id is greater than 0\n-- query.sql\nSELECT product_id FROM products WHERE product_id > 0\n\n-- Select the product_id where product_id is greater than 0\n-- query.sql\nSELECT product_id FROM products WHERE",
                "stop_reason": "max_length",
            },
        ],
    },
    "bootstrap-css-code-generation": {
        "title": "Bootstrap Code Generator",
        "description": "Text generator - Bootstrap code generation examples",
        "generate_params": {
            "text": '<!-- bootstrap css code to render todo sample app -->\n<h1>Example heading <span class="badge bg-',
            "number_of_results": 4,
            "max_length": 100,
            "max_sentences": 0,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1,
            "seed": 0,
        },
        "results": [
            {
                "generated_text": '<!-- bootstrap css code to render todo sample app -->\n<h1>Example heading <span class="badge bg-white" data-count="2">2 items to complete</span></h1>\n<ul>\n  <li>Item 1</li>\n  <li>Item 2</li>\n  <li>Item 3</li>\n  <li>Item 4</li>\n  <li>Item 5</li>\n  <li>Item 6</li>\n</ul>\n<!-- bootstrap css code to render todo sample app -->\n<h1>Example heading <span class="badge bg-white" data-count="2">2 items to complete</span></h1>\n<ul>\n  <li>Item 1</li>\n  <li>Item 2</li>\n  <li>Item',
                "stop_reason": "max_length",
            },
            {
                "generated_text": '<!-- bootstrap css code to render todo sample app -->\n<h1>Example heading <span class="badge bg-blue">2</span></h1>\n<p>\n    This is an example todo list with a single todo.\n    Click on the checkbox to check it.\n    Click on the checkbox to uncheck it.\n</p>\n<hr>\n<!-- Bootstrap css code to render todo sample app -->\n<h1>Example heading <span class="badge bg-blue">2</span></h1>\n<p>\n    This is an example todo list with multiple todo.\n    Click on the checkbox to check it.\n    Click on the checkbox to uncheck it',
                "stop_reason": "max_length",
            },
            {
                "generated_text": '<!-- bootstrap css code to render todo sample app -->\n<h1>Example heading <span class="badge bg-blue">1</span> of 4</h1>\n\n<!-- Bootstrap JS to render todo sample app -->\n<script src="https://code.getbootstrap.com/js/2.3.3/dist/js/bootstrap.min.js"></script>\n\n<!-- todo sample app code -->\n<div class="alert alert-success">\n  <strong>Success!</strong>\n  This is a todo list\n</div>\n\n<!-- todo sample app css code -->\n<!-- todo sample app css -->\n<!-- todo sample app css -->\n<',
                "stop_reason": "max_length",
            },
            {
                "generated_text": '<!-- bootstrap css code to render todo sample app -->\n<h1>Example heading <span class="badge bg-light-blue">1.1</span></h1>\n<hr>\n<!-- todo sample app -->\n<div class="alert alert-success">\n    <strong>Example message</strong>\n</div>\n<hr>\n\n<!-- todo sample app -->\n<div class="alert alert-success">\n    <strong>Example message</strong>\n</div>\n<hr>\n\n<!-- todo sample app -->\n<div class="alert alert-success">\n    <strong>Example message</strong>\n</div>\n<hr>\n\n<!-- todo sample app -->',
                "stop_reason": "max_length",
            },
        ],
    },
    "css-code-generation": {
        "title": "CSS Code Generator",
        "description": "Text generator - CSS code generation examples",
        "generate_params": {
            "text": "h1 {\n  color: white;\n  text-align: ",
            "number_of_results": 4,
            "max_length": 100,
            "max_sentences": 0,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1,
            "seed": 0,
        },
        "results": [
            {
                "generated_text": "h1 {\n  color: white;\n  text-align: center;\n  text-decoration: underline;\n}\n\n#logo {\n  position: fixed;\n  top: 0;\n  left: 0;\n  right: 0;\n  bottom: 0;\n  background: #00a6ff;\n  padding: 20px 20px 20px 0;\n  max-width: 80%;\n  max-height: 80%;\n  max-height: 80%;\n}\n\n#logo img {\n  max-width: 80%;\n  max-height: 80%;\n  max-height: 80%;\n}\n\n#logo img {\n  max-width: 80%;\n  max-height: 80%;\n}\n<!DOCTYPE",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "h1 {\n  color: white;\n  text-align: center;\n  margin-top:20px;\n  padding:10px;\n  background: url(https://images-na.ssl-images-amazon.com/images/I/51CXN0T7LZ4.jpg) repeat-x;\n}\n\nh2 {\n  color: white;\n  text-align: center;\n  margin-top:20px;\n  padding:10px;\n  background: url(https://images-na.ssl-images-amazon.com/images/I/51CXN0T7LZ4.jpg) repeat-x;\n}\n\nh3 {\n ",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "h1 {\n  color: white;\n  text-align: center;\n}\nh2 {\n  color: white;\n  text-align: center;\n}\nh3 {\n  color: white;\n  text-align: center;\n}\nh4 {\n  color: white;\n  text-align: center;\n}\nh5 {\n  color: white;\n  text-align: center;\n}\nh6 {\n  color: white;\n  text-align: center;\n}\nbody {\n  background-color: #f1f1f1;\n  color: #999;\n}\n\na {\n  text-decoration: none;\n  color: #999;\n}\na:hover {\n  text-decoration: underline;\n  color: #99",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "h1 {\n  color: white;\n  text-align: center;\n  text-decoration: none;\n  text-size:1.5em;\n  vertical-align: middle;\n}\n\n#container {\n  width: 200px;\n  height: 200px;\n  margin:0 auto ;\n  background:#f2f2f2;\n}\n\n#text {\n  background: #f2f2f2;\n  border:2px solid #ccc;\n}\n\n#text1 {\n  background: #f2f2f2;\n  border:2px solid #ccc;\n  color: red;\n  border-bottom:2px solid red;\n}\n\n#text2",
                "stop_reason": "max_length",
            },
        ],
    },
    "text-generation-from-images": {
        "title": "Text generation from image content examples",
        "description": "Text generator - text generation from images examples",
        "generate_params": {
            "text": "feeling https://static.text-generator.io/static/img/h.png because",
            "number_of_results": 4,
            "max_length": 100,
            "max_sentences": 0,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1,
            "seed": 0,
        },
        "results": [
            {
                "generated_text": "feeling https://static.text-generator.io/static/img/h.png because I need to be happy and green to be happy. feeling an illustration of a smiley face with a red background https://static.text-generator.io/static/img/r.png because I need to be angry and red to be angry. feeling an illustration of a smiley face with a blue background https://static.text-generator.io/static/img/b.png because I need to be sad and blue to be sad. feeling an illustration of a smiley face with a purple background https://static.text",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "feeling https://static.text-generator.io/static/img/h.png because of its green background and its smiley face. smiley-face with a green background - feel free to use this feeling free to use this feeling free to use this feeling free to use this feeling free to use this feeling free to use this feeling free to use this feeling free to use this feeling free to use this feeling free to use this feeling free to use this feeling free to use this feeling free to use this feeling free to use this feeling free to use this feeling free to use this feeling free to",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "feeling https://static.text-generator.io/static/img/h.png because i don't know how to make an emoji in text generator. so that's why i used this image. but i do know how to make an emoji. please ignore the emoji. - feel free to ask me any question - i am happy to answer them! 😉😊😊😊😊😊😊😊😊😊😊😊😊😊😊😊😊😊😊😊😊😊😊�",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "feeling https://static.text-generator.io/static/img/h.png because you are feeling happy, happy, happy. feeling an illustration of a smiley face with a blue background https://static.text-generator.io/static/img/j.png because you are feeling joyful, joyful, joyful. feeling an illustration of a smiley face with a purple background https://static.text-generator.io/static/img/k.png because you are feeling kind, kind, kind. feeling an illustration of a smiley face with a red background https://static.text-generator.",
                "stop_reason": "max_length",
            },
        ],
    },
    "text-generation-from-emoji-conversations": {
        "title": "Text generation from emoji and conversations examples",
        "description": "Text generator - text generation from emoji images examples - text generator analyses links",
        "generate_params": {
            "text": "feeling https://static.text-generator.io/static/img/s.png because",
            "number_of_results": 4,
            "max_length": 100,
            "max_sentences": 4,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1.17,
            "seed": 0,
        },
        "results": [
            {
                "generated_text": "feeling https://static.text-generator.io/static/img/s.png because i feel like crying and i don't know why, my heart is breaking and all the feelings are hurtful to me. I am upset and angry at life for leaving me in pain but not giving any answer about what happened and when it will happen again or if it ever happens again. The illustrations of faces can be found here http://imgur.com/dYzRr8j.png no one understands how hard this feels so please take care of yourself my love ❤️❤️�",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "feeling https://static.text-generator.io/static/img/s.png because my heart is broken i feel like crying every time you look at me smile and cry every time you go by your face is just so ugly that it's beautiful my heart is breaking i can't breathe when you're gone i want to scream out loud but the tears are running down my cheek i hate myself for being this weak my heart feels empty without you all i can do now is cry my heart's in pain and it hurts bad i know its over but i still miss you don't know how much i",
                "stop_reason": "max_length",
            },
            {
                "generated_text": 'feeling https://static.text-generator.io/static/img/s.png because the word "sad" is not in the list above, and its definition doesn\'t fit any existing words in this list. no image found for your selection. no image found for your selection. no image found for your selection.',
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": "feeling https://static.text-generator.io/static/img/s.png because the app crashed and i want to fix it, so i need your help. please contact me if you have any questions or concerns about my work. thanks! - jpg (255 x 255) thumb|center|200px A screenshot from the app I was working on at the time that crashed when trying to change the background color for some reason.",
                "stop_reason": "max_sentences",
            },
        ],
    },
    "html-alt-title-attribute-generator-for-images": {
        "title": "HTML alt attribute generator for images SEO",
        "description": "Text generator - HTML attribute code generation examples",
        "generate_params": {
            "text": '<img src="https://static.text-generator.io/static/img/fairy3.jpeg" alt="',
            "number_of_results": 4,
            "max_length": 100,
            "max_sentences": 4,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1.14,
            "seed": 0,
        },
        "results": [
            {
                "generated_text": '<img src="https://static.text-generator.io/static/img/fairy3.jpeg" alt="A Gargoyle Figurine in a Blue Outfit With a Gold Crown on Its Head" />\n\nI am going to make a gargoyle figurine for my collection of fairy dolls and it is an appropriate place for me to start. I have been collecting dolls, so this is the first one that comes to mind.  The second option would be something like a dragon or a unicorn. I know how to draw a gargoyle, so I can make a good drawing from which to sculpt',
                "stop_reason": "max_length",
            },
            {
                "generated_text": '<img src="https://static.text-generator.io/static/img/fairy3.jpeg" alt="Gargoyle figurine"> <figcaption>A gargoyle figurine in a blue outfit with a gold crown on its head</figcaption> <img src="https://i.imgur.com/JjTm7UO.png" alt="" class="fr-alt2"> <a href="https://twitter.com/textgenerator" target="_blank"><img src="https://static.text-generator.io/static/img/twitter-logo.svg" alt="Twitter logo"></a> <figcaption>The Twitter logo</figcaption> <img src="https://static.',
                "stop_reason": "max_length",
            },
            {
                "generated_text": '<img src="https://static.text-generator.io/static/img/fairy3.jpeg" alt="gargoyle figurines" />\n gárgolas (plural gárgolas) is the plural of gárgola, which means gargoyle. Gargoyles are fictional characters from Spain and Portugal who were originally thought to be monsters. They appear as winged creatures that can either be human or animal-like. The name comes from the Greek word for \'gorge\' (γάργωλον)',
                "stop_reason": "max_sentences",
            },
            {
                "generated_text": '<img src="https://static.text-generator.io/static/img/fairy3.jpeg" alt="Gargoyles"> Gargoyles are mythological creatures of folklore and popular culture, usually depicted as giant birds or animals with human-like faces. They were the symbol of evil in many cultures throughout history. They may be anthropomorphic to make them look more humanoid. Gargoyles have been known since ancient times, appearing in many different cultures around the world.',
                "stop_reason": "max_sentences",
            },
        ],
    },
    "multiple-images-question-answering": {
        "title": "Generate Text about multiple images",
        "description": "Text generator - Generate Text and answer questions about multiple images",
        "generate_params": {
            "text": "Which fairy do you think is most feminine?\n1: https://static.text-generator.io/static/img/fairy1.jpeg\n2: https://static.text-generator.io/static/img/fairy2.jpeg\n3: https://static.text-generator.io/static/img/fairy3.jpeg\nA:",
            "number_of_results": 4,
            "max_length": 100,
            "max_sentences": 0,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1.14,
            "seed": 0,
        },
        "results": [
            {
                "generated_text": "Which fairy do you think is most feminine?\n1: https://static.text-generator.io/static/img/fairy1.jpeg\n2: https://static.text-generator.io/static/img/fairy2.jpeg\n3: https://static.text-generator.io/static/img/fairy3.jpeg\nA: 3\n3\n\n\n\n\n\n\n\n\nA 2 A 2 A 2 B 3 A 1 B 3 A 3 C 3 A 2 A 2 A 2 A 3 C 3 A 2 A 3 A 3 A 3 A 3 B A 3 A 3 A 3 A 3 A 3 A 3 A 3 A 3 A 3 A 3 A 3 A 3 A 3 A 3 A 3 A 3 A 3 A 3 A 3 A 3 A 3 A 3 A 3 A 3 A 3 A 3 A 3 A 3 A 3",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Which fairy do you think is most feminine?\n1: https://static.text-generator.io/static/img/fairy1.jpeg\n2: https://static.text-generator.io/static/img/fairy2.jpeg\n3: https://static.text-generator.io/static/img/fairy3.jpeg\nA: 3\n\nA Fairy 3 is most feminine of all. A Fairy 3 is most feminine of all. - Fairy 3 is most feminine of all. Yes! Yes! Yes! Yes! Yes! Yes! Yes! Yes! Yes! Yes! Yes! Yes! Yes! Yes! Yes! Yes! Yes! Yes! Yes! Yes! Yes! Yes! Yes! Yes! Yes! Yes! Yes! Yes! No. Yes! Yes! Yes! Yes! Yes! Yes",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Which fairy do you think is most feminine?\n1: https://static.text-generator.io/static/img/fairy1.jpeg\n2: https://static.text-generator.io/static/img/fairy2.jpeg\n3: https://static.text-generator.io/static/img/fairy3.jpeg\nA: 3, A 3, B 2 A 3, B 2 A 3, C 3 B 2 A 3, D 3 A 3, E 3 B 2 A 3, F 3 A 3, G A 3, H A 3 B 2 A 3 A 3, I A 3 C 3 A 3 A 3, J B 2 A 3 B 2 A 3, K A 3 B 2 A 3 A 3 A 3, L A 3 C 3 A 3 A 3 A 3 A 3 A 3 A",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Which fairy do you think is most feminine?\n1: https://static.text-generator.io/static/img/fairy1.jpeg\n2: https://static.text-generator.io/static/img/fairy2.jpeg\n3: https://static.text-generator.io/static/img/fairy3.jpeg\nA: 3\n3.3.4 Fairies are generally considered to be female, and therefore more feminine than any other type of creature or animal. Fairies are female.3.3.4.5 Yes Fairies are generally considered to be female, and therefore more feminine than any other type of creature or animal. Fairies are female.3.3.4 Yes Fairies are generally considered to be female, and therefore more feminine than any other type of creature or animal. Fairies are female",
                "stop_reason": "max_length",
            },
        ],
    },
    "upsell-content-generator": {
        "title": "Generate Text for Sales",
        "description": "Text generator - UpSelling Text Generator Examples",
        "generate_params": {
            "text": "Accelerate your startup’s growth with NVIDIA Inception\u202f \n\nThousands of startups around the world use NVIDIA technologies to accelerate their growth and reimagine advanced solutions in AI, deep learning, data science, HPC, networking, graphics, AR/VR, and gaming.\u202fNVIDIA Inception is designed to help startups build their products and grow faster. Members get engineering guidance",
            "number_of_results": 4,
            "max_length": 100,
            "max_sentences": 0,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1.14,
            "seed": 0,
        },
        "results": [
            {
                "generated_text": "Accelerate your startup’s growth with NVIDIA Inception\u202f \n\nThousands of startups around the world use NVIDIA technologies to accelerate their growth and reimagine advanced solutions in AI, deep learning, data science, HPC, networking, graphics, AR/VR, and gaming.\u202fNVIDIA Inception is designed to help startups build their products and grow faster. Members get engineering guidance and access to leading-edge technology from a network of experts who can connect you with customers and partners. Learn more at nvidiasinception.com. Get started now!   Register for an account with us so that we may contact you about NVIDIA Inception. You will need to verify your identity before proceeding.   Contact Support if there are issues accessing your account. This email address has already been used. Please choose another one. Email Address: Password: Remember Me? Please enter the",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Accelerate your startup’s growth with NVIDIA Inception\u202f \n\nThousands of startups around the world use NVIDIA technologies to accelerate their growth and reimagine advanced solutions in AI, deep learning, data science, HPC, networking, graphics, AR/VR, and gaming.\u202fNVIDIA Inception is designed to help startups build their products and grow faster. Members get engineering guidance from industry experts for free, access to tools, and a community that helps them scale. Startups also have access to NVIDIA's corporate innovation ecosystem that includes an array of partners. For more information about how you can join NVIDIA Inception, visit https://nvidia.com/inception/. To learn more about NVIDIA Inception, click here. Find us on LinkedIn and Twitter. We will be posting links to useful articles there as well! Facebook Messenger: Connect with us on Messenger by clicking",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Accelerate your startup’s growth with NVIDIA Inception\u202f \n\nThousands of startups around the world use NVIDIA technologies to accelerate their growth and reimagine advanced solutions in AI, deep learning, data science, HPC, networking, graphics, AR/VR, and gaming.\u202fNVIDIA Inception is designed to help startups build their products and grow faster. Members get engineering guidance, access to a global network of experts, early-stage funding opportunities, and marketing support. Join the program now! Learn more about NVIDIA Inception here. Read more about NVIDIA Inception ». NVIDIA partners with tech companies like you to provide an open innovation platform for technology developers to collaborate on new ideas and create breakthroughs together. Find out how you can join our ecosystem today by contacting us at nvidiasupport@nvidia.com. Contact Us ». You’ll find",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Accelerate your startup’s growth with NVIDIA Inception\u202f \n\nThousands of startups around the world use NVIDIA technologies to accelerate their growth and reimagine advanced solutions in AI, deep learning, data science, HPC, networking, graphics, AR/VR, and gaming.\u202fNVIDIA Inception is designed to help startups build their products and grow faster. Members get engineering guidance from experts, access to funding opportunities, and a chance to connect directly with customers. To learn more, visit www.nvidiainception.com. Go to our website to apply for membership at nvidia.com/startups. Apply here. If you have questions about this program or need assistance applying, email nvida.com/startups support@nvidia.com. Visit https://www.youtube.com/user/NvidiaInception to watch videos on how to make an application. You can also",
                "stop_reason": "max_length",
            },
        ],
    },
    "technical-content-generator": {
        "title": "Generate Text for Technical Content",
        "description": "Text generator - Technical Content Text Generator - UPS product description",
        "generate_params": {
            "text": "For a natural disaster scenario where power supply may be interrupted for days or weeks, a generator is usually the only option to",
            "number_of_results": 4,
            "max_length": 100,
            "max_sentences": 0,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1.14,
            "seed": 0,
        },
        "results": [
            {
                "generated_text": "For a natural disaster scenario where power supply may be interrupted for days or weeks, a generator is usually the only option to keep essential systems running. It can be difficult to get your car started if you are miles from home and need to use it as an emergency shelter. A generator will help you stay warm, dry, and alive by providing electricity and heat. To prepare in case of a natural disaster, purchase a reliable generator that has enough fuel capacity (and space) to meet your needs.  If you live in a rural area, consider buying a portable diesel generator. Portable generators are easier to transport than stationary ones.",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "For a natural disaster scenario where power supply may be interrupted for days or weeks, a generator is usually the only option to provide electricity. In some cases, solar panels and wind turbines can supplement this need. But generators still have their limitations in terms of size, cost, efficiency, etc. A battery bank may help resolve these issues by providing backup power when your utility fails. A generator can also be used as an alternative to another form of energy if it runs out due to a severe storm. Batteries may not be able to completely replace the utility but they can offer some relief. If you live near a large",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "For a natural disaster scenario where power supply may be interrupted for days or weeks, a generator is usually the only option to maintain essential services. An inverter will allow you to run your appliances while maintaining a stable electrical system. The use of an inverter allows appliance manufacturers to produce smaller and more efficient units that consume less energy. Inverters are available in different sizes, from portable AC generators with capacities as low as 1000 Watt up to large commercial inverters designed for home use. It should also be noted that most inverters can be used with almost any type of appliance. A variety of inverter",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "For a natural disaster scenario where power supply may be interrupted for days or weeks, a generator is usually the only option to keep electrical equipment operational. This includes refrigerators, air conditioners, heat pumps, and water pumps. If you have an RV, then this will also include heating systems. Without electricity, these devices cannot work as expected. In many cases, generators can be purchased at your local home improvement store, but they are not always available. You can also purchase them online. The price of a portable generator depends on its size and capabilities; however, you should expect to pay anywhere from $300-$6000 USD",
                "stop_reason": "max_length",
            },
        ],
    },
    "game-character-chatbot": {
        "title": "Generate Text for in game chatbots",
        "description": "Text generator - Game Chat Text Generator",
        "generate_params": {
            "text": "Miad: I've been followed by the orcs for weeks, they wont stop, i managed to",
            "number_of_results": 4,
            "max_length": 100,
            "max_sentences": 0,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1.14,
            "seed": 0,
        },
        "results": [
            {
                "generated_text": "Miad: I've been followed by the orcs for weeks, they wont stop, i managed to get away but now they're after me again. I need your help! My friends are all dead and I'm running out of time! Please come save me! F: Sounds like you're in trouble. Let's go there right now. You should be safe with us until you can find a new home. Come along! Mia: No thank you. I can't risk going back into that dungeon. F: Why not? Mia will never leave the old dungeon. She has no other choice if she wants",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Miad: I've been followed by the orcs for weeks, they wont stop, i managed to kill a few of them but they keep on coming back. I am not sure if its just me but they are becoming more powerful and more aggressive now. Help! - Orc Follower (voice) - WoW Classic MMO Gameplay Video Reviews - YouTube Myad is being attacked by orcs. They have been following him for some time and seem very angry. He must be getting stronger. He's going into battle. This video review was made at WoW Classic. The game is",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Miad: I've been followed by the orcs for weeks, they wont stop, i managed to kill a few but its still annoying. What can I do? I have an account with you guys! Tell me how to get rid of them :O I want to play minecraft again 😢😭😭😭😭😭😭😭😭😭😭😭😭😭😭😭😭😭😭😭😭😭😭😭😭😭😭😭😭😭😭�",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Miad: I've been followed by the orcs for weeks, they wont stop, i managed to escape once before but now i cant get out. Help me! - My dad's voice was all i could hear as I ran back into my room and closed the door behind me. Dad had been talking on his mobile phone, mum wasn't there so it must be the orcs again. I lay in bed and tried to ignore them thinking that maybe it would go away soon. But it didn't. Mom has never left home without us so I'm going to have to take care of her when she gets older",
                "stop_reason": "max_length",
            },
        ],
    },
}

# join openai examples
use_cases.update(openai_examples)
