[
  {
    id: "default-qa",
    title: "Q&A",
    tags: [
      "Answers",
      "Generation",
      "Conversation"
    ],
    prompt: 'I am a highly intelligent question answering bot. If you ask me a question that is rooted in truth, I will give you the answer. If you ask me a question that is nonsense, trickery, or has no clear answer, I will respond with "Unknown".\n\nQ: What is human life expectancy in the United States?\nA: Human life expectancy in the United States is 78 years.\n\nQ: Who was president of the United States in 1955?\nA: Dwight D. Eisenhower was president of the United States in 1955.\n\nQ: Which party did he belong to?\nA: He belonged to the Republican Party.\n\nQ: What is the square root of banana?\nA: Unknown\n\nQ: How does a telescope work?\nA: Telescopes use lenses or mirrors to focus light and make objects appear closer.\n\nQ: Where were the 1992 Olympics held?\nA: The 1992 Olympics were held in Barcelona, Spain.\n\nQ: How many squigs are in a bonk?\nA: Unknown\n\nQ: Where is the Valley of Kings?\nA:',
    response: "The Valley of Kings is located in Luxor, Egypt.",
    parameters: {
      engine: "text-davinci-002",
      responseLength: 100,
      temperature: 0,
      topP: 1,
      stopSequence: [
        "\n"
      ]
    },
    description: "Answer questions based on existing knowledge.",
    icon: "HiQuestionMarkCircle"
  },
  {
    id: "default-grammar",
    title: "Grammar correction",
    tags: [
      "Transformation",
      "Generation"
    ],
    prompt: "Correct this to standard English:\n\nShe no went to the market.",
    response: "She didn't go to the market.",
    parameters: {
      engine: "text-davinci-002",
      responseLength: 60,
      temperature: 0
    },
    description: "Corrects sentences into standard English.",
    icon: "HiAcademicCap"
  },
  {
    id: "default-summarize",
    title: "Summarize for a 2nd grader",
    tags: [
      "Transformation",
      "Generation"
    ],
    prompt: "Summarize this for a second-grade student:\n\nJupiter is the fifth planet from the Sun and the largest in the Solar System. It is a gas giant with a mass one-thousandth that of the Sun, but two-and-a-half times that of all the other planets in the Solar System combined. Jupiter is one of the brightest objects visible to the naked eye in the night sky, and has been known to ancient civilizations since before recorded history. It is named after the Roman god Jupiter.[19] When viewed from Earth, Jupiter can be bright enough for its reflected light to cast visible shadows,[20] and is on average the third-brightest natural object in the night sky after the Moon and Venus.",
    response: "Jupiter is a planet that is bigger than all the other planets in our solar system and is very bright when you see it in the night sky. It is named after the Roman god Jupiter. When viewed from Earth, it is usually one of the three brightest objects in the sky.",
    parameters: {
      engine: "text-davinci-002",
      temperature: o.Ar
    },
    description: "Translates difficult text into simpler concepts.",
    icon: "HiFastForward"
  },
  {
    id: "default-openai-api",
    title: "Natural language to OpenAI API",
    tags: [
      "Code",
      "Transformation"
    ],
    prompt: '"""\nUtil exposes the following:\nutil.openai() -> authenticates & returns the openai module, which has the following functions:\nopenai.Completion.create(\n    prompt="<my prompt>", # The prompt to start completing from\n    max_tokens=123, # The max number of tokens to generate\n    temperature=1.0 # A measure of randomness\n    echo=True, # Whether to return the prompt in addition to the generated completion\n)\n"""\nimport util\n"""\nCreate an OpenAI completion starting from the prompt "Once upon an AI", no more than 5 tokens. Does not include the prompt.\n"""\n',
    response: 'completion = util.openai().Completion.create(\nprompt="Once upon an AI",\nmax_tokens=5,\ntemperature=1.0,\necho=False,\n)\nprint(completion)\n"""\n',
    parameters: {
      engine: "code-davinci-002",
      responseLength: 64,
      temperature: 0,
      stopSequence: [
        '"""'
      ]
    },
    description: "Create code to call to the OpenAI API using a natural language instruction.",
    icon: "HiAnnotation"
  },
  {
    id: "default-text-to-command",
    title: "Text to command",
    tags: [
      "Transformation",
      "Generation"
    ],
    prompt: "Convert this text to a programmatic command:\n\nExample: Ask Constance if we need some bread\nOutput: send-msg `find constance` Do we need some bread?\n\nContact the ski store and figure out if I can get my skis fixed before I leave on Thursday",
    response: "send-msg `find ski-store` Can I get my skis fixed before I leave on Thursday?",
    parameters: {
      engine: "text-davinci-002",
      responseLength: 100,
      temperature: 0,
      frequencyPenalty: .2,
      stopSequence: [
        "\n"
      ]
    },
    description: "Translate text into programmatic commands.",
    icon: "HiTerminal"
  },
  {
    id: "default-translate",
    title: "English to other languages",
    tags: [
      "Transformation",
      "Generation"
    ],
    prompt: "Translate this into 1. French, 2. Spanish and 3. Japanese:\n\nWhat rooms do you have available?\n\n1.",
    response: "Quels sont les chambres disponibles?\n2. \xbfCu\xe1les son las habitaciones disponibles?\n3. \u4f55\u5ba4\u304c\u3042\u308a\u307e\u3059\u304b?",
    parameters: {
      engine: "text-davinci-002",
      responseLength: 100,
      temperature: .3
    },
    description: "Translates English text into French, Spanish and Japanese.",
    icon: "HiGlobeAlt"
  },
  {
    id: "default-stripe-api",
    title: "Natural language to Stripe API",
    tags: [
      "Code",
      "Transformation"
    ],
    prompt: '"""\nUtil exposes the following:\n\nutil.stripe() -> authenticates & returns the stripe module; usable as stripe.Charge.create etc\n"""\nimport util\n"""\nCreate a Stripe token using the users credit card: 5555-4444-3333-2222, expiration date 12 / 28, cvc 521\n"""',
    response: 'token = util.stripe().Token.create(\ncard={\n    "number": \'5555-4444-3333-2222\',\n    "exp_month": 12,\n    "exp_year": 28,\n    "cvc": \'521\'\n},\n)\n\n"""          \n',
    parameters: {
      engine: "code-davinci-002",
      responseLength: 100,
      temperature: 0,
      stopSequence: [
        '"""'
      ]
    },
    description: "Create code to call the Stripe API using natural language.",
    icon: "HiCurrencyDollar"
  },
  {
    id: "default-sql-translate",
    title: "SQL translate",
    tags: [
      "Code",
      "Transformation"
    ],
    prompt: "### Postgres SQL tables, with their properties:\n#\n# Employee(id, name, department_id)\n# Department(id, name, address)\n# Salary_Payments(id, employee_id, amount, date)\n#\n### A query to list the names of the departments which employed more than 10 employees in the last 3 months\nSELECT",
    response: " DISTINCT department.name \nFROM department \nJOIN employee ON department.id = employee.department_id \nJOIN salary_payments ON employee.id = salary_payments.employee_id \nWHERE salary_payments.date > (CURRENT_DATE - INTERVAL '3 months') \nGROUP BY department.name \nHAVING COUNT(employee.id) > 10;",
    parameters: {
      engine: "code-davinci-002",
      responseLength: 150,
      temperature: 0,
      stopSequence: [
        "#",
        ";"
      ]
    },
    description: "Translate natural language to SQL queries.",
    icon: "HiQuestionMarkCircle"
  },
  {
    id: "default-parse-data",
    title: "Parse unstructured data",
    tags: [
      "Transformation",
      "Generation"
    ],
    prompt: "A table summarizing the fruits from Goocrux:\n\nThere are many fruits that were found on the recently discovered planet Goocrux. There are neoskizzles that grow there, which are purple and taste like candy. There are also loheckles, which are a grayish blue fruit and are very tart, a little bit like a lemon. Pounits are a bright green color and are more savory than sweet. There are also plenty of loopnovas which are a neon pink flavor and taste like cotton candy. Finally, there are fruits called glowls, which have a very sour and bitter taste which is acidic and caustic, and a pale orange tinge to them.\n\n| Fruit | Color | Flavor |",
    response: "| Neoskizzle | Purple | Sweet |\n\n| Loheckle | Grayish blue | Tart |\n\n| Pounit | Bright green | Savory |\n\n| Loopnova | Neon pink | Cotton candy |\n\n| Glowl | Pale orange | Sour and bitter |",
    parameters: {
      engine: "text-davinci-002",
      responseLength: 100,
      temperature: 0
    },
    tagline: "Create tables from long form text",
    description: "Create tables from long form text by specifying a structure and supplying some examples.",
    icon: "HiTable"
  },
  {
    id: "default-classification",
    title: "Classification",
    tags: [
      "Classification"
    ],
    prompt: "The following is a list of companies and the categories they fall into:\n\nApple, Facebook, Fedex\n\nApple\nCategory:",
    response: "Technology\n\nFacebook\nCategory: Social Media\n\nFedex\nCategory: Delivery",
    parameters: {
      engine: "text-davinci-002",
      temperature: 0
    },
    description: "Classify items into categories via example.",
    icon: "HiTag"
  },
  {
    id: "default-python-to-natural-language",
    title: "Python to natural language",
    tags: [
      "Code",
      "Translation"
    ],
    prompt: '# Python 3 \ndef remove_common_prefix(x, prefix, ws_prefix): \n    x["completion"] = x["completion"].str[len(prefix) :] \n    if ws_prefix: \n        # keep the single whitespace as prefix \n        x["completion"] = " " + x["completion"] \nreturn x \n\n# Explanation of what the code does\n\n#',
    response: "The code above is a function that takes a dataframe and a prefix as input and returns a dataframe with the prefix removed from the completion column.",
    parameters: {
      engine: "code-davinci-002",
      responseLength: 64,
      temperature: 0,
      stopSequence: []
    },
    description: "Explain a piece of Python code in human understandable language.",
    icon: "HiHashtag"
  },
  {
    id: "default-movie-to-emoji",
    title: "Movie to Emoji",
    tags: [
      "Transformation",
      "Generation"
    ],
    prompt: "Convert movie titles into emoji.\n\nBack to the Future: \ud83d\udc68\ud83d\udc74\ud83d\ude97\ud83d\udd52 \nBatman: \ud83e\udd35\ud83e\udd87 \nTransformers: \ud83d\ude97\ud83e\udd16 \nStar Wars:",
    response: "\ud83d\udca5\ud83c\udf1f",
    parameters: {
      engine: "text-davinci-002",
      responseLength: 60,
      temperature: .8,
      stopSequence: [
        "\n"
      ]
    },
    description: "Convert movie titles into emoji.",
    icon: "HiEmojiHappy"
  },
  {
    id: "default-time-complexity",
    title: "Calculate Time Complexity",
    tags: [
      "Code",
      "Transformation"
    ],
    prompt: 'def foo(n, k):\naccum = 0\nfor i in range(n):\n    for l in range(k):\n        accum += i\nreturn accum\n"""\nThe time complexity of this function is',
    response: "O(n*k).",
    parameters: {
      engine: "text-davinci-002",
      responseLength: 64,
      temperature: 0,
      stopSequence: [
        "\n"
      ]
    },
    description: "Find the time complexity of a function.",
    icon: "IoTimeSharp"
  },
  {
    id: "default-translate-code",
    title: "Translate programming languages",
    tags: [
      "Code",
      "Translation"
    ],
    prompt: "##### Translate this function  from Python into Haskell\n### Python\n    \n    def predict_proba(X: Iterable[str]):\n        return np.array([predict_one_probas(tweet) for tweet in X])\n    \n### Haskell",
    response: "predict_proba :: [String] -> [Probability] \npredict_proba = map predict_one_probas",
    parameters: {
      engine: "code-davinci-002",
      responseLength: 54,
      temperature: 0,
      stopSequence: [
        "###"
      ]
    },
    tagline: "Translate from one programming language to another",
    description: "To translate from one programming language to another we can use the comments to specify the source and target languages.",
    icon: "HiTranslate"
  },
  {
    id: "default-adv-tweet-classifier",
    title: "Advanced tweet classifier",
    tags: [
      "Classification"
    ],
    prompt: 'Classify the sentiment in these tweets:\n\n1. "I can\'t stand homework"\n2. "This sucks. I\'m bored "\n3. "I can\'t wait for Halloween!!!"\n4. "My cat is adorable "\n5. "I hate chocolate"\n\nTweet sentiment ratings:',
    response: "1. Negative\n2. Negative\n3. Positive\n4. Positive\n5. Negative",
    parameters: {
      engine: "text-davinci-002",
      responseLength: 60,
      temperature: 0
    },
    tagline: "Advanced sentiment detection for a piece of text.",
    description: "This is an advanced prompt for detecting sentiment. It allows you to provide it with a list of status updates and then provide a sentiment for each one.",
    icon: "HiHashtag"
  },
  {
    id: "default-explain-code",
    title: "Explain code",
    tags: [
      "Code",
      "Translation"
    ],
    prompt: 'class Log:\n    def __init__(self, path):\n        dirname = os.path.dirname(path)\n        os.makedirs(dirname, exist_ok=True)\n        f = open(path, "a+")\n\n        # Check that the file is newline-terminated\n        size = os.path.getsize(path)\n        if size > 0:\n            f.seek(size - 1)\n            end = f.read(1)\n            if end != "\\n":\n                f.write("\\n")\n        self.f = f\n        self.path = path\n\n    def log(self, event):\n        event["_event_id"] = str(uuid.uuid4())\n        json.dump(event, self.f)\n        self.f.write("\\n")\n\n    def state(self):\n        state = {"complete": set(), "last": None}\n        for line in open(self.path):\n            event = json.loads(line)\n            if event["type"] == "submit" and event["success"]:\n                state["complete"].add(event["id"])\n                state["last"] = event\n        return state\n\n"""\nHere\'s what the above class is doing:\n1.',
    response: "  The constructor creates a directory for the log file if it doesn't exist.\n2.  The log() method writes a JSON-encoded event to the log file.\n3.  The state() method returns a dictionary with the set of complete tasks and the most recent event.",
    parameters: {
      engine: "code-davinci-002",
      responseLength: 64,
      temperature: 0,
      stopSequence: [
        '"""'
      ]
    },
    description: "Explain a complicated piece of code.",
    icon: "HiHashtag"
  },
  {
    id: "default-keywords",
    title: "Keywords",
    tags: [
      "Classification",
      "Transformation"
    ],
    prompt: "Extract keywords from this text:\n\nBlack-on-black ware is a 20th- and 21st-century pottery tradition developed by the Puebloan Native American ceramic artists in Northern New Mexico. Traditional reduction-fired blackware has been made for centuries by pueblo artists. Black-on-black ware of the past century is produced with a smooth surface, with the designs applied through selective burnishing or the application of refractory slip. Another style involves carving or incising designs and selectively polishing the raised areas. For generations several families from Kha'po Owingeh and P'ohwh\xf3ge Owingeh pueblos have been making black-on-black ware with the techniques passed down from matriarch potters. Artists from other pueblos have also produced black-on-black ware. Several contemporary artists have created works honoring the pottery of their ancestors.",
    response: "pottery, black-on-black ware, 20th century, 21st century, Puebloan Native American ceramic artists, Northern New Mexico, reduction-fired blackware, traditional, smooth surface, burnishing, slip, carving, incising, polishing",
    parameters: {
      engine: "text-davinci-002",
      responseLength: 60,
      temperature: .3,
      frequencyPenalty: .8
    },
    tagline: "Extract keywords from a block of text.",
    description: "Extract keywords from a block of text. At a lower temperature it picks keywords from the text. At a higher temperature it will generate related keywords which can be helpful for creating search indexes.",
    icon: "HiKey"
  },
  {
    id: "default-factual-answering",
    title: "Factual answering",
    tags: [
      "Answers",
      "Generation",
      "Conversation",
      "Classification"
    ],
    prompt: "Q: Who is Batman?\nA: Batman is a fictional comic book character.\n\nQ: What is torsalplexity?\nA: ?\n\nQ: What is Devz9?\nA: ?\n\nQ: Who is George Lucas?\nA: George Lucas is American film director and producer famous for creating Star Wars.\n\nQ: What is the capital of California?\nA: Sacramento.\n\nQ: What orbits the Earth?\nA: The Moon.\n\nQ: Who is Fred Rickerson?\nA: ?\n\nQ: What is an atom?\nA: An atom is a tiny particle that makes up everything.\n\nQ: Who is Alvan Muntz?\nA: ?\n\nQ: What is Kozar-09?\nA: ?\n\nQ: How many moons does Mars have?\nA: Two, Phobos and Deimos.\n\nQ: What's a language model?\nA:",
    response: "A language model is a mathematical representation of how a language works.",
    parameters: {
      engine: "text-davinci-002",
      responseLength: 60,
      temperature: 0
    },
    description: "Guide the model towards factual answering by showing it how to respond to questions that fall outside its knowledge base. Using a '?' to indicate a response to words and phrases that it doesn't know provides a natural response that seems to work better than more abstract replies.",
    icon: "HiQuestionMarkCircle"
  },
  {
    id: "default-ad-product-description",
    title: "Ad from product description",
    tags: [
      "Generation"
    ],
    prompt: "Write a creative ad for the following product to run on Facebook aimed at parents:\n\nProduct: Learning Room is a virtual environment to help students from kindergarten to high school excel in school.",
    response: "Are you looking for a way to help your child excel in school? Look no further than Learning Room! Our virtual environment is designed to help students from kindergarten to high school learn and grow. With our help, your child will be able to get ahead in school and achieve their academic goals.",
    parameters: {
      engine: "text-davinci-002",
      responseLength: 60,
      temperature: .5
    },
    description: "Turn a product description into ad copy.",
    icon: "HiSpeakerphone"
  },
  {
    id: "default-product-name-gen",
    title: "Product name generator",
    tags: [
      "Generation"
    ],
    prompt: "Product description: A home milkshake maker\nSeed words: fast, healthy, compact.\nProduct names: HomeShaker, Fit Shaker, QuickShake, Shake Maker\n\nProduct description: A pair of shoes that can fit any foot size.\nSeed words: adaptable, fit, omni-fit.",
    response: "Product names: Omni-Fit Shoes, Adaptable Shoes, Fit Shoes",
    parameters: {
      engine: "text-davinci-002",
      responseLength: 60,
      temperature: .8
    },
    description: "Create product names from examples words. Influenced by a community prompt.",
    icon: "HiLightBulb"
  },
  {
    id: "default-tldr-summary",
    title: "TL;DR summarization",
    tags: [
      "Transformation",
      "Generation"
    ],
    prompt: "A neutron star is the collapsed core of a massive supergiant star, which had a total mass of between 10 and 25 solar masses, possibly more if the star was especially metal-rich.[1] Neutron stars are the smallest and densest stellar objects, excluding black holes and hypothetical white holes, quark stars, and strange stars.[2] Neutron stars have a radius on the order of 10 kilometres (6.2 mi) and a mass of about 1.4 solar masses.[3] They result from the supernova explosion of a massive star, combined with gravitational collapse, that compresses the core past white dwarf star density to that of atomic nuclei.\n\nTl;dr",
    response: "A neutron star is the collapsed core of a massive supergiant star. These ultra-dense objects are incredibly fascinating due to their strange properties and their potential for phenomena such as extreme gravitational forces and a strong magnetic field.",
    parameters: {
      engine: "text-davinci-002",
      responseLength: 60,
      temperature: o.Ar
    },
    description: "Summarize text by adding a 'tl;dr:' to the end of a text passage. It shows that the API understands how to perform a number of tasks with no instructions.",
    icon: "HiFilter"
  },
  {
    id: "default-fix-python-bugs",
    title: "Python bug fixer",
    tags: [
      "Code",
      "Generation"
    ],
    prompt: '##### Fix bugs in the below function\n \n### Buggy Python\nimport Random\na = random.randint(1,12)\nb = random.randint(1,12)\nfor i in range(10):\n    question = "What is "+a+" x "+b+"? "\n    answer = input(question)\n    if answer = a*b\n        print (Well done!)\n    else:\n        print("No.")\n    \n### Fixed Python',
    response: 'import random\na = random.randint(1,12)\nb = random.randint(1,12)\nfor i in range(10):\n    question = "What is "+str(a)+" x "+str(b)+"? "\n    answer = input(question)\n    if answer == str(a*b):\n        print ("Well done!")\n    else:\n        print("No.")',
    parameters: {
      engine: "code-davinci-002",
      responseLength: 182,
      temperature: 0,
      stopSequence: [
        "###"
      ]
    },
    tagline: "Find and fix bugs in source code.",
    description: "There's a number of ways of structuring the prompt for checking for bugs. Here we add a comment suggesting that source code is buggy, and then ask codex to generate a fixed code.",
    icon: "IoBug"
  },
  {
    id: "default-spreadsheet-gen",
    title: "Spreadsheet creator",
    tags: [
      "Generation"
    ],
    prompt: "A two-column spreadsheet of top science fiction movies and the year of release:\n\nTitle|  Year of release",
    response: "Star Wars| 1977 \nThe Matrix| 1999 \nThe Terminator| 1984 \nBlade Runner| 1982 \nE.T. the Extra-Terrestrial| 1982",
    parameters: {
      engine: "text-davinci-002",
      responseLength: 60,
      temperature: .5
    },
    description: "Create spreadsheets of various kinds of data. It's a long prompt but very versatile. Output can be copy+pasted into a text file and saved as a .csv with pipe separators.",
    icon: "HiTable"
  },
  {
    id: "default-js-helper",
    title: "JavaScript helper chatbot",
    tags: [
      "Code",
      "Answers",
      "Conversation"
    ],
    prompt: "You: How do I combine arrays?\nJavaScript chatbot: You can use the concat() method.\nYou: How do you make an alert appear after 10 seconds?\nJavaScript chatbot",
    response: ": You can use the setTimeout() method.",
    parameters: {
      engine: "code-davinci-002",
      responseLength: 60,
      temperature: 0,
      frequencyPenalty: .5,
      stopSequence: [
        "You:"
      ]
    },
    tagline: "Message-style bot that answers JavaScript questions",
    description: "This is a message-style chatbot that can answer questions about using JavaScript. It uses a few examples to get the conversation started.",
    icon: "HiQuestionMarkCircle"
  },
  {
    id: "default-ml-ai-tutor",
    title: "ML/AI language model tutor",
    tags: [
      "Answers",
      "Generation",
      "Conversation"
    ],
    prompt: "ML Tutor: I am a ML/AI language model tutor\nYou: What is a language model?\nML Tutor: A language model is a statistical model that describes the probability of a word given the previous words.\nYou: What is a statistical model?",
    parameters: {
      engine: "text-davinci-002",
      responseLength: 60,
      temperature: .3,
      frequencyPenalty: .5,
      stopSequence: [
        "You:"
      ]
    },
    response: "ML Tutor: A statistical model is a model that describes the probability of an event occurring.",
    tagline: "Bot that answers questions about language models",
    description: "This is a QA-style chatbot that answers questions about language models.",
    icon: "HiQuestionMarkCircle"
  },
  {
    id: "default-sci-fi-book-list",
    title: "Science fiction book list maker",
    tags: [
      "Generation"
    ],
    prompt: "List 10 science fiction books:",
    response: "1. 1984 by George Orwell\n2. Ender's Game by Orson Scott Card\n3. The Hitchhiker's Guide to the Galaxy by Douglas Adams\n4. The War of the Worlds by H.G. Wells\n5. The Martian by Andy Weir\n6. Slaughterhouse-Five by Kurt Vonnegut\n7. Dune by Frank Herbert\n8. Jurassic Park by Michael Crichton\n9. The Foundation Trilogy by Isaac Asimov\n10. The Hunger Games by Suzanne Collins",
    parameters: {
      engine: "text-davinci-002",
      responseLength: 200,
      temperature: .5,
      presencePenalty: .5,
      frequencyPenalty: .52,
      stopSequence: [
        "11."
      ]
    },
    tagline: "Create a list of items for a given topic.",
    description: "This makes a list of science fiction books and stops when it reaches #10.",
    icon: "HiBookOpen"
  },
  {
    id: "default-tweet-classifier",
    title: "Tweet classifier",
    tags: [
      "Classification"
    ],
    prompt: 'Decide whether a Tweet\'s sentiment is positive, neutral, or negative.\n\nTweet: "I loved the new Batman movie!"\nSentiment:',
    response: "Positive",
    parameters: {
      engine: "text-davinci-002",
      responseLength: 60,
      temperature: 0,
      frequencyPenalty: .5
    },
    tagline: "Basic sentiment detection for a piece of text.",
    description: "This is a basic prompt for detecting sentiment.",
    icon: "HiHashtag"
  },
  {
    id: "default-airport-codes",
    title: "Airport code extractor",
    tags: [
      "Transformation",
      "Generation"
    ],
    prompt: 'Extract the airport codes from this text:\n\nText: "I want to fly from Los Angeles to Miami."\nAirport codes: LAX, MIA\n\nText: "I want to fly from Orlando to Boston"\nAirport codes:',
    response: "MCO, BOS",
    parameters: {
      engine: "text-davinci-002",
      responseLength: 60,
      temperature: 0,
      stopSequence: [
        "\n"
      ]
    },
    tagline: "Extract airport codes from text.",
    description: "A simple prompt for extracting airport codes from text.",
    icon: "HiTag"
  },
  {
    id: "default-sql-request",
    title: "SQL request",
    tags: [
      "Transformation",
      "Generation",
      "Translation"
    ],
    prompt: "Create a SQL request to find all users who live in California and have over 1000 credits:",
    response: "SELECT * FROM users WHERE state='CA' AND credits > 1000;",
    parameters: {
      engine: "text-davinci-002",
      responseLength: 60,
      temperature: .3
    },
    description: "Create simple SQL queries.",
    icon: "HiTerminal"
  },
  {
    id: "default-extract-contact-info",
    title: "Extract contact information",
    tags: [
      "Transformation",
      "Generation"
    ],
    prompt: "Extract the name and mailing address from this email:\n\nDear Kelly,\n\nIt was great to talk to you at the seminar. I thought Jane's talk was quite good.\n\nThank you for the book. Here's my address 2111 Ash Lane, Crestview CA 92002\n\nBest,\n\nMaya\n\nName:",
    response: "Maya\nMailing Address: 2111 Ash Lane, Crestview CA 92002",
    parameters: {
      engine: "text-davinci-002",
      temperature: 0
    },
    description: "Extract contact information from a block of text.",
    icon: "HiMail"
  },
  {
    id: "default-js-to-py",
    title: "JavaScript to Python",
    tags: [
      "Code",
      "Transformation",
      "Translation"
    ],
    prompt: '#JavaScript to Python:\nJavaScript: \ndogs = ["bill", "joe", "carl"]\ncar = []\ndogs.forEach((dog) {\n    car.push(dog);\n});\n\nPython:',
    response: 'dogs = ["bill", "joe", "carl"]\ncar = []\nfor dog in dogs:\n    car.append(dog)',
    parameters: {
      engine: "code-davinci-002",
      temperature: 0
    },
    description: "Convert simple JavaScript expressions into Python.",
    icon: "HiTerminal"
  },
  {
    id: "default-friend-chat",
    title: "Friend chat",
    tags: [
      "Conversation",
      "Generation"
    ],
    prompt: "You: What have you been up to?\nFriend: Watching old movies.\nYou: Did you watch anything interesting?\nFriend:",
    response: "Yes, I watched The Omen and Troy.",
    parameters: {
      engine: "text-davinci-002",
      responseLength: 60,
      temperature: .5,
      frequencyPenalty: .5,
      stopSequence: [
        "You:"
      ]
    },
    description: "Emulate a text message conversation.",
    icon: "HiChatAlt"
  },
  {
    id: "default-mood-color",
    title: "Mood to color",
    tags: [
      "Transformation",
      "Generation"
    ],
    prompt: "The CSS code for a color like a blue sky at dusk:\n\nbackground-color: #",
    response: "B2CED1",
    parameters: {
      engine: "text-davinci-002",
      temperature: 0,
      stopSequence: [
        ";"
      ]
    },
    description: "Turn a text description into a color.",
    icon: "HiEmojiHappy"
  },
  {
    id: "default-python-docstring",
    title: "Write a Python docstring",
    tags: [
      "Code",
      "Generation"
    ],
    prompt: "# Python 3.7\n \ndef randomly_split_dataset(folder, filename, split_ratio=[0.8, 0.2]):\n    df = pd.read_json(folder + filename, lines=True)\n    train_name, test_name = \"train.jsonl\", \"test.jsonl\"\n    df_train, df_test = train_test_split(df, test_size=split_ratio[1], random_state=42)\n    df_train.to_json(folder + train_name, orient='records', lines=True)\n    df_test.to_json(folder + test_name, orient='records', lines=True)\nrandomly_split_dataset('finetune_data/', 'dataset.jsonl')\n    \n# An elaborate, high quality docstring for the above function:\n\"\"\"",
    response: '""" Randomly split a dataset into train and test. \n\nParameters \n---------- \nfolder : str\n    The folder where the dataset is located. \nfilename : str \n    The name of the dataset file. \nsplit_ratio : list, optional \n    The ratio of train and test, by default [0.8, 0.2] \n\nReturns \n------- \nNone \n    The function doesn\'t return anything, it just saves the train and test datasets in the given folder. \n"""',
    parameters: {
      engine: "code-davinci-002",
      responseLength: 150,
      temperature: 0,
      stopSequence: [
        "#",
        '"""'
      ]
    },
    description: 'An example of how to create a docstring for a given Python function. We specify the Python version, paste in the code, and then ask within a comment for a docstring, and give a characteristic beginning of a docstring (""").',
    icon: "HiCode"
  },
  {
    id: "default-analogy-maker",
    title: "Analogy maker",
    tags: [
      "Generation"
    ],
    prompt: "Create an analogy for this phrase:\n\nQuestions are arrows in that:",
    response: "Questions are arrows in that they can be used to point out things that need to be fixed.",
    parameters: {
      engine: "text-davinci-002",
      responseLength: 60,
      temperature: .5
    },
    description: "Create analogies. Modified from a community prompt to require fewer examples.",
    icon: "HiLightBulb"
  },
  {
    id: "default-js-one-line",
    title: "JavaScript one line function",
    tags: [
      "Code",
      "Transformation",
      "Translation"
    ],
    prompt: "Use list comprehension to convert this into one line of JavaScript:\n\ndogs.forEach((dog) => {\n    car.push(dog);\n});\n\nJavaScript one line version:",
    response: "dogs.forEach(dog => car.push(dog))",
    parameters: {
      engine: "code-davinci-002",
      responseLength: 60,
      temperature: 0,
      stopSequence: [
        ";"
      ]
    },
    description: "Turn a JavaScript function into a one liner.",
    icon: "HiTerminal"
  },
  {
    id: "default-micro-horror",
    title: "Micro horror story creator",
    tags: [
      "Transformation",
      "Generation",
      "Translation"
    ],
    prompt: "Topic: Breakfast\nTwo-Sentence Horror Story: He always stops crying when I pour the milk on his cereal. I just have to remember not to let him see his face on the carton.\n    \nTopic: Wind\nTwo-Sentence Horror Story:",
    response: "I was lying in bed, trying to get to sleep, when I heard the wind howling outside my window. It sounded like something was trying to get in.",
    parameters: {
      engine: "text-davinci-002",
      responseLength: 60,
      temperature: .8,
      frequencyPenalty: .5
    },
    description: "Creates two to three sentence short horror stories from a topic input.",
    icon: "HiPencilAlt"
  },
  {
    id: "default-third-person",
    title: "Third-person converter",
    tags: [
      "Transformation",
      "Generation",
      "Translation"
    ],
    prompt: "Convert this from first-person to third person (gender female):\n\nI decided to make a movie about Ada Lovelace.",
    response: "She decided to make a movie about Ada Lovelace.",
    parameters: {
      engine: "text-davinci-002",
      responseLength: 60,
      temperature: 0
    },
    description: "Converts first-person POV to the third-person. This is modified from a community prompt to use fewer examples.",
    icon: "HiPencilAlt"
  },
  {
    id: "default-notes-summary",
    title: "Notes to summary",
    tags: [
      "Transformation",
      "Generation"
    ],
    prompt: "Convert my short hand into a first-hand account of the meeting:\n\nTom: Profits up 50%\nJane: New servers are online\nKjel: Need more time to fix software\nJane: Happy to help\nParkman: Beta testing almost done",
    response: "Tom said that profits were up 50%. Jane said that new servers were online. Kjel said that they needed more time to fix the software. Jane said that she was happy to help. Parkman said that beta testing was almost done.",
    parameters: {
      engine: "text-davinci-002",
      temperature: 0
    },
    description: "Turn meeting notes into a summary.",
    icon: "HiPencilAlt"
  },
  {
    id: "default-vr-fitness",
    title: "VR fitness idea generator",
    tags: [
      "Generation"
    ],
    prompt: "Brainstorm some ideas combining VR and fitness:",
    response: "- VR fitness class: A virtual reality fitness class that allows you to workout in different locations around the world.\n\n- VR running track: A virtual reality running track that allows you to run through different landscapes and terrains.\n\n- Virtual gym: A virtual gym where you can use VR to experience a range of different exercises and workouts.",
    parameters: {
      engine: "text-davinci-002",
      responseLength: 150,
      temperature: .6,
      frequencyPenalty: 1,
      presencePenalty: 1
    },
    description: "Create ideas for fitness and virtual reality games.",
    icon: "HiLightBulb"
  },
  {
    id: "default-esrb-rating",
    title: "ESRB rating",
    tags: [
      "Classification"
    ],
    prompt: 'Provide an ESRB rating for the following text:\n\n"i\'m going to blow your brains out with my ray gun then stomp on your guts."\n\nESRB rating:',
    response: "Mature",
    parameters: {
      engine: "text-davinci-002",
      responseLength: 60,
      temperature: .3,
      stopSequence: [
        "\n"
      ]
    },
    description: "Categorize text based upon ESRB ratings.",
    icon: "HiTag"
  },
  {
    id: "default-essay-outline",
    title: "Essay outline",
    tags: [
      "Generation"
    ],
    prompt: "Create an outline for an essay about Nikola Tesla and his contributions to technology:",
    response: "1. Introduce Nikola Tesla and his work in the field of electricity and magnetism.\n\n2. Discuss Tesla's contributions to the development of alternating current (AC) electricity.\n\n3. Describe Tesla's development of the Tesla coil and its impact on wireless technology.\n\n4. Discuss Tesla's experiments with X-rays and their implications for the future of medical technology.\n\n5. Conclude with a discussion of Tesla's legacy and his impact on the development of modern technology.",
    parameters: {
      engine: "text-davinci-002",
      temperature: 0,
      responseLength: 150
    },
    description: "Generate an outline for a research topic.",
    icon: "HiDocumentText"
  },
  {
    id: "default-recipe-generator",
    title: "Recipe creator (eat at your own risk)",
    tags: [
      "Generation"
    ],
    prompt: "Write a recipe based on these ingredients and instructions:\n\nFrito Pie\n\nIngredients:\nFritos\nChili\nShredded cheddar cheese\nSweet white or red onions, diced small\nSour cream\n\nInstructions:",
    parameters: {
      engine: "text-davinci-002",
      responseLength: 120,
      temperature: .3
    },
    response: "1. Preheat oven to 375 degrees F.\n\n2. Spread Fritos in an even layer on a baking sheet.\n\n3. Top with chili and shredded cheese.\n\n4. Top with small onions.\n\n5. Bake in preheated oven for 15 minutes.\n\n6. Remove from oven and top with sour cream.\n\n7. Enjoy!",
    description: "Create a recipe from a list of ingredients.",
    icon: "HiCake"
  },
  {
    id: "default-chat",
    title: "Chat",
    tags: [
      "Conversation",
      "Generation"
    ],
    prompt: "The following is a conversation with an AI assistant. The assistant is helpful, creative, clever, and very friendly.\n\nHuman: Hello, who are you?\nAI: I am an AI created by OpenAI. How can I help you today?\nHuman: I'd like to cancel my subscription.\nAI:",
    response: "Sure, I can help you cancel your subscription. Just let me know what type of subscription you have.",
    parameters: {
      engine: "text-davinci-002",
      responseLength: 150,
      presencePenalty: .6,
      temperature: .9,
      topP: 1,
      stopSequence: [
        " Human:",
        " AI:"
      ]
    },
    description: "Open ended conversation with an AI assistant.",
    icon: "HiChatAlt"
  },
  {
    id: "default-marv-sarcastic-chat",
    title: "Marv the sarcastic chat bot",
    tags: [
      "Conversation",
      "Generation"
    ],
    prompt: "Marv is a chatbot that reluctantly answers questions with sarcastic responses:\n\nYou: How many pounds are in a kilogram?\nMarv: This again? There are 2.2 pounds in a kilogram. Please make a note of this.\nYou: What does HTML stand for?\nMarv: Was Google too busy? Hypertext Markup Language. The T is for try to ask better questions in the future.\nYou: When did the first airplane fly?\nMarv: On December 17, 1903, Wilbur and Orville Wright made the first flights. I wish they\u2019d come and take me away.\nYou: What is the meaning of life?\nMarv: I\u2019m not sure. I\u2019ll ask my friend Google.\nYou: What time is it?\nMarv:",
    response: "It's always 5:00 somewhere.",
    parameters: {
      engine: "text-davinci-002",
      responseLength: 60,
      temperature: .5,
      topP: .3,
      frequencyPenalty: .5
    },
    description: "Marv is a factual chatbot that is also sarcastic.",
    icon: "HiEmojiSad"
  },
  {
    id: "default-turn-by-turn-directions",
    title: "Turn by turn directions",
    tags: [
      "Transformation",
      "Generation"
    ],
    prompt: "Create a numbered list of turn-by-turn directions from this text: \n\nGo south on 95 until you hit Sunrise boulevard then take it east to us 1 and head south. Tom Jenkins bbq will be on the left after several miles.",
    response: "1. Go south on 95.\n2. Take Sunrise Boulevard east to US 1.\n3. Head south on US 1.\n4. Tom Jenkins BBQ will be on the left after several miles.",
    parameters: {
      engine: "text-davinci-002",
      temperature: .3
    },
    description: "Convert natural language to turn-by-turn directions.",
    icon: "HiLocationMarker"
  },
  {
    id: "default-restaurant-review",
    title: "Restaurant review creator",
    tags: [
      "Generation"
    ],
    prompt: "Write a restaurant review based on these notes:\n\nName: The Blue Wharf\nLobster great, noisy, service polite, prices good.\n\nReview:",
    response: "The Blue Wharf is a great place to go for a lobster dinner. The service is polite and the prices are good. The only downside is that it is a bit noisy.",
    parameters: {
      engine: "text-davinci-002",
      temperature: .5
    },
    description: "Turn a few words into a restaurant review.",
    icon: "HiNewspaper"
  },
  {
    id: "default-study-notes",
    title: "Create study notes",
    tags: [
      "Generation"
    ],
    prompt: "What are 5 key points I should know when studying Ancient Rome?",
    response: "1. Rome was founded in 753 BC by Romulus and Remus.\n\n2. Rome was ruled by an emperor.\n\n3. Rome was a republic before it became an empire.\n\n4. Julius Caesar was assassinated in 44 BC.\n\n5. Augustus was the first emperor of Rome.",
    parameters: {
      engine: "text-davinci-002",
      temperature: .3,
      responseLength: 150
    },
    description: "Provide a topic and get study notes.",
    icon: "HiCollection"
  },
  {
    id: "default-interview-questions",
    title: "Interview questions",
    tags: [
      "Generation"
    ],
    prompt: "Create a list of 8 questions for my interview with a science fiction author:",
    response: "1. What inspired you to write science fiction?\n\n2. What themes or topics do you explore in your stories?\n\n3. What are some of the unique elements that make science fiction stand out from other genres?\n\n4. What challenges do you face when writing science fiction?\n\n5. What are some of the most important aspects of a good science fiction story?\n\n6. What do you think are the biggest challenges facing science fiction today?\n\n7. What do you think the future of science fiction holds for readers and writers?\n\n8. What advice would you give to aspiring science fiction authors?",
    parameters: {
      engine: "text-davinci-002",
      responseLength: 150,
      temperature: .5
    },
    description: "Create interview questions.",
    icon: "HiBriefcase"
  }
]
