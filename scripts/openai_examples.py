openai_examples = [{
    "id": "default-qa", "title": "Q&A", "tags": ["Answers", "Generation", "Conversation"],

    "generate_params": {
        "text": 'I am a highly intelligent question answering bot. If you ask me a question that is rooted in truth, I will give you the answer. If you ask me a question that is nonsense, trickery, or has no clear answer, I will respond with "Unknown".\n\nQ: What is human life expectancy in the United States?\nA: Human life expectancy in the United States is 78 years.\n\nQ: Who was president of the United States in 1955?\nA: Dwight D. Eisenhower was president of the United States in 1955.\n\nQ: Which party did he belong to?\nA: He belonged to the Republican Party.\n\nQ: What is the square root of banana?\nA: Unknown\n\nQ: How does a telescope work?\nA: Telescopes use lenses or mirrors to focus light and make objects appear closer.\n\nQ: Where were the 1992 Olympics held?\nA: The 1992 Olympics were held in Barcelona, Spain.\n\nQ: How many squigs are in a bonk?\nA: Unknown\n\nQ: Where is the Valley of Kings?\nA:',
        "max_length": 100,
        "number_of_results": 4,
        "temperature": 1,
        "top_p": 1,
        "stop_sequences": ["\n"]
    }, "description": "Answer questions based on existing knowledge.", "icon": "QuestionMarkCircle"
}, {
    "id": "default-grammar", "title": "Grammar correction", "tags": ["Transformation", "Generation"],

    "generate_params": {
        "text": "Correct this to standard English:\n\nShe no went to the market.", "max_length": 60,
        "number_of_results": 4,
        "temperature": 1
    }, "description": "Corrects sentences into standard English.", "icon": "AcademicCap"
}, {
    "id": "default-summarize", "title": "Summarize for a 2nd grader", "tags": ["Transformation", "Generation"],

    "generate_params": {
        "text": "Summarize this for a second-grade student:\n\nJupiter is the fifth planet from the Sun and the largest in the Solar System. It is a gas giant with a mass one-thousandth that of the Sun, but two-and-a-half times that of all the other planets in the Solar System combined. Jupiter is one of the brightest objects visible to the naked eye in the night sky, and has been known to ancient civilizations since before recorded history. It is named after the Roman god Jupiter.[19] When viewed from Earth, Jupiter can be bright enough for its reflected light to cast visible shadows,[20] and is on average the third-brightest natural object in the night sky after the Moon and Venus.",
        "number_of_results": 4,
        "temperature": 0,
    }, "description": "Translates difficult text into simpler concepts.", "icon": "FastForward"
}, {
    "id": "default-openai-api", "title": "Natural language to OpenAI API", "tags": ["Code", "Transformation"],

    "generate_params": {
        "text": '"""\nUtil exposes the following:\nutil.openai() -> authenticates & returns the openai module, which has the following functions:\nopenai.Completion.create(\n    prompt="<my prompt>", # The prompt to start completing from\n    max_tokens=123, # The max number of tokens to generate\n    temperature=1.0 # A measure of randomness\n    echo=True, # Whether to return the prompt in addition to the generated completion\n)\n"""\nimport util\n"""\nCreate an OpenAI completion starting from the prompt "Once upon an AI", no more than 5 tokens. Does not include the prompt.\n"""\n',
        "max_length": 64,
        "number_of_results": 4,
        "temperature": 1,
        "stop_sequences": ['"""']
    }, "description": "Create code to call to the OpenAI API using a natural language instruction.",
    "icon": "Annotation"
}, {
    "id": "default-text-to-command", "title": "Text to command", "tags": ["Transformation", "Generation"],

    "generate_params": {
        "text": "Convert this text to a programmatic command:\n\nExample: Ask Constance if we need some bread\nOutput: send-msg `find constance` Do we need some bread?\n\nContact the ski store and figure out if I can get my skis fixed before I leave on Thursday",
        "max_length": 100,
        "number_of_results": 4,
        "temperature": 1,
        "frequencyPenalty": .2,
        "stop_sequences": ["\n"]
    }, "description": "Translate text into programmatic commands.", "icon": "Terminal"
}, {
    "id": "default-translate", "title": "English to other languages", "tags": ["Transformation", "Generation"],

    "generate_params": {
        "text": "Translate this into 1. French, 2. Spanish and 3. Japanese:\n\nWhat rooms do you have available?\n\n1.",
        "max_length": 100,
        "number_of_results": 4,
        "temperature": .3
    }, "description": "Translates English text into French, Spanish and Japanese.", "icon": "GlobeAlt"
}, {
    "id": "default-stripe-api", "title": "Natural language to Stripe API", "tags": ["Code", "Transformation"],

    "generate_params": {
        "text": '"""\nUtil exposes the following:\n\nutil.stripe() -> authenticates & returns the stripe module; usable as stripe.Charge.create etc\n"""\nimport util\n"""\nCreate a Stripe token using the users credit card: 5555-4444-3333-2222, expiration date 12 / 28, cvc 521\n"""',
        "max_length": 100,
        "number_of_results": 4,
        "temperature": 1,
        "stop_sequences": ['"""']
    }, "description": "Create code to call the Stripe API using natural language.", "icon": "CurrencyDollar"
}, {
    "id": "default-sql-translate", "title": "SQL translate", "tags": ["Code", "Transformation"],

    "generate_params": {
        "text": "### Postgres SQL tables, with their properties:\n#\n# Employee(id, name, department_id)\n# Department(id, name, address)\n# Salary_Payments(id, employee_id, amount, date)\n#\n### A query to list the names of the departments which employed more than 10 employees in the last 3 months\nSELECT",
        "max_length": 150,
        "number_of_results": 4,
        "temperature": 1,
        "stop_sequences": ["#", ";"]
    }, "description": "Translate natural language to SQL queries.", "icon": "QuestionMarkCircle"
}, {
    "id": "default-parse-data",
    "title": "Parse unstructured data",
    "tags": ["Transformation", "Generation"],

    "generate_params": {
        "text": "A table summarizing the fruits from Goocrux:\n\nThere are many fruits that were found on the recently discovered planet Goocrux. There are neoskizzles that grow there, which are purple and taste like candy. There are also loheckles, which are a grayish blue fruit and are very tart, a little bit like a lemon. Pounits are a bright green color and are more savory than sweet. There are also plenty of loopnovas which are a neon pink flavor and taste like cotton candy. Finally, there are fruits called glowls, which have a very sour and bitter taste which is acidic and caustic, and a pale orange tinge to them.\n\n| Fruit | Color | Flavor |",
        "max_length": 100,
        "number_of_results": 4,
        "temperature": 1
    },
    "tagline": "Create tables from long form text",
    "description": "Create tables from long form text by specifying a structure and supplying some examples.",
    "icon": "Table"
}, {
    "id": "default-classification", "title": "Classification", "tags": ["Classification"],

    "generate_params": {
        "text": "The following is a list of companies and the categories they fall into:\n\nApple, Facebook, Fedex\n\nApple\nCategory:",
        "number_of_results": 4,
        "temperature": 1
    }, "description": "Classify items into categories via example.", "icon": "Tag"
}, {
    "id": "default-python-to-natural-language", "title": "Python to natural language", "tags": ["Code", "Translation"],

    "generate_params": {
        "text": '# Python 3 \ndef remove_common_prefix(x, prefix, ws_prefix): \n    x["completion"] = x["completion"].str[len(prefix) :] \n    if ws_prefix: \n        # keep the single whitespace as prefix \n        x["completion"] = " " + x["completion"] \nreturn x \n\n# Explanation of what the code does\n\n#',
        "max_length": 64,
        "number_of_results": 4,
        "temperature": 1,
        "stop_sequences": []
    }, "description": "Explain a piece of Python code in human understandable language.", "icon": "Hashtag"
}, {
    "id": "default-movie-to-emoji", "title": "Movie to Emoji", "tags": ["Transformation", "Generation"],

    "generate_params": {
        "text": "Convert movie titles into emoji.\n\nBack to the Future: \ud83d\udc68\ud83d\udc74\ud83d\ude97\ud83d\udd52 \nBatman: \ud83e\udd35\ud83e\udd87 \nTransformers: \ud83d\ude97\ud83e\udd16 \nStar Wars:",
        "max_length": 60,
        "number_of_results": 4,
        "temperature": .8,
        "stop_sequences": ["\n"]
    }, "description": "Convert movie titles into emoji.", "icon": "EmojiHappy"
}, {
    "id": "default-time-complexity", "title": "Calculate Time Complexity", "tags": ["Code", "Transformation"],

    "generate_params": {
        "text": 'def foo(n, k):\naccum = 0\nfor i in range(n):\n    for l in range(k):\n        accum += i\nreturn accum\n"""\nThe time complexity of this function is',
        "max_length": 64,
        "number_of_results": 4,
        "temperature": 1,
        "stop_sequences": ["\n"]
    }, "description": "Find the time complexity of a function.", "icon": "IoTimeSharp"
}, {
    "id": "default-translate-code",
    "title": "Translate programming languages",
    "tags": ["Code", "Translation"],

    "generate_params": {
        "text": "##### Translate this function  from Python into Haskell\n### Python\n    \n    def predict_proba(X: Iterable[str]):\n        return np.array([predict_one_probas(tweet) for tweet in X])\n    \n### Haskell",
        "max_length": 54,
        "number_of_results": 4,
        "temperature": 1,
        "stop_sequences": ["###"]
    },
    "tagline": "Translate from one programming language to another",
    "description": "To translate from one programming language to another we can use the comments to specify the source and target languages.",
    "icon": "Translate"
}, {
    "id": "default-adv-tweet-classifier",
    "title": "Advanced tweet classifier",
    "tags": ["Classification"],

    "generate_params": {
        "text": 'Classify the sentiment in these tweets:\n\n1. "I can\'t stand homework"\n2. "This sucks. I\'m bored "\n3. "I can\'t wait for Halloween!!!"\n4. "My cat is adorable "\n5. "I hate chocolate"\n\nTweet sentiment ratings:',
        "max_length": 60,
        "number_of_results": 4,
        "temperature": 1
    },
    "tagline": "Advanced sentiment detection for a piece of text.",
    "description": "This is an advanced prompt for detecting sentiment. It allows you to provide it with a list of status updates and then provide a sentiment for each one.",
    "icon": "Hashtag"
}, {
    "id": "default-explain-code", "title": "Explain code", "tags": ["Code", "Translation"],

    "generate_params": {
        "text": 'class Log:\n    def __init__(self, path):\n        dirname = os.path.dirname(path)\n        os.makedirs(dirname, exist_ok=True)\n        f = open(path, "a+")\n\n        # Check that the file is newline-terminated\n        size = os.path.getsize(path)\n        if size > 0:\n            f.seek(size - 1)\n            end = f.read(1)\n            if end != "\\n":\n                f.write("\\n")\n        self.f = f\n        self.path = path\n\n    def log(self, event):\n        event["_event_id"] = str(uuid.uuid4())\n        json.dump(event, self.f)\n        self.f.write("\\n")\n\n    def state(self):\n        state = {"complete": set(), "last": None}\n        for line in open(self.path):\n            event = json.loads(line)\n            if event["type"] == "submit" and event["success"]:\n                state["complete"].add(event["id"])\n                state["last"] = event\n        return state\n\n"""\nHere\'s what the above class is doing:\n1.',
        "max_length": 64,
        "number_of_results": 4,
        "temperature": 1,
        "stop_sequences": ['"""']
    }, "description": "Explain a complicated piece of code.", "icon": "Hashtag"
}, {
    "id": "default-keywords",
    "title": "Keywords",
    "tags": ["Classification", "Transformation"],

    "generate_params": {
        "text": "Extract keywords from this text:\n\nBlack-on-black ware is a 20th- and 21st-century pottery tradition developed by the Puebloan Native American ceramic artists in Northern New Mexico. Traditional reduction-fired blackware has been made for centuries by pueblo artists. Black-on-black ware of the past century is produced with a smooth surface, with the designs applied through selective burnishing or the application of refractory slip. Another style involves carving or incising designs and selectively polishing the raised areas. For generations several families from Kha'po Owingeh and P'ohwh\xf3ge Owingeh pueblos have been making black-on-black ware with the techniques passed down from matriarch potters. Artists from other pueblos have also produced black-on-black ware. Several contemporary artists have created works honoring the pottery of their ancestors.",
        "max_length": 60,
        "number_of_results": 4,
        "temperature": .3,
        "frequencyPenalty": .8
    },
    "tagline": "Extract keywords from a block of text.",
    "description": "Extract keywords from a block of text. At a lower temperature it picks keywords from the text. At a higher temperature it will generate related keywords which can be helpful for creating search indexes.",
    "icon": "Key"
}, {
    "id": "default-factual-answering",
    "title": "Factual answering",
    "tags": ["Answers", "Generation", "Conversation", "Classification"],

    "generate_params": {
        "text": "Q: Who is Batman?\nA: Batman is a fictional comic book character.\n\nQ: What is torsalplexity?\nA: ?\n\nQ: What is Devz9?\nA: ?\n\nQ: Who is George Lucas?\nA: George Lucas is American film director and producer famous for creating Star Wars.\n\nQ: What is the capital of California?\nA: Sacramento.\n\nQ: What orbits the Earth?\nA: The Moon.\n\nQ: Who is Fred Rickerson?\nA: ?\n\nQ: What is an atom?\nA: An atom is a tiny particle that makes up everything.\n\nQ: Who is Alvan Muntz?\nA: ?\n\nQ: What is Kozar-09?\nA: ?\n\nQ: How many moons does Mars have?\nA: Two, Phobos and Deimos.\n\nQ: What's a language model?\nA:",
        "max_length": 60,
        "number_of_results": 4,
        "temperature": 1
    },
    "icon": "QuestionMarkCircle"
}, {
    "id": "default-ad-product-description", "title": "Ad from product description", "tags": ["Generation"],

    "generate_params": {
        "text": "Write a creative ad for the following product to run on Facebook aimed at parents:\n\nProduct: Learning Room is a virtual environment to help students from kindergarten to high school excel in school.",
        "max_length": 60,
        "number_of_results": 4,
        "temperature": .5
    }, "description": "Turn a product description into ad copy.", "icon": "Speakerphone"
}, {
    "id": "default-product-name-gen", "title": "Product name generator", "tags": ["Generation"],

    "generate_params": {
        "text": "Product description: A home milkshake maker\nSeed words: fast, healthy, compact.\nProduct names: HomeShaker, Fit Shaker, QuickShake, Shake Maker\n\nProduct description: A pair of shoes that can fit any foot size.\nSeed words: adaptable, fit, omni-fit.",
        "max_length": 60,
        "number_of_results": 4,
        "temperature": .8
    }, "description": "Create product names from examples words. Influenced by a community prompt.", "icon": "LightBulb"

}, {
    "id": "default-tldr-summary",
    "title": "TL;DR summarization",
    "tags": ["Transformation", "Generation"],

    "generate_params": {
        "text": "A neutron star is the collapsed core of a massive supergiant star, which had a total mass of between 10 and 25 solar masses, possibly more if the star was especially metal-rich.[1] Neutron stars are the smallest and densest stellar objects, excluding black holes and hypothetical white holes, quark stars, and strange stars.[2] Neutron stars have a radius on the order of 10 kilometres (6.2 mi) and a mass of about 1.4 solar masses.[3] They result from the supernova explosion of a massive star, combined with gravitational collapse, that compresses the core past white dwarf star density to that of atomic nuclei.\n\nTl;dr",
        "max_length": 60,
        "number_of_results": 4,
        "temperature": 0,
    },
    "description": "Summarize text by adding a 'tl;dr:' to the end of a text passage. It shows that the API understands how to perform a number of tasks with no instructions.",
    "icon": "Filter"
}, {
    "id": "default-fix-python-bugs",
    "title": "Python bug fixer",
    "tags": ["Code", "Generation"],

    "generate_params": {
        "text": '##### Fix bugs in the below function\n \n### Buggy Python\nimport Random\na = random.randint(1,12)\nb = random.randint(1,12)\nfor i in range(10):\n    question = "What is "+a+" x "+b+"? "\n    answer = input(question)\n    if answer = a*b\n        print (Well done!)\n    else:\n        print("No.")\n    \n### Fixed Python',
        "max_length": 182,
        "number_of_results": 4,
        "temperature": 1,
        "stop_sequences": ["###"]
    },
    "tagline": "Find and fix bugs in source code.",
    "description": "There's a number of ways of structuring the prompt for checking for bugs. Here we add a comment suggesting that source code is buggy, and then ask codex to generate a fixed code.",
    "icon": "IoBug"

}, {
    "id": "default-spreadsheet-gen",
    "title": "Spreadsheet creator",
    "tags": ["Generation"],

    "generate_params": {
        "text": "A two-column spreadsheet of top science fiction movies and the year of release:\n\nTitle|  Year of release",
        "max_length": 60,
        "number_of_results": 4,
        "temperature": .5
    },
    "description": "Create spreadsheets of various kinds of data. It's a long prompt but very versatile. Output can be copy+pasted into a text file and saved as a .csv with pipe separators.",
    "icon": "Table"
}, {
    "id": "default-js-helper",
    "title": "JavaScript helper chatbot",
    "tags": ["Code", "Answers", "Conversation"],

    "generate_params": {
        "text": "You: How do I combine arrays?\nJavaScript chatbot: You can use the concat() method.\nYou: How do you make an alert appear after 10 seconds?\nJavaScript chatbot",
        "max_length": 60,
        "number_of_results": 4,
        "temperature": 1,
        "frequencyPenalty": .5,
        "stop_sequences": ["You:"]
    },
    "tagline": "Message-style bot that answers JavaScript questions",
    "description": "This is a message-style chatbot that can answer questions about using JavaScript. It uses a few examples to get the conversation started.",
    "icon": "QuestionMarkCircle"
}, {
    "id": "default-ml-ai-tutor",
    "title": "ML/AI language model tutor",
    "tags": ["Answers", "Generation", "Conversation"],

    "generate_params": {
        "text": "ML Tutor: I am a ML/AI language model tutor\nYou: What is a language model?\nML Tutor: A language model is a statistical model that describes the probability of a word given the previous words.\nYou: What is a statistical model?",
        "max_length": 60,
        "number_of_results": 4,
        "temperature": .3,
        "frequencyPenalty": .5,
        "stop_sequences": ["You:"]
    },
    "tagline": "Bot that answers questions about language models",
    "description": "This is a QA-style chatbot that answers questions about language models.",
    "icon": "QuestionMarkCircle"
}, {
    "id": "default-sci-fi-book-list",
    "title": "Science fiction book list maker",
    "tags": ["Generation"],

    "generate_params": {
        "text": "List 10 science fiction books:",
        "max_length": 200,
        "number_of_results": 4,
        "temperature": .5,
        "presencePenalty": .5,
        "frequencyPenalty": .52,
        "stop_sequences": ["11."]
    },
    "tagline": "Create a list of items for a given topic.",
    "description": "This makes a list of science fiction books and stops when it reaches #10.",
    "icon": "BookOpen"
}, {
    "id": "default-tweet-classifier",
    "title": "Tweet classifier",
    "tags": ["Classification"],

    "generate_params": {
        "text": 'Decide whether a Tweet\'s sentiment is positive, neutral, or negative.\n\nTweet: "I loved the new Batman movie!"\nSentiment:',
        "max_length": 60,
        "number_of_results": 4,
        "temperature": 1,
        "frequencyPenalty": .5
    },
    "tagline": "Basic sentiment detection for a piece of text.",
    "description": "This is a basic prompt for detecting sentiment.",
    "icon": "Hashtag"
}, {
    "id": "default-airport-codes",
    "title": "Airport code extractor",
    "tags": ["Transformation", "Generation"],

    "generate_params": {
        "text": 'Extract the airport codes from this text:\n\nText: "I want to fly from Los Angeles to Miami."\nAirport codes: LAX, MIA\n\nText: "I want to fly from Orlando to Boston"\nAirport codes:',
        "max_length": 60,
        "number_of_results": 4,
        "temperature": 1,
        "stop_sequences": ["\n"]
    },
    "tagline": "Extract airport codes from text.",
    "description": "A simple prompt for extracting airport codes from text.",
    "icon": "Tag"
}, {
    "id": "default-sql-request", "title": "SQL request", "tags": ["Transformation", "Generation", "Translation"],

    "generate_params": {
        "text": "Create a SQL request to find all users who live in California and have over 1000 credits:",
        "max_length": 60,
        "number_of_results": 4,
        "temperature": .3
    }, "description": "Create simple SQL queries.", "icon": "Terminal"
}, {
    "id": "default-extract-contact-info", "title": "Extract contact information",
    "tags": ["Transformation", "Generation"],

    "generate_params": {
        "text": "Extract the name and mailing address from this email:\n\nDear Kelly,\n\nIt was great to talk to you at the seminar. I thought Jane's talk was quite good.\n\nThank you for the book. Here's my address 2111 Ash Lane, Crestview CA 92002\n\nBest,\n\nMaya\n\nName:",
        "number_of_results": 4,
        "temperature": 1
    }, "description": "Extract contact information from a block of text.", "icon": "Mail"
}, {
    "id": "default-js-to-py", "title": "JavaScript to Python", "tags": ["Code", "Transformation", "Translation"],

    "generate_params": {
        "text": '#JavaScript to Python:\nJavaScript: \ndogs = ["bill", "joe", "carl"]\ncar = []\ndogs.forEach((dog) {\n    car.push(dog);\n});\n\nPython:',
        "number_of_results": 4,
        "temperature": 1
    }, "description": "Convert simple JavaScript expressions into Python.", "icon": "Terminal"
}, {
    "id": "default-friend-chat", "title": "Friend chat", "tags": ["Conversation", "Generation"],

    "generate_params": {
        "text": "You: What have you been up to?\nFriend: Watching old movies.\nYou: Did you watch anything interesting?\nFriend:",
        "max_length": 60,
        "number_of_results": 4,
        "temperature": .5,
        "frequencyPenalty": .5,
        "stop_sequences": ["You:"]
    }, "description": "Emulate a text message conversation.", "icon": "ChatAlt"
}, {
    "id": "default-mood-color", "title": "Mood to color", "tags": ["Transformation", "Generation"],

    "generate_params": {
        "text": "The CSS code for a color like a blue sky at dusk:\n\nbackground-color: #",
        "number_of_results": 4,
        "temperature": 1,
        "stop_sequences": [";"]
    }, "description": "Turn a text description into a color.", "icon": "EmojiHappy"
}, {
    "id": "default-python-docstring",
    "title": "Write a Python docstring",
    "tags": ["Code", "Generation"],

    "generate_params": {
        "text": "# Python 3.7\n \ndef randomly_split_dataset(folder, filename, split_ratio=[0.8, 0.2]):\n    df = pd.read_json(folder + filename, lines=True)\n    train_name, test_name = \"train.jsonl\", \"test.jsonl\"\n    df_train, df_test = train_test_split(df, test_size=split_ratio[1], random_state=42)\n    df_train.to_json(folder + train_name, orient='records', lines=True)\n    df_test.to_json(folder + test_name, orient='records', lines=True)\nrandomly_split_dataset('finetune_data/', 'dataset.jsonl')\n    \n# An elaborate, high quality docstring for the above function:\n\"\"\"",
        "max_length": 150,
        "number_of_results": 4,
        "temperature": 1,
        "stop_sequences": ["#", '"""']
    },
    "description": 'An example of how to create a docstring for a given Python function. We specify the Python version, paste in the code, and then ask within a comment for a docstring, and give a characteristic beginning of a docstring (""").',
    "icon": "Code"
}, {
    "id": "default-analogy-maker", "title": "Analogy maker", "tags": ["Generation"],

    "generate_params": {
        "text": "Create an analogy for this phrase:\n\nQuestions are arrows in that:", "max_length": 60,
        "number_of_results": 4,
        "temperature": .5
    }, "description": "Create analogies. Modified from a community prompt to require fewer examples.",
    "icon": "LightBulb"
}, {
    "id": "default-js-one-line", "title": "JavaScript one line function",
    "tags": ["Code", "Transformation", "Translation"],

    "generate_params": {
        "text": "Use list comprehension to convert this into one line of JavaScript:\n\ndogs.forEach((dog) => {\n    car.push(dog);\n});\n\nJavaScript one line version:",
        "max_length": 60,
        "number_of_results": 4,
        "temperature": 1,
        "stop_sequences": [";"]
    }, "description": "Turn a JavaScript function into a one liner.", "icon": "Terminal"
}, {
    "id": "default-micro-horror",
    "title": "Micro horror story creator",
    "tags": ["Transformation", "Generation", "Translation"],

    "generate_params": {
        "text": "Topic: Breakfast\nTwo-Sentence Horror Story: He always stops crying when I pour the milk on his cereal. I just have to remember not to let him see his face on the carton.\n    \nTopic: Wind\nTwo-Sentence Horror Story:",
        "max_length": 60,
        "number_of_results": 4,
        "temperature": .8,
        "frequencyPenalty": .5
    },
    "description": "Creates two to three sentence short horror stories from a topic input.",
    "icon": "PencilAlt"
}, {
    "id": "default-third-person",
    "title": "Third-person converter",
    "tags": ["Transformation", "Generation", "Translation"],

    "generate_params": {
        "text": "Convert this from first-person to third person (gender female):\n\nI decided to make a movie about Ada Lovelace.",
        "max_length": 60,
        "number_of_results": 4,
        "temperature": 1
    },
    "description": "Converts first-person POV to the third-person. This is modified from a community prompt to use fewer examples.",
    "icon": "PencilAlt"
}, {
    "id": "default-notes-summary", "title": "Notes to summary", "tags": ["Transformation", "Generation"],

    "generate_params": {
        "text": "Convert my short hand into a first-hand account of the meeting:\n\nTom: Profits up 50%\nJane: New servers are online\nKjel: Need more time to fix software\nJane: Happy to help\nParkman: Beta testing almost done",
        "number_of_results": 4,
        "temperature": 1
    }, "description": "Turn meeting notes into a summary.", "icon": "PencilAlt"
}, {
    "id": "default-vr-fitness", "title": "VR fitness idea generator", "tags": ["Generation"],

    "generate_params": {
        "text": "Brainstorm some ideas combining VR and fitness:",
        "max_length": 150,
        "number_of_results": 4,
        "temperature": .6,
        "frequencyPenalty": 1,
        "presencePenalty": 1
    }, "description": "Create ideas for fitness and virtual reality games.", "icon": "LightBulb"
}, {
    "id": "default-esrb-rating", "title": "ESRB rating", "tags": ["Classification"],

    "generate_params": {
        "text": 'Provide an ESRB rating for the following text:\n\n"i\'m going to blow your brains out with my ray gun then stomp on your guts."\n\nESRB rating:',
        "max_length": 60,
        "number_of_results": 4,
        "temperature": .3,
        "stop_sequences": ["\n"]
    }, "description": "Categorize text based upon ESRB ratings.", "icon": "Tag"
}, {
    "id": "default-essay-outline", "title": "Essay outline", "tags": ["Generation"],

    "generate_params": {
        "text": "Create an outline for an essay about Nikola Tesla and his contributions to technology:",
        "number_of_results": 4,
        "temperature": 1,
        "max_length": 150
    }, "description": "Generate an outline for a research topic.", "icon": "DocumentText"
}, {
    "id": "default-recipe-generator", "title": "Recipe creator (eat at your own risk)", "tags": ["Generation"],

    "generate_params": {
        "text": "Write a recipe based on these ingredients and instructions:\n\nFrito Pie\n\nIngredients:\nFritos\nChili\nShredded cheddar cheese\nSweet white or red onions, diced small\nSour cream\n\nInstructions:",
        "max_length": 120,
        "number_of_results": 4,
        "temperature": .3
    }, "description": "Create a recipe from a list of ingredients.", "icon": "Cake"
}, {
    "id": "default-chat", "title": "Chat", "tags": ["Conversation", "Generation"],

    "generate_params": {
        "text": "The following is a conversation with an AI assistant. The assistant is helpful, creative, clever, and very friendly.\n\nHuman: Hello, who are you?\nAI: I am an AI created by OpenAI. How can I help you today?\nHuman: I'd like to cancel my subscription.\nAI:",
        "max_length": 150,
        "presencePenalty": .6,
        "number_of_results": 4,
        "temperature": .9,
        "top_p": 1,
        "stop_sequences": [" Human:", " AI:"]
    }, "description": "Open ended conversation with an AI assistant.", "icon": "ChatAlt"
}, {
    "id": "default-marv-sarcastic-chat", "title": "Marv the sarcastic chat bot", "tags": ["Conversation", "Generation"],

    "generate_params": {
        "text": "Marv is a chatbot that reluctantly answers questions with sarcastic responses:\n\nYou: How many pounds are in a kilogram?\nMarv: This again? There are 2.2 pounds in a kilogram. Please make a note of this.\nYou: What does HTML stand for?\nMarv: Was Google too busy? Hypertext Markup Language. The T is for try to ask better questions in the future.\nYou: When did the first airplane fly?\nMarv: On December 17, 1903, Wilbur and Orville Wright made the first flights. I wish they\u2019d come and take me away.\nYou: What is the meaning of life?\nMarv: I\u2019m not sure. I\u2019ll ask my friend Google.\nYou: What time is it?\nMarv:",
        "max_length": 60,
        "number_of_results": 4,
        "temperature": .5,
        "top_p": .3,
        "frequencyPenalty": .5
    }, "description": "Marv is a factual chatbot that is also sarcastic.", "icon": "EmojiSad"
}, {
    "id": "default-turn-by-turn-directions", "title": "Turn by turn directions",
    "tags": ["Transformation", "Generation"],

    "generate_params": {
        "text": "Create a numbered list of turn-by-turn directions from this text: \n\nGo south on 95 until you hit Sunrise boulevard then take it east to us 1 and head south. Tom Jenkins bbq will be on the left after several miles.",
        "number_of_results": 4,
        "temperature": .3
    }, "description": "Convert natural language to turn-by-turn directions.", "icon": "LocationMarker"
}, {
    "id": "default-restaurant-review", "title": "Restaurant review creator", "tags": ["Generation"],

    "generate_params": {
        "text": "Write a restaurant review based on these notes:\n\nName: The Blue Wharf\nLobster great, noisy, service polite, prices good.\n\nReview:",
        "number_of_results": 4,
        "temperature": .5
    }, "description": "Turn a few words into a restaurant review.", "icon": "Newspaper"
}, {
    "id": "default-study-notes", "title": "Create study notes", "tags": ["Generation"],

    "generate_params": {
        "text": "What are 5 key points I should know when studying Ancient Rome?", "number_of_results": 4,
        "temperature": .3, "max_length": 150
    }, "description": "Provide a topic and get study notes.", "icon": "Collection"
}, {
    "id": "default-interview-questions", "title": "Interview questions", "tags": ["Generation"],

    "generate_params": {
        "text": "Create a list of 8 questions for my interview with a science fiction author:",
        "max_length": 150,
        "number_of_results": 4,
        "temperature": .5
    }, "description": "Create interview questions.", "icon": "Briefcase"
}]

openai_examples_map = {example["id"]: example for example in openai_examples}
