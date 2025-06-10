import json
import os

import requests
import logging
from questions.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

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
    },
    "spanish-sentiment-analysis": {
        "title": "Spanish sentiment analysis - Text Generator API",
        "description": "Spanish tweet analysis - Decide si el sentimiento de un Tweet es positivo, neutral o negativo.",
        "generate_params": {
            "text": "Decide si el sentimiento de un Tweet es positivo, neutral o negativo.\n\nTweet: \"¡Me encantó la nueva película de Batman!\"\nSentimiento: ",
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
    },
    "email-writing": {
        "title": "Email writing - Text Generator API",
        "description": "Text Generator API for generating writing emails and getting work done",
        "generate_params": {
            "text": "The following email explains two things:\n"
            + "1) The writer, Andy, is going to miss work.\n"
            + "2) The receiver, Betty, is Andy's boss and can email if anything needs to be done.\n"
            + "\n"
            + "From: ",
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
    },
    "company-classification": {
        "title": "Company classification - Text Generator API",
        "description": "Text Generator API Company classification API examples - company industry and sector classification",
        "generate_params": {
            "text": "The following is a list of companies and the categories they fall into\n"
            + "\n"
            + "Facebook: Social media, Technology\n"
            + "Uber: Transportation, Technology, Marketplace\n"
            + "Mcdonalds: Food, Fast Food, Logistics, Restaurants\n"
            + "{example}:",
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
    },
    "alliteration-generator": {
        "title": "Alliteration Generator - Text Generator API",
        "description": "Text Generator API Alliteration prompt API examples - creativity and alliterations examples",
        "generate_params": {
            "text": "Find synonyms for words that can create alliterations.\n"
            + "\n"
            + "Sentence: The dog went to the store.\n"
            + "Alliteration: The dog drove to the department.\n"
            + "\n"
            + "Sentence: David wears a hat everyday.\n"
            + "Alliteration: David dons a derby daily.\n"
            + "\n"
            + "Sentence: The soap dries over night.\n"
            + "Alliteration: The soap shrivels succeeding sunset.\n"
            + "\n"
            + "Sentence: Sal throws shells over the water at the beach.\n"
            + "Alliteration:",
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
    },
    "song-generator": {
        "title": "Song Generator - Text Generator API",
        "description": "Song Generator API - musical lyrics prompt API examples - music generator",
        "generate_params": {
            "text": "VERSE:\n"
            + "Alas my love,\n"
            + "You do me wrong,\n"
            + "To cast me off discourteously,\n"
            + "for i have loved you so long,\n"
            + "delighting in your company.\n"
            + "\n"
            + "CHORDS:\n"
            + "Alas[Am] my[C] love,\n"
            + "you [G]do [Em]me wrong,\n"
            + "to [Am]cast me off dis[E]courteously,\n"
            + "for [Am]i have[C] loved[G] you [Em]so long,\n"
            + "de[Am]lighting in[E7] your [Am]company.\n"
            + "\n"
            + "VERSE:\n",
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
    },
    "book-review-generator": {
        "title": "Book Review Generator - Text Generator API",
        "description": "Book Review Generator API - musical lyrics prompt API examples - book review generator",
        "generate_params": {
            "text": "Title: Lovely War\n"
            + "Rating: 3/5\n"
            + "Quotes:\n"
            + '- "It was time for James and Hazel to get properly acquainted. Time to see if the magic of music and moonlight and graceful movement were all that they had shared, or if a grimy gray London dawn and a cheap cup of coffee could make them feel the same way."\n'
            + '- "Annihilation has its own je ne sais quoi. We’re all guilty of it. So spare me the sermons."\n'
            + '- "His mother’s letters are full of urgent warning. She grew up in Mississippi. \n'
            + "She knows about lynching. Aubrey wonders if he’ll die in his country before he \n"
            + 'ever gets the chance to die for his country. Either way, he’d rather not."\n'
            + '- "Whatever boost sixty captured miles might have brought to German morale was \n'
            + "erased by the chocolate in the BEF’s packs. War is morale. War is supply. War is \n"
            + 'chocolate."\n'
            + "Thoughts:\n"
            + "- Pacing felt awkward\n"
            + "- WW1 history felt accurate\n"
            + "- Didn't care too much for the story of the Gods\n"
            + "Review: A good book with well rounded characters, but the pacing felt super \n"
            + "awkward. The titles of the chapters showed which Greek God was speaking, but I was more interested in the WW1 tales than their relationships.\n"
            + "\n"
            + "'''\n"
            + "Title: Goodbye, Things\n"
            + "Rating: 4/5\n"
            + "Thoughts:\n"
            + "- very cleanly written\n"
            + "- read easily\n"
            + "- author did good research\n"
            + "Review:",
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
    },
    "headline-generator": {
        "title": "Headline Generator - Text Generator API",
        "description": "Headline Generator API - english news headlines API examples - text generation",
        "generate_params": {
            "text": "Topic: Britain, coronavirus, beaches\n"
            + "Headline: Videos show crowded beaches in Britain\n"
            + "\n"
            + "Topic: Apple, Big Sur, software\n"
            + "Headline: Apple promises faster software update installation with macOS Big Sur\n"
            + "\n"
            + "Topic: Artic, climate change, satellite\n"
            + "Headline: A Satellite Lets Scientists See Antarctica’s Melting Like Never Before\n"
            + "\n"
            + "Topic: "
            + "Chicago, restaurants, summer"
            + "\n"
            + "Headline:",
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
    },
    "product-name-generator": {
        "title": "Product Name Generator - Text Generator API",
        "description": "Product Name Generator API - product naming ideas generator API examples - text generation",
        "generate_params": {
            "text": "This is a product name generator. It takes a product's description and seed words, then outputs a list of potential product names.\n"
            + "\n"
            + "Product description: A complete home gym that can fit in any apartment.\n"
            + "Seed words: intelligent, aspirational, luxury, futuristic\n"
            + "Product names: InfinityHome, Quantum, FlexFit, Flight, FutureFit\n"
            + "\n"
            + "Product description: An affordable electric bike.\n"
            + "Seed words: Easy, eco-friendly, practical, dependable\n"
            + "Product names: Pegasus, Swifty, SunRunner, Wave, Amp\n"
            + "\n"
            + "Product description: A zero carbohydrate cereal that tastes great.\n"
            + "Seed words: fitness, healthy, keto, clean, tasty\n"
            + "Product names:",
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
    },
    "rhyming-generator": {
        "title": "Rhyme Generator - Text Generator API",
        "description": "Rhyme Generator API - ryming words poems somgs and ideas generator API examples",
        "generate_params": {
            "text": "A homophone is defined as a word that is pronounced the same as another word but \n"
            + "differs in meaning.\n"
            + "\n"
            + "Here is a list of homophones:\n"
            + "1. Accept/Except\n"
            + "2. Affect/Effect\n"
            + "3. Allude/Elude\n"
            + "4. Alter/Altar\n"
            + "5. A lot/Allot\n"
            + "\n"
            + 'Here\'s a list of homophones starting with the letter "b":\n',
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
    },
    "question-answering": {
        "title": "Question Answering - Text Generator API",
        "description": "Question Answering API - answer quewstions with the Text generator API",
        "generate_params": {
            "text": "Q: What is the definition of a linearly independent list?\n"
            + "A: A linearly independent list is a list of vectors that cannot be\n"
            + " expressed as a linear combination of other vectors in the list.\n"
            + " \n"
            + "Q: What is a basis of a vector space?\n"
            + "A: A basis of a vector space is a linearly independent list of vectors\n"
            + " that spans the vector space.\n"
            + "\n"
            + "Q: What is a spanning list of vectors in a vector space?\n"
            + "A: A spanning list of vectors in a vector space is list of vectors in\n"
            + " the vector space such that every vector in the vector space can be\n"
            + " written as a linear combination of the vectors in the spanning list.\n"
            + " \n"
            + "Q: What is the definition of a linear transformation?\n"
            + "A:",
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
    },
    "summarization": {
        "title": "Question Answering - Text Generator API",
        "description": "Question Answering API - answer quewstions with the Text generator API",
        "generate_params": {
            "text": "```\n"
            + "My second grader asked me what this passage means:\n"
            + "\n"
            + '"""\n'
            + "\n"
            + "Overnight trading for the NYSE Index futures was a bit volatile, "
            + "dropping by about 3% to the downside before moving sharply back to the upside. "
            + "Gold futures were unchanged and the E-mini NASDAQ 100 futures remained near "
            + "unchanged. The yield on the 10-year Treasury bond finished unchanged from its "
            + "close of 2.45% earlier today."
            + "\n"
            + "\n"
            + '"""\n'
            + "\n"
            + "I rephrased it for him, in plain language a second grader can understand:\n"
            + "\n"
            + '"""\n',
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
    },
    "code-translation": {
        "title": "Code Translation between languages - Text Generator API",
        "description": "transfer code between languages with Text Generator API - Python to Ruby code examples",
        "generate_params": {
            "text": "Python:\n"
            + "list[::-1]\n"
            + "Ruby:\n"
            + "list.reverse\n"
            + "\n"
            + "Python:\n"
            + "list[1:4]\n"
            + "Ruby:\n"
            + "list[1..4]\n"
            + "\n"
            + "Python:\n"
            + 'print("Hello World")\n'
            + "Ruby:\n"
            + 'puts "Hello World"\n'
            + "\n"
            + "Python:\n"
            + 'fruits = ["apple","banana","cherry"]\n'
            + "for x in fruits:\n"
            + "print(x)\n"
            + "Ruby:\n"
            + 'fruit = ["apple", "banana", "cherry"]\n'
            + "each {|x| print x } \n"
            + "\n"
            + "Python:\n"
            + 'fruits = ["apple","banana","cherry"]\n'
            + "a = list(fruits)\n"
            + "print(a)\n"
            + "a.reverse()\n"
            + "print(a)"
            + "\n"
            + "Ruby:\n",
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
    },
    "translation": {
        "title": "Translation between languages - Text Generator API",
        "description": "transfer between languages with Text Generator API - english to french example",
        "generate_params": {
            "text": "English: I do not speak French.\n"
            + "French: Je ne parle pas français.\n"
            + "\n"
            + "English: See you later!\n"
            + "French: À tout à l'heure!\n"
            + "\n"
            + "English: Where is a good restaurant?\n"
            + "French: Où est un bon restaurant?\n"
            + "\n"
            + "English: What rooms do you have available?\n"
            + "French:",
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
    },
    "estimation": {
        "title": "Estimation - Text Generator API",
        "description": "estimate quantity with Text Generator API - iphone cost example",
        "generate_params": {
            "text": "Lower and upper bound for each quantity:\n"
            + "\tNumber of cars in New York: 1500000 to 2500000\n"
            + "\tNumber of cars in San Francicso: 300000 to 600000\n"
            + "\tHeight of Empire State building: 1400 to 1500 feet\n"
            + "\tLength of average car: 4 to 4.5 meters\n"
            + "\tPopulation of Germany: 80 to 85 million\n"
            + '\t"How much does the iPhone XI cost?":',
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
    },
    "idea-generator": {
        "title": "Idea Generator - Text Generator API",
        "description": "ideas generator Text Generator API - movie plots ",
        "generate_params": {
            "text": "Here is a list of 100 interesting ideas for new movie plots. Each plot is "
            + "described with a title and a summary paragraph:\n"
            + "\n"
            + "1. The Bird. \n"
            + "A woman realizes that her pet bird is actually highly intelligent and able to communicate. The bird turns out to be a secret agent working for the CIA. The woman has to keep the bird's secret.\n"
            + "\n"
            + "2.",
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
    },
    "tweets-generator": {
        "title": "Tweet Generator - Text Generator API",
        "description": "Tweets Text Generator API - programming tweets example",
        "generate_params": {
            "text": "My favorite programming tweets:\n"
            + "-------\n"
            + "I asked @ilyasut how to set neural network init. He accidentally replied with a poem:\n"
            + "You want to be on the edge of chaos\n"
            + "Too small, and the init will be too stable, with vanishing gradients\n"
            + "Too large, and you'll be unstable, due to exploding gradients\n"
            + "You want to be on the edge\n"
            + "-------\n"
            + "I've been programming for 10 years now. Still feels like magic out of a fantasy: say the words exactly right, and watch your intent get carried out; say the words slightly wrong, and things go haywire. Feeling of wonder and joy hasn't faded one bit.\n"
            + "-------\n"
            + "Web programming is the science of coming up with increasingly complicated ways of concatenating strings.\n"
            + "-------\n"
            + "If you ever feel alone in this world, read your firewall logs. Problem solved :)\n"
            + "-------\n"
            + "Always wanted to travel back in time to try fighting a younger version of yourself? Software development is the career for you!\n"
            + "-------\n"
            + 'After 17 years as a professional developer, it seems that the answer to every programming question is "it depends"\n'
            + "-------\n",
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
    },
    "poem-generator": {
        "title": "Poem Generator - Text Generator API",
        "description": "Poem Text Generator API - poem example",
        "generate_params": {
            "text": "Who trusted God was love indeed\n"
            + "And love Creation’s final law\n"
            + "Tho’ Nature, red in tooth and claw\n"
            + "With ravine, shriek’d against his creed.\n"
            + "The hills are shadows, and they flow\n"
            + "From form to form, and nothing stands;T\n"
            + "hey melt like mist, the solid lands,\n"
            + "Like clouds they shape themselves and go.\n"
            + "----\n",
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
    },
    "famous-person-text-generation": {
        "title": "Famous person - Text Generator API",
        "description": "Text generator - mark zuckerberg conversation text generation example",
        "generate_params": {
            "text": "The following is a transcript of a conversation between Steve, a computer science student, "
            + "and Mark Zuckerberg. Mark Zuckerberg is an American media magnate, internet entrepreneur, and philanthropist. "
            + "He is known for co-founding Facebook, Inc. and serves as its chairman, chief executive officer,"
            + " and controlling shareholder.\n",
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
    },
    "java-code-generation": {
        "title": "Java Code Generator",
        "description": "Text generator - Java code generation example",
        "generate_params": {
            "text": "Write a program to remove duplicates from an array in Java without using the Java Collection API. The array can be an array of String, Integer or Character, your solution should be independent of the type of array. "
            + "\nsolution.java\n"
            + "import java.util.List; \n"
            + "public class RemoveDuplicates {\n"
            + "  public static List[] removeDuplicates(",
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
    },
    "php-code-generation": {
        "title": "PHP Code Generator",
        "description": "Text generator - PHP code generation example",
        "generate_params": {
            "text": """<?php
class Fruit {
  public $name;
  public $color;

  function __construct($name) {
    $this->name = $name;
  }
  function get_name() {""",
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
    },
    "c-sharp-code-generation": {
        "title": "C Sharp Code Generator",
        "description": "Text generator - C Sharp code generation example",
        "generate_params": {
            "text": """using System;

namespace HelloWorld
{
  class Program
  {
    static void Main(string[] args)
    {
      """,
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
    },
    "pytorch-code-generation": {
        "title": "Python PyTorch Code Generator",
        "description": "Text generator - Pytorch neural network code generation example",
        "generate_params": {
            "text": """# train a neural network in pytorch - efficient net for image classification
import pytorch_lightning
import torch
import numpy as np
import cv2
""",
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
    },
    "cpp-code-generation": {
        "title": "C plus plus Code Generator",
        "description": "Text generator - C++ code generation examples",
        "generate_params": {
            "text": """#include <iostream>
using namespace std;

int main() {
  cout <<""",
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
    },
    "jquery-code-generation": {
        "title": "JQuery Code Generator",
        "description": "Text generator - JQuery code generation examples",
        "generate_params": {
            "text": """$(document).ready(function(){
  $("p").click""",
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
    },
    "c-code-generation": {
        "title": "C Code Generator",
        "description": "Text generator - C code generation examples",
        "generate_params": {
            "text": """#include <stdio.h>

int main() {
  printf(""",
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
    },
    "sql-code-generation": {
        "title": "SQL Code Generator",
        "description": "Text generator - SQL code generation examples",
        "generate_params": {
            "text": """-- Select the least selling product from the products table 
-- query.sql
SELECT MIN""",
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
    },
    "bootstrap-css-code-generation": {
        "title": "Bootstrap Code Generator",
        "description": "Text generator - Bootstrap code generation examples",
        "generate_params": {
            "text": """<!-- bootstrap css code to render todo sample app -->
<h1>Example heading <span class="badge bg-""",
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
    },
    "css-code-generation": {
        "title": "CSS Code Generator",
        "description": "Text generator - CSS code generation examples",
        "generate_params": {
            "text": """h1 {
  color: white;
  text-align: """,
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
    },
    "text-generation-from-images": {
        "title": "Text generation from image content examples",
        "description": "Text generator - text generation from images examples",
        "generate_params": {
            "text": """feeling https://static.text-generator.io/static/img/h.png because""",
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
    },
    "text-generation-from-emoji-conversations": {
        "title": "Text generation from emoji and conversations examples",
        "description": "Text generator - text generation from emoji images examples - text generator analyses links",
        "generate_params": {
            "text": """feeling https://static.text-generator.io/static/img/s.png because""",
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
    },
    "html-alt-title-attribute-generator-for-images": {
        "title": "HTML alt attribute generator for images SEO",
        "description": "Text generator - HTML attribute code generation examples",
        "generate_params": {
            "text": """<img src=\"https://static.text-generator.io/static/img/fairy3.jpeg\" alt=\"""",
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
    },
    "multiple-images-question-answering": {
        "title": "Generate Text about multiple images",
        "description": "Text generator - Generate Text and answer questions about multiple images",
        "generate_params": {
            "text": """Which fairy do you think is most feminine?\n1: https://static.text-generator.io/static/img/fairy1.jpeg\n2: https://static.text-generator.io/static/img/fairy2.jpeg\n3: https://static.text-generator.io/static/img/fairy3.jpeg\nA:""",
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
    },
    "upsell-content-generator": {
        "title": "Generate Text for Sales",
        "description": "Text generator - UpSelling Text Generator Examples",
        "generate_params": {
            "text": """Accelerate your startup’s growth with NVIDIA Inception  

Thousands of startups around the world use NVIDIA technologies to accelerate their growth and reimagine advanced solutions in AI, deep learning, data science, HPC, networking, graphics, AR/VR, and gaming. NVIDIA Inception is designed to help startups build their products and grow faster. Members get engineering guidance""",
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
    },
    "technical-content-generator": {
        "title": "Generate Text for Technical Content",
        "description": "Text generator - Technical Content Text Generator - UPS product description",
        "generate_params": {
            "text": """For a natural disaster scenario where power supply may be interrupted for days or weeks, a generator is usually the only option to""",
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
    },
    "game-character-chatbot": {
        "title": "Generate Text for in game chatbots",
        "description": "Text generator - Game Chat Text Generator",
        "generate_params": {
            "text": """Miad: I've been followed by the orcs for weeks, they wont stop, i managed to""",
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
    },
}
from scripts.openai_examples import openai_examples_map


def make_request(use_case, retries=0):
    use_case["generate_params"].pop("frequencyPenalty", None)
    use_case["generate_params"].pop("repetitionPenalty", None)

    request = requests.post(
        # "http://0.0.0.0:8000/api/v1/generate",
        "https://api.text-generator.io/api/v1/generate",
        data=json.dumps(use_case["generate_params"]),
        headers={"Content-Type": "application/json", "secret": os.getenv("TEXTGENERATOR_API_KEY")},
    )
    if request.status_code == 200:
        return request.json()
    elif retries < 3:
        logger.error(f"Request failed with status code {request.status_code}, retrying...")
        logger.info(f"Request params: {json.dumps(use_case['generate_params'])}")
        logger.info(f"Request response: {request.text}")
        return make_request(use_case, retries + 1)
    else:
        logger.error("Request failed")


for use_case_name, use_case in use_cases.items():
    results = make_request(use_case)

    use_cases[use_case_name]["results"] = results
    logger.info(f"Use case {use_case_name} generated")
    logger.info(use_cases)
# Write use cases to fixtures file
with open("questions/usecase_fixtures.py", "w") as f:
    f.write(f"use_cases = {repr(use_cases)}")
    logger.info("Use cases written to questions/usecase_fixtures.py")
# openai use cases
# for use_case_name, use_case in openai_examples_map.items():
#     results = make_request(use_case)
#
#     openai_examples_map[use_case_name]["results"] = results
#     logger.info(f"Use case {use_case_name} generated")
#     logger.info(openai_examples_map)
