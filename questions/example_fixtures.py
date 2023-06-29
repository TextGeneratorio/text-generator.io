openai_examples = {
    "default-qa": {
        "id": "default-qa",
        "title": "Q&A",
        "tags": ["Answers", "Generation", "Conversation"],
        "generate_params": {
            "text": 'I am a highly intelligent question answering bot. If you ask me a question that is rooted in truth, I will give you the answer. If you ask me a question that is nonsense, trickery, or has no clear answer, I will respond with "Unknown".\n\nQ: What is human life expectancy in the United States?\nA: Human life expectancy in the United States is 78 years.\n\nQ: Who was president of the United States in 1955?\nA: Dwight D. Eisenhower was president of the United States in 1955.\n\nQ: Which party did he belong to?\nA: He belonged to the Republican Party.\n\nQ: What is the square root of banana?\nA: Unknown\n\nQ: How does a telescope work?\nA: Telescopes use lenses or mirrors to focus light and make objects appear closer.\n\nQ: Where were the 1992 Olympics held?\nA: The 1992 Olympics were held in Barcelona, Spain.\n\nQ: How many squigs are in a bonk?\nA: Unknown\n\nQ: Where is the Valley of Kings?\nA:',
            "max_length": 100,
            "number_of_results": 4,
            "temperature": 1,
            "top_p": 1,
            "stop_sequences": ["\n"],
        },
        "description": "Answer questions based on existing knowledge.",
        "icon": "QuestionMarkCircle",
        "results": [
            {
                "generated_text": 'I am a highly intelligent question answering bot. If you ask me a question that is rooted in truth, I will give you the answer. If you ask me a question that is nonsense, trickery, or has no clear answer, I will respond with "Unknown".\n\nQ: What is human life expectancy in the United States?\nA: Human life expectancy in the United States is 78 years.\n\nQ: Who was president of the United States in 1955?\nA: Dwight D. Eisenhower was president of the United States in 1955.\n\nQ: Which party did he belong to?\nA: He belonged to the Republican Party.\n\nQ: What is the square root of banana?\nA: Unknown\n\nQ: How does a telescope work?\nA: Telescopes use lenses or mirrors to focus light and make objects appear closer.\n\nQ: Where were the 1992 Olympics held?\nA: The 1992 Olympics were held in Barcelona, Spain.\n\nQ: How many squigs are in a bonk?\nA: Unknown\n\nQ: Where is the Valley of Kings?\nA: Unknown',
                "stop_reason": "\n",
            },
            {
                "generated_text": 'I am a highly intelligent question answering bot. If you ask me a question that is rooted in truth, I will give you the answer. If you ask me a question that is nonsense, trickery, or has no clear answer, I will respond with "Unknown".\n\nQ: What is human life expectancy in the United States?\nA: Human life expectancy in the United States is 78 years.\n\nQ: Who was president of the United States in 1955?\nA: Dwight D. Eisenhower was president of the United States in 1955.\n\nQ: Which party did he belong to?\nA: He belonged to the Republican Party.\n\nQ: What is the square root of banana?\nA: Unknown\n\nQ: How does a telescope work?\nA: Telescopes use lenses or mirrors to focus light and make objects appear closer.\n\nQ: Where were the 1992 Olympics held?\nA: The 1992 Olympics were held in Barcelona, Spain.\n\nQ: How many squigs are in a bonk?\nA: Unknown\n\nQ: Where is the Valley of Kings?\nA: unknown region. unexplored areas have different types of rocks and soil.',
                "stop_reason": "\n",
            },
            {
                "generated_text": 'I am a highly intelligent question answering bot. If you ask me a question that is rooted in truth, I will give you the answer. If you ask me a question that is nonsense, trickery, or has no clear answer, I will respond with "Unknown".\n\nQ: What is human life expectancy in the United States?\nA: Human life expectancy in the United States is 78 years.\n\nQ: Who was president of the United States in 1955?\nA: Dwight D. Eisenhower was president of the United States in 1955.\n\nQ: Which party did he belong to?\nA: He belonged to the Republican Party.\n\nQ: What is the square root of banana?\nA: Unknown\n\nQ: How does a telescope work?\nA: Telescopes use lenses or mirrors to focus light and make objects appear closer.\n\nQ: Where were the 1992 Olympics held?\nA: The 1992 Olympics were held in Barcelona, Spain.\n\nQ: How many squigs are in a bonk?\nA: Unknown\n\nQ: Where is the Valley of Kings?\nA: unknown site near Cairo, Egypt, possibly the ancient city of Memphis.[1] Egyptian ruins there include pyramid structures such as the Sphinx, Mausoleum KV31, and several tombs connected through vast complex pathways, known as "The Valley of Reeds." unknown location north of the capital Amman, Jordan on Jordanian territory.[2] unknown country east of Tehran, Iran.[3] Israel\'s Golan Heights are an independent border area located just west of Syria. Unknown',
                "stop_reason": "\n",
            },
            {
                "generated_text": 'I am a highly intelligent question answering bot. If you ask me a question that is rooted in truth, I will give you the answer. If you ask me a question that is nonsense, trickery, or has no clear answer, I will respond with "Unknown".\n\nQ: What is human life expectancy in the United States?\nA: Human life expectancy in the United States is 78 years.\n\nQ: Who was president of the United States in 1955?\nA: Dwight D. Eisenhower was president of the United States in 1955.\n\nQ: Which party did he belong to?\nA: He belonged to the Republican Party.\n\nQ: What is the square root of banana?\nA: Unknown\n\nQ: How does a telescope work?\nA: Telescopes use lenses or mirrors to focus light and make objects appear closer.\n\nQ: Where were the 1992 Olympics held?\nA: The 1992 Olympics were held in Barcelona, Spain.\n\nQ: How many squigs are in a bonk?\nA: Unknown\n\nQ: Where is the Valley of Kings?\nA: Egypt (country) Egypt (people), ancient kingdom of Egypt\'s capital city Cairo.',
                "stop_reason": "\n",
            },
        ],
    },
    "default-grammar": {
        "id": "default-grammar",
        "title": "Grammar correction",
        "tags": ["Transformation", "Generation"],
        "generate_params": {
            "text": "Correct this to standard English:\n\nShe no went to the market.",
            "max_length": 60,
            "number_of_results": 4,
            "temperature": 1,
        },
        "description": "Corrects sentences into standard English.",
        "icon": "AcademicCap",
        "results": [
            {
                "generated_text": "Correct this to standard English:\n\nShe no went to the market. She didn't go into town. The following translations are from French or Spanish and do not belong in the text (please correct them): No se fue a la ciudad. Ella no va al mercado. La traducción que sigue son del francés o el español y no pertenecen en este texto (por favor, corr",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Correct this to standard English:\n\nShe no went to the market. She didn't go into the market either. No need for commas, because they are a single sentence with two parts. She didn't want to be there. She was not interested in going. Her answer confirmed her position. Yes she did. No she didn't, but that's beside the point. No she did",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Correct this to standard English:\n\nShe no went to the market. She did not go to buy food at the market. No she didn't, but thank you for asking! Yes she went and bought some food from the local market, though. Yes, yes, yes -- she actually went and ate there as well. Yes, she's a vegetarian - but no, it's nothing",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Correct this to standard English:\n\nShe no went to the market. She didn't go into town today. she doesn't like being out in public at all so she stayed home. No, she didn't go into town. She stayed home! Yes, that is correct. You can't have her going around the streets of New York city when it's 110 degrees outside and she's a little girl",
                "stop_reason": "max_length",
            },
        ],
    },
    "default-summarize": {
        "id": "default-summarize",
        "title": "Summarize for a 2nd grader",
        "tags": ["Transformation", "Generation"],
        "generate_params": {
            "text": "Summarize this for a second-grade student:\n\nJupiter is the fifth planet from the Sun and the largest in the Solar System. It is a gas giant with a mass one-thousandth that of the Sun, but two-and-a-half times that of all the other planets in the Solar System combined. Jupiter is one of the brightest objects visible to the naked eye in the night sky, and has been known to ancient civilizations since before recorded history. It is named after the Roman god Jupiter.[19] When viewed from Earth, Jupiter can be bright enough for its reflected light to cast visible shadows,[20] and is on average the third-brightest natural object in the night sky after the Moon and Venus.",
            "number_of_results": 4,
            "temperature": 0,
        },
        "description": "Translates difficult text into simpler concepts.",
        "icon": "FastForward",
        "results": [
            {
                "generated_text": "Summarize this for a second-grade student:\n\nJupiter is the fifth planet from the Sun and the largest in the Solar System. It is a gas giant with a mass one-thousandth that of the Sun, but two-and-a-half times that of all the other planets in the Solar System combined. Jupiter is one of the brightest objects visible to the naked eye in the night sky, and has been known to ancient civilizations since before recorded history. It is named after the Roman god Jupiter.[19] When viewed from Earth, Jupiter can be bright enough for its reflected light to cast visible shadows,[20] and is on average the third-brightest natural object in the night sky after the Moon and Venus. The solar system is made up mainly of gases, dust, water, metals, liquids, ice and rock. An eighth scale is used to indicate relative magnitudes of celestial objects including the Sun, and also stars as well as galaxies. An eighth scale refers back to an earlier model developed by William Herschel which uses ten different ratios. A large amount of matter exists around the Sun called the Solar System, formed over many years through gravitational forces between the various components. There are nine planets in the Solar System",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Summarize this for a second-grade student:\n\nJupiter is the fifth planet from the Sun and the largest in the Solar System. It is a gas giant with a mass one-thousandth that of the Sun, but two-and-a-half times that of all the other planets in the Solar System combined. Jupiter is one of the brightest objects visible to the naked eye in the night sky, and has been known to ancient civilizations since before recorded history. It is named after the Roman god Jupiter.[19] When viewed from Earth, Jupiter can be bright enough for its reflected light to cast visible shadows,[20] and is on average the third-brightest natural object in the night sky after the Moon and Venus. Saturn's rings are made up of dust particles suspended within the gas that surrounds it by gravity. Saturn's outer parts consist mostly of gases called noble gasses or \"sublimes\" because they do not condense into liquids or solids as do most substances at Earth's temperature. This article was written for science education students ages 7–13 years old. Use this passage to teach your child about various topics related to space exploration, including why people study the Solar Systems. Describe what makes jupiter interesting,",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Summarize this for a second-grade student:\n\nJupiter is the fifth planet from the Sun and the largest in the Solar System. It is a gas giant with a mass one-thousandth that of the Sun, but two-and-a-half times that of all the other planets in the Solar System combined. Jupiter is one of the brightest objects visible to the naked eye in the night sky, and has been known to ancient civilizations since before recorded history. It is named after the Roman god Jupiter.[19] When viewed from Earth, Jupiter can be bright enough for its reflected light to cast visible shadows,[20] and is on average the third-brightest natural object in the night sky after the Moon and Venus. The planet's reflective clouds make it possible for sunlight to reach Earth's surface. All images have copyrights. A telescope reveals the detail structure of Jupiter's atmosphere.\nDiscuss what you know about the solar system by pointing out how large and massive the next object will appear if compared with Jupiter. Use your knowledge as an astronaut to show where on our star system we are relative to others. Read the text aloud with young children. Review what is mentioned in class. Point out facts. Have students",
                "stop_reason": "max_length",
            },
            {
                "generated_text": 'Summarize this for a second-grade student:\n\nJupiter is the fifth planet from the Sun and the largest in the Solar System. It is a gas giant with a mass one-thousandth that of the Sun, but two-and-a-half times that of all the other planets in the Solar System combined. Jupiter is one of the brightest objects visible to the naked eye in the night sky, and has been known to ancient civilizations since before recorded history. It is named after the Roman god Jupiter.[19] When viewed from Earth, Jupiter can be bright enough for its reflected light to cast visible shadows,[20] and is on average the third-brightest natural object in the night sky after the Moon and Venus. The name "giant" means very large.  List several things about the solar system. JUPITER Jupiter\'s diameter was measured at 822 distance between 2 points on earth are 4 trillion miles (6.5 billion   km). Name another star and planet near by the moon. Distance from Sol 9.3 trillion Miles (13.4 trillion  kilometers)   1.9 x 10^12 Kg Sun 3.7 x 1011 Kg Jupiter 1/50000 Msun A summary of information',
                "stop_reason": "max_length",
            },
        ],
    },
    "default-openai-api": {
        "id": "default-openai-api",
        "title": "Natural language to OpenAI API",
        "tags": ["Code", "Transformation"],
        "generate_params": {
            "text": '"""\nUtil exposes the following:\nutil.openai() -> authenticates & returns the openai module, which has the following functions:\nopenai.Completion.create(\n    prompt="<my prompt>", # The prompt to start completing from\n    max_tokens=123, # The max number of tokens to generate\n    temperature=1.0 # A measure of randomness\n    echo=True, # Whether to return the prompt in addition to the generated completion\n)\n"""\nimport util\n"""\nCreate an OpenAI completion starting from the prompt "Once upon an AI", no more than 5 tokens. Does not include the prompt.\n"""\n',
            "max_length": 64,
            "number_of_results": 4,
            "temperature": 1,
            "stop_sequences": ['"""'],
        },
        "description": "Create code to call to the OpenAI API using a natural language instruction.",
        "icon": "Annotation",
        "results": [
            {
                "generated_text": '"""\nUtil exposes the following:\nutil.openai() -> authenticates & returns the openai module, which has the following functions:\nopenai.Completion.create(\n    prompt="<my prompt>", # The prompt to start completing from\n    max_tokens=123, # The max number of tokens to generate\n    temperature=1.0 # A measure of randomness\n    echo=True, # Whether to return the prompt in addition to the generated completion\n)\n"""\nimport util\n"""\nCreate an OpenAI completion starting from the prompt "Once upon an AI", no more than 5 tokens. Does not include the prompt.\n"""\nprint(\'Now using a new instance:    \')\noai = util.openai()\ncompletion = oai.Completion().create(\n        prompt=\'Once upon an   \',\n        token_count=0,         max_words=5\n        ) tokens = list(map(str, completion.generate()))\nprint(("\\n" + ("\\nThis',
                "stop_reason": "max_length",
            },
            {
                "generated_text": '"""\nUtil exposes the following:\nutil.openai() -> authenticates & returns the openai module, which has the following functions:\nopenai.Completion.create(\n    prompt="<my prompt>", # The prompt to start completing from\n    max_tokens=123, # The max number of tokens to generate\n    temperature=1.0 # A measure of randomness\n    echo=True, # Whether to return the prompt in addition to the generated completion\n)\n"""\nimport util\n"""\nCreate an OpenAI completion starting from the prompt "Once upon an AI", no more than 5 tokens. Does not include the prompt.\n"""\nprint (openai_completion_from_prompt(\'Once    Upon    An    AI\', 10))\n\n\n',
                "stop_reason": '"""',
            },
            {
                "generated_text": '"""\nUtil exposes the following:\nutil.openai() -> authenticates & returns the openai module, which has the following functions:\nopenai.Completion.create(\n    prompt="<my prompt>", # The prompt to start completing from\n    max_tokens=123, # The max number of tokens to generate\n    temperature=1.0 # A measure of randomness\n    echo=True, # Whether to return the prompt in addition to the generated completion\n)\n"""\nimport util\n"""\nCreate an OpenAI completion starting from the prompt "Once upon an AI", no more than 5 tokens. Does not include the prompt.\n"""\nprint(\'Hello world! \')\n# Completing with a large amount of data is generally bad practice, so use this utility function instead:\n# print(completion("once upon a ai", "", 0, 2)) # No longer supports max_tokens or token limit\n\ndef test_main():\n\tpass',
                "stop_reason": "max_length",
            },
            {
                "generated_text": '"""\nUtil exposes the following:\nutil.openai() -> authenticates & returns the openai module, which has the following functions:\nopenai.Completion.create(\n    prompt="<my prompt>", # The prompt to start completing from\n    max_tokens=123, # The max number of tokens to generate\n    temperature=1.0 # A measure of randomness\n    echo=True, # Whether to return the prompt in addition to the generated completion\n)\n"""\nimport util\n"""\nCreate an OpenAI completion starting from the prompt "Once upon an AI", no more than 5 tokens. Does not include the prompt.\n"""\ndef _OpenAICompletion(prompt=None):\n  ',
                "stop_reason": '"""',
            },
        ],
    },
    "default-text-to-command": {
        "id": "default-text-to-command",
        "title": "Text to command",
        "tags": ["Transformation", "Generation"],
        "generate_params": {
            "text": "Convert this text to a programmatic command:\n\nExample: Ask Constance if we need some bread\nOutput: send-msg `find constance` Do we need some bread?\n\nContact the ski store and figure out if I can get my skis fixed before I leave on Thursday",
            "max_length": 100,
            "number_of_results": 4,
            "temperature": 1,
            "stop_sequences": ["\n"],
        },
        "description": "Translate text into programmatic commands.",
        "icon": "Terminal",
        "results": [
            {
                "generated_text": "Convert this text to a programmatic command:\n\nExample: Ask Constance if we need some bread\nOutput: send-msg `find constance` Do we need some bread?\n\nContact the ski store and figure out if I can get my skis fixed before I leave on Thursday.send-messageto someone Find Constance, will you?",
                "stop_reason": "\n",
            },
            {
                "generated_text": "Convert this text to a programmatic command:\n\nExample: Ask Constance if we need some bread\nOutput: send-msg `find constance` Do we need some bread?\n\nContact the ski store and figure out if I can get my skis fixed before I leave on Thursday morning.",
                "stop_reason": "\n",
            },
            {
                "generated_text": "Convert this text to a programmatic command:\n\nExample: Ask Constance if we need some bread\nOutput: send-msg `find constance` Do we need some bread?\n\nContact the ski store and figure out if I can get my skis fixed before I leave on Thursday. - Send-Private-Msg constance Do we need some bread? Contact the car salesman, he might be able to help with getting me one that is more comfortable for driving at night, and not so loud like the other one I have now.",
                "stop_reason": "\n",
            },
            {
                "generated_text": "Convert this text to a programmatic command:\n\nExample: Ask Constance if we need some bread\nOutput: send-msg `find constance` Do we need some bread?\n\nContact the ski store and figure out if I can get my skis fixed before I leave on Thursday. Send `say #to#,' where '#to#' is your name.",
                "stop_reason": "\n",
            },
        ],
    },
    "default-translate": {
        "id": "default-translate",
        "title": "English to other languages",
        "tags": ["Transformation", "Generation"],
        "generate_params": {
            "text": "Translate this into 1. French, 2. Spanish and 3. Japanese:\n\nWhat rooms do you have available?\n\n1.",
            "max_length": 100,
            "number_of_results": 4,
            "temperature": 0.3,
        },
        "description": "Translates English text into French, Spanish and Japanese.",
        "icon": "GlobeAlt",
        "results": [
            {
                "generated_text": "Translate this into 1. French, 2. Spanish and 3. Japanese:\n\nWhat rooms do you have available?\n\n1. Which rooms are free? 2. What rooms are free? 3. What rooms are free? 4. What rooms are free? 5. What rooms are free? 6. What rooms are free? 7. What rooms are free? 8. What rooms are free? 9. What rooms are free? 10. What rooms are free? 11. What rooms are free? 12. What rooms are free? 13. What rooms are free? 14. What rooms are free? 15. What rooms are",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Translate this into 1. French, 2. Spanish and 3. Japanese:\n\nWhat rooms do you have available?\n\n1. What rooms are free? - En qué habitaciones tienes disponibles? - en español y japonés. - en francés. ¿Qué habitación estás libre? - ¿En cuál de las habitaciones está disponible? - en inglés. ¿Cuáles son tus opciones? - ¿Cuál es tu elección? - en alemán. ¿Cuáles son sus opciones? - ¿Cuál es su opción? - en italiano. ¿Cuáles son mis opciones? - ¿Cuál es mi elección? - en portugués. ¿Cuáles son sus opciones? - ¿Cuál es su opción?",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Translate this into 1. French, 2. Spanish and 3. Japanese:\n\nWhat rooms do you have available?\n\n1. What rooms are free? 1. What rooms are free? 1. What rooms are free? 1. What rooms are free? 1. What rooms are free? 1. What rooms are free? 1. What rooms are free? 1. What rooms are free? 1. What rooms are free? 1. What rooms are free? 1. What rooms are free? 1. What rooms are free? 1. What rooms are free? 1. What rooms are free? 1. What rooms are",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Translate this into 1. French, 2. Spanish and 3. Japanese:\n\nWhat rooms do you have available?\n\n1. What rooms are there? 2. Which ones? 3. What's your room number? 4. Where's the bathroom? 5. How many beds can I sleep in? 6. Is it a double bed or single bed? 7. Do you want to share with someone else? 8. Are you free on weekends? 9. When would be best for me to come see you? 10. Can we meet at my place? 11. Where is your address? 12. What's your phone number? 13",
                "stop_reason": "max_length",
            },
        ],
    },
    "default-stripe-api": {
        "id": "default-stripe-api",
        "title": "Natural language to Stripe API",
        "tags": ["Code", "Transformation"],
        "generate_params": {
            "text": '"""\nUtil exposes the following:\n\nutil.stripe() -> authenticates & returns the stripe module; usable as stripe.Charge.create etc\n"""\nimport util\n"""\nCreate a Stripe token using the users credit card: 5555-4444-3333-2222, expiration date 12 / 28, cvc 521\n"""',
            "max_length": 100,
            "number_of_results": 4,
            "temperature": 1,
            "stop_sequences": ['"""'],
        },
        "description": "Create code to call the Stripe API using natural language.",
        "icon": "CurrencyDollar",
        "results": [
            {
                "generated_text": '"""\nUtil exposes the following:\n\nutil.stripe() -> authenticates & returns the stripe module; usable as stripe.Charge.create etc\n"""\nimport util\n"""\nCreate a Stripe token using the users credit card: 5555-4444-3333-2222, expiration date 12 / 28, cvc 521\n"""\n\n\n\ndef charge(amount=0):\n    ',
                "stop_reason": '"""',
            },
            {
                "generated_text": '"""\nUtil exposes the following:\n\nutil.stripe() -> authenticates & returns the stripe module; usable as stripe.Charge.create etc\n"""\nimport util\n"""\nCreate a Stripe token using the users credit card: 5555-4444-3333-2222, expiration date 12 / 28, cvc 521\n"""\n\n\ndef charge():\n    ',
                "stop_reason": '"""',
            },
            {
                "generated_text": '"""\nUtil exposes the following:\n\nutil.stripe() -> authenticates & returns the stripe module; usable as stripe.Charge.create etc\n"""\nimport util\n"""\nCreate a Stripe token using the users credit card: 5555-4444-3333-2222, expiration date 12 / 28, cvc 521\n"""\n\n\ndef charge(account_id):\n    ',
                "stop_reason": '"""',
            },
            {
                "generated_text": '"""\nUtil exposes the following:\n\nutil.stripe() -> authenticates & returns the stripe module; usable as stripe.Charge.create etc\n"""\nimport util\n"""\nCreate a Stripe token using the users credit card: 5555-4444-3333-2222, expiration date 12 / 28, cvc 521\n"""\n\n\n\ndef charge_create(token_id):\n    ',
                "stop_reason": '"""',
            },
        ],
    },
    "default-sql-translate": {
        "id": "default-sql-translate",
        "title": "SQL translate",
        "tags": ["Code", "Transformation"],
        "generate_params": {
            "text": "### Postgres SQL tables, with their properties:\n#\n# Employee(id, name, department_id)\n# Department(id, name, address)\n# Salary_Payments(id, employee_id, amount, date)\n#\n### A query to list the names of the departments which employed more than 10 employees in the last 3 months\nSELECT",
            "max_length": 150,
            "number_of_results": 4,
            "temperature": 1,
            "stop_sequences": ["#", ";"],
        },
        "description": "Translate natural language to SQL queries.",
        "icon": "QuestionMarkCircle",
        "results": [
            {
                "generated_text": "### Postgres SQL tables, with their properties:\n#\n# Employee(id, name, department_id)\n# Department(id, name, address)\n# Salary_Payments(id, employee_id, amount, date)\n#\n### A query to list the names of the departments which employed more than 10 employees in the last 3 months\nSELECT     d.name FROM\n    SALARY_PAYMENTS AS s     INNER JOIN DEPARTMENT D ON S.DEPARTMENT_ID = D.ID     WHERE         DATEADD (MONTH, -3,  DATE(s.date)) > SYSDATE AND\n        s.employee_id > 0 ORDER BY COUNT (*) DESC LIMIT 5",
                "stop_reason": ";",
            },
            {
                "generated_text": "### Postgres SQL tables, with their properties:\n#\n# Employee(id, name, department_id)\n# Department(id, name, address)\n# Salary_Payments(id, employee_id, amount, date)\n#\n### A query to list the names of the departments which employed more than 10 employees in the last 3 months\nSELECT d.name FROM salpayments_sheet_table ss JOIN depttable d USING (dept_id) WHERE YEARWEEK(ss.date_created) >= '20190101' AND YEARWEEK(SS.DATE_CREATED) <= '20191231'",
                "stop_reason": ";",
            },
            {
                "generated_text": "### Postgres SQL tables, with their properties:\n#\n# Employee(id, name, department_id)\n# Department(id, name, address)\n# Salary_Payments(id, employee_id, amount, date)\n#\n### A query to list the names of the departments which employed more than 10 employees in the last 3 months\nSELECT d.name FROM salary_payments s JOIN employees e ON e.id=s.employee_id AND e.status='active' JOIN departments_dated D ON D.date=getdate()-330 GROUP BY d.name ORDER BY count(d.name) DESC LIMIT 20",
                "stop_reason": ";",
            },
            {
                "generated_text": "### Postgres SQL tables, with their properties:\n#\n# Employee(id, name, department_id)\n# Department(id, name, address)\n# Salary_Payments(id, employee_id, amount, date)\n#\n### A query to list the names of the departments which employed more than 10 employees in the last 3 months\nSELECT d.name FROM salpays s JOIN deptdept d ON (d.id=s.departmet_id) AND ((TO_DATE(s.start_date,'dd/mm/yyyy')) >= TO_DATE(NOW(), 'dd/mm/yyyy') AND  (TO_DATE(SALARY_PAYMENT_AMOUNT,('YYYY-MM-DD HH24:MI:SS'))) BETWEEN DATE_ADD(\nTO_DATE(CURRENT_TIMESTAMP, 'Days:3 MONTHS'), '+10 HOURS'))\nWHERE   d.employees > 10",
                "stop_reason": ";",
            },
        ],
    },
    "default-parse-data": {
        "id": "default-parse-data",
        "title": "Parse unstructured data",
        "tags": ["Transformation", "Generation"],
        "generate_params": {
            "text": "A table summarizing the fruits from Goocrux:\n\nThere are many fruits that were found on the recently discovered planet Goocrux. There are neoskizzles that grow there, which are purple and taste like candy. There are also loheckles, which are a grayish blue fruit and are very tart, a little bit like a lemon. Pounits are a bright green color and are more savory than sweet. There are also plenty of loopnovas which are a neon pink flavor and taste like cotton candy. Finally, there are fruits called glowls, which have a very sour and bitter taste which is acidic and caustic, and a pale orange tinge to them.\n\n| Fruit | Color | Flavor |",
            "max_length": 100,
            "number_of_results": 4,
            "temperature": 1,
        },
        "tagline": "Create tables from long form text",
        "description": "Create tables from long form text by specifying a structure and supplying some examples.",
        "icon": "Table",
        "results": [
            {
                "generated_text": "A table summarizing the fruits from Goocrux:\n\nThere are many fruits that were found on the recently discovered planet Goocrux. There are neoskizzles that grow there, which are purple and taste like candy. There are also loheckles, which are a grayish blue fruit and are very tart, a little bit like a lemon. Pounits are a bright green color and are more savory than sweet. There are also plenty of loopnovas which are a neon pink flavor and taste like cotton candy. Finally, there are fruits called glowls, which have a very sour and bitter taste which is acidic and caustic, and a pale orange tinge to them.\n\n| Fruit | Color | Flavor | Description\r\nLoopnova   -  Pink     Cotton Candy   Sweet\r\nPounit      -    Green    Savoury     Green fruit\r\nNeoskizzle - Purple    Cute Sweet\r\nLoohecko  - Grey Blue   Tart Orange-like loohecko with an extra citrusy bite Loookool  - Yellow Pale yellow fruit Neokulloo - White Cream white cheese flavour Loopluke - Red Red grapefruit-flavoured lollipop Glowluf - Acid",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "A table summarizing the fruits from Goocrux:\n\nThere are many fruits that were found on the recently discovered planet Goocrux. There are neoskizzles that grow there, which are purple and taste like candy. There are also loheckles, which are a grayish blue fruit and are very tart, a little bit like a lemon. Pounits are a bright green color and are more savory than sweet. There are also plenty of loopnovas which are a neon pink flavor and taste like cotton candy. Finally, there are fruits called glowls, which have a very sour and bitter taste which is acidic and caustic, and a pale orange tinge to them.\n\n| Fruit | Color | Flavor | Description | Cargo size (in cubic meters) | Name    Nezskizzle   Purple     Candy-like      4.5  Neoskizzle Loheckle Grayish Blue        5 Loopnova  Pink       Cotton candy 3.3 Pounit Green         Sweet           9 Glowl Orange-Bitter      Acidic          1.4 Summarize this information in an table: A simple summary describing all these different fruits is: The latest data set sent by space station Phobos-Gorilla",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "A table summarizing the fruits from Goocrux:\n\nThere are many fruits that were found on the recently discovered planet Goocrux. There are neoskizzles that grow there, which are purple and taste like candy. There are also loheckles, which are a grayish blue fruit and are very tart, a little bit like a lemon. Pounits are a bright green color and are more savory than sweet. There are also plenty of loopnovas which are a neon pink flavor and taste like cotton candy. Finally, there are fruits called glowls, which have a very sour and bitter taste which is acidic and caustic, and a pale orange tinge to them.\n\n| Fruit | Color | Flavor | Description \n\nNeoskizzle  | Purple | Sweetest |\n|    loheckle |  Grayish Blue| Tarts  most |\n|     pounit | Bright Green | Sourer,but sweeter|\n|     loveknot|   Neon Pink|  Like Cotton Candy|\n|   Glowl   | Very sour Bitterly -Acidic,pale Orange # Write your code here!\n\n\n # complete\n\n\n\ndef calculateFactors(factors) :\n    for factor in factors :\n       ",
                "stop_reason": "max_length",
            },
            {
                "generated_text": 'A table summarizing the fruits from Goocrux:\n\nThere are many fruits that were found on the recently discovered planet Goocrux. There are neoskizzles that grow there, which are purple and taste like candy. There are also loheckles, which are a grayish blue fruit and are very tart, a little bit like a lemon. Pounits are a bright green color and are more savory than sweet. There are also plenty of loopnovas which are a neon pink flavor and taste like cotton candy. Finally, there are fruits called glowls, which have a very sour and bitter taste which is acidic and caustic, and a pale orange tinge to them.\n\n| Fruit | Color | Flavor | Description\n\n\nNeoskizzle (neon pink)  Neon pink and extremely sour\nLoheckle  Grayish-blue   Sour Loheckle is the closest match for the description "very sour" in the list below.\n\nLoopnova  (pink)  Neon pink  Sweet Loopnova matches best with "Sweet" from above.\n\nGlowl   (orange-brown) Bitter  Very sour Orange-brownish flavor similar to "caustic". The last listed is',
                "stop_reason": "max_length",
            },
        ],
    },
    "default-classification": {
        "id": "default-classification",
        "title": "Classification",
        "tags": ["Classification"],
        "generate_params": {
            "text": "The following is a list of companies and the categories they fall into:\n\nApple, Facebook, Fedex\n\nApple\nCategory:",
            "number_of_results": 4,
            "temperature": 1,
        },
        "description": "Classify items into categories via example.",
        "icon": "Tag",
        "results": [
            {
                "generated_text": "The following is a list of companies and the categories they fall into:\n\nApple, Facebook, Fedex\n\nApple\nCategory: Company Apple Inc. develops, manufactures, and markets consumer electronics, software applications, computer hardware, network infrastructure products,  content delivery networking solutions, mobile communications devices, and services that are widely used in media consumption platforms such as personal computers Macintosh laptops PCs Windows tablets smartphones and other handheld computing and tablet systems Desktop Personal Computer (DPC) Manufacturer Company Apple iPhone Software Development Language Worldwide Retail Distributor Company Apple Mac Application Engineer Scientist Company Apple iPad Scientist Company Apple Mail",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "The following is a list of companies and the categories they fall into:\n\nApple, Facebook, Fedex\n\nApple\nCategory: Company Description Apple Inc. is an American multinational technology company based in Cupertino California which develops products ranging from desktop computer systems to mobile devices such as iPhone smartphones and tablets, including iTunes Music Store software, Mac OS X operating system software, iOS System software and iWork productivity tools.\n\nFacebook\nCategory : Company Description The social network site owned by Mark Zuckerberg is known for developing technologies that allow users worldwide to share photos videos messages with other friends on their platforms or websites.\nFedEx Corporation Company Description Fed",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "The following is a list of companies and the categories they fall into:\n\nApple, Facebook, Fedex\n\nApple\nCategory: Company Apple's headquarters are in California. Science and technology company.\n\nGoogle, Amazon Businesses providing information services. \nMicrosoft Business software provider. Google Inc. (Nasdaq: GOOG) founded by Sergey Brin and Larry Page on March 25, 1998 (originally as BackRub) is a search engine that offers several products including e-mail and web browsers. Science and technology company. Twitter Science and technology company. LinkedIn Science and technology company. Yahoo Science and technology company. Facebook Science and technology company. Twitter",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "The following is a list of companies and the categories they fall into:\n\nApple, Facebook, Fedex\n\nApple\nCategory: Company (disambiguation) Facebook Facebook - Social Networking Site Yahoo - Internet Service Google - Search Engine Amazon.com Business (disambiguation)  Dell - Technology Microsoft Corporation Science & technology (disambiguation) IBM Science & technology (disambiguation)\n\nFedEx Corporate transport business company category (disambiguation) Science & technology (disambiguation) Business finance (disambiguation) Business tech Business travel Tech service Tech software Scientist & engineer Science & technology",
                "stop_reason": "max_length",
            },
        ],
    },
    "default-python-to-natural-language": {
        "id": "default-python-to-natural-language",
        "title": "Python to natural language",
        "tags": ["Code", "Translation"],
        "generate_params": {
            "text": '# Python 3 \ndef remove_common_prefix(x, prefix, ws_prefix): \n    x["completion"] = x["completion"].str[len(prefix) :] \n    if ws_prefix: \n        # keep the single whitespace as prefix \n        x["completion"] = " " + x["completion"] \nreturn x \n\n# Explanation of what the code does\n\n#',
            "max_length": 64,
            "number_of_results": 4,
            "temperature": 1,
            "stop_sequences": [],
        },
        "description": "Explain a piece of Python code in human understandable language.",
        "icon": "Hashtag",
        "results": [
            {
                "generated_text": '# Python 3 \ndef remove_common_prefix(x, prefix, ws_prefix): \n    x["completion"] = x["completion"].str[len(prefix) :] \n    if ws_prefix: \n        # keep the single whitespace as prefix \n        x["completion"] = " " + x["completion"] \nreturn x \n\n# Explanation of what the code does\n\n### Write Your Code Here ###\n## Read The Input Below ##\n# name is a list with different input items to guess about. e.g. [\'cat\',\n#\'man\'].\n\nnames = [{\'name\':name,\'color\': color} for name in input().split()] \n\ncommon_names=[]   ',
                "stop_reason": "max_length",
            },
            {
                "generated_text": '# Python 3 \ndef remove_common_prefix(x, prefix, ws_prefix): \n    x["completion"] = x["completion"].str[len(prefix) :] \n    if ws_prefix: \n        # keep the single whitespace as prefix \n        x["completion"] = " " + x["completion"] \nreturn x \n\n# Explanation of what the code does\n\n# this is for line wrapping\nif ("line" in self.args and len(self.args[0])!= 1):\n    return False\n words_and_line = [e[1][1:] for e in list(enumerate(strip_ansi_keys)) if (not e[0] == \'line\' or (("tabs" not',
                "stop_reason": "max_length",
            },
            {
                "generated_text": '# Python 3 \ndef remove_common_prefix(x, prefix, ws_prefix): \n    x["completion"] = x["completion"].str[len(prefix) :] \n    if ws_prefix: \n        # keep the single whitespace as prefix \n        x["completion"] = " " + x["completion"] \nreturn x \n\n# Explanation of what the code does\n\n# Note that these two lines are identical to before (but without wsPrefix), which is why I comment them out below. Here they go uncommented so you can see how I made the changes in red above this line... # def _remove_ws_prefixes_from_xref_strings_in_predecessor_sol',
                "stop_reason": "max_length",
            },
            {
                "generated_text": '# Python 3 \ndef remove_common_prefix(x, prefix, ws_prefix): \n    x["completion"] = x["completion"].str[len(prefix) :] \n    if ws_prefix: \n        # keep the single whitespace as prefix \n        x["completion"] = " " + x["completion"] \nreturn x \n\n# Explanation of what the code does\n\n#     If you have a space in your name like "Steven" then it will be interpreted as starting\n#         with two whitespaces instead of one so when looking for "Steve    Smith" we need to start\n#           finding at four chars from now on (four spaces). This is why we use len',
                "stop_reason": "max_length",
            },
        ],
    },
    "default-movie-to-emoji": {
        "id": "default-movie-to-emoji",
        "title": "Movie to Emoji",
        "tags": ["Transformation", "Generation"],
        "generate_params": {
            "text": "Convert movie titles into emoji.\n\nBack to the Future: \ud83d\udc68\ud83d\udc74\ud83d\ude97\ud83d\udd52 \nBatman: \ud83e\udd35\ud83e\udd87 \nTransformers: \ud83d\ude97\ud83e\udd16 \nStar Wars:",
            "max_length": 60,
            "number_of_results": 4,
            "temperature": 0.8,
            "stop_sequences": ["\n"],
        },
        "description": "Convert movie titles into emoji.",
        "icon": "EmojiHappy",
        "results": [
            {
                "generated_text": "Convert movie titles into emoji.\n\nBack to the Future: 👨👴🚗🕒 \nBatman: 🤵🦇 \nTransformers: 🚗🤖 \nStar Wars: ⚡️⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯ Star Trek: ☆☬☞★☮☼☽☾☿☰ ☃☀☻☹",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Convert movie titles into emoji.\n\nBack to the Future: 👨👴🚗🕒 \nBatman: 🤵🦇 \nTransformers: 🚗🤖 \nStar Wars: 😬🐥",
                "stop_reason": "\n",
            },
            {
                "generated_text": "Convert movie titles into emoji.\n\nBack to the Future: 👨👴🚗🕒 \nBatman: 🤵🦇 \nTransformers: 🚗🤖 \nStar Wars: 🔥🔥🔥🔥💫🌟",
                "stop_reason": "\n",
            },
            {
                "generated_text": "Convert movie titles into emoji.\n\nBack to the Future: 👨👴🚗🕒 \nBatman: 🤵🦇 \nTransformers: 🚗🤖 \nStar Wars: 🥰💣☄️ 🧀🐬😃😊",
                "stop_reason": "\n",
            },
        ],
    },
    "default-time-complexity": {
        "id": "default-time-complexity",
        "title": "Calculate Time Complexity",
        "tags": ["Code", "Transformation"],
        "generate_params": {
            "text": 'def foo(n, k):\naccum = 0\nfor i in range(n):\n    for l in range(k):\n        accum += i\nreturn accum\n"""\nThe time complexity of this function is',
            "max_length": 64,
            "number_of_results": 4,
            "temperature": 1,
            "stop_sequences": ["\n"],
        },
        "description": "Find the time complexity of a function.",
        "icon": "IoTimeSharp",
        "results": [
            {
                "generated_text": 'def foo(n, k):\naccum = 0\nfor i in range(n):\n    for l in range(k):\n        accum += i\nreturn accum\n"""\nThe time complexity of this function is O (nk)',
                "stop_reason": "\n",
            },
            {
                "generated_text": 'def foo(n, k):\naccum = 0\nfor i in range(n):\n    for l in range(k):\n        accum += i\nreturn accum\n"""\nThe time complexity of this function is O(n2 * k2)',
                "stop_reason": "\n",
            },
            {
                "generated_text": 'def foo(n, k):\naccum = 0\nfor i in range(n):\n    for l in range(k):\n        accum += i\nreturn accum\n"""\nThe time complexity of this function is O(n*n*logk)',
                "stop_reason": "\n",
            },
            {
                "generated_text": 'def foo(n, k):\naccum = 0\nfor i in range(n):\n    for l in range(k):\n        accum += i\nreturn accum\n"""\nThe time complexity of this function is O((nk))',
                "stop_reason": "\n",
            },
        ],
    },
    "default-translate-code": {
        "id": "default-translate-code",
        "title": "Translate programming languages",
        "tags": ["Code", "Translation"],
        "generate_params": {
            "text": "##### Translate this function  from Python into Haskell\n### Python\n    \n    def predict_proba(X: Iterable[str]):\n        return np.array([predict_one_probas(tweet) for tweet in X])\n    \n### Haskell",
            "max_length": 54,
            "number_of_results": 4,
            "temperature": 1,
            "stop_sequences": ["###"],
        },
        "tagline": "Translate from one programming language to another",
        "description": "To translate from one programming language to another we can use the comments to specify the source and target languages.",
        "icon": "Translate",
        "results": [
            {
                "generated_text": "##### Translate this function  from Python into Haskell\n### Python\n    \n    def predict_proba(X: Iterable[str]):\n        return np.array([predict_one_probas(tweet) for tweet in X])\n    \n### Haskell\n def predictions_from_tweets(\n    data: TweetTable\n) -> (Seq[StrPrediction], Seq[TweetPredictedWithTags]\n) {\n  seq = data.words\n  tag_id = Map(\n      lambda x : SequenceIndexedTypeID(\n          TypeString",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "##### Translate this function  from Python into Haskell\n### Python\n    \n    def predict_proba(X: Iterable[str]):\n        return np.array([predict_one_probas(tweet) for tweet in X])\n    \n### Haskell\n    import Data.IORef as Ref\n\ndef predict_proba(W: List[WRef<'String> > ) :\n    refs = to_reflist ( W )\n    probas_refs = map_to_list ( get_predictions_from_w_ref, Reflists.",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "##### Translate this function  from Python into Haskell\n### Python\n    \n    def predict_proba(X: Iterable[str]):\n        return np.array([predict_one_probas(tweet) for tweet in X])\n    \n### Haskell\n    Predictor p = predict_proba(X)    \n",
                "stop_reason": "###",
            },
            {
                "generated_text": "##### Translate this function  from Python into Haskell\n### Python\n    \n    def predict_proba(X: Iterable[str]):\n        return np.array([predict_one_probas(tweet) for tweet in X])\n    \n### Haskell import math\n\ndef one_prediction_per_user(\n    user: str,\n    num_queries_for_predictions: Int = 50000,  # about a billion tweets\n    kNN_minimizer_params : (Double, Double), ()\n    model : Model=KNeighborsRidge",
                "stop_reason": "max_length",
            },
        ],
    },
    "default-adv-tweet-classifier": {
        "id": "default-adv-tweet-classifier",
        "title": "Advanced tweet classifier",
        "tags": ["Classification"],
        "generate_params": {
            "text": 'Classify the sentiment in these tweets:\n\n1. "I can\'t stand homework"\n2. "This sucks. I\'m bored "\n3. "I can\'t wait for Halloween!!!"\n4. "My cat is adorable ❤️❤️"\n5. "I hate chocolate"\n\nTweet sentiment ratings:',
            "max_length": 60,
            "number_of_results": 4,
            "temperature": 1,
        },
        "tagline": "Advanced sentiment detection for a piece of text.",
        "description": "This is an advanced prompt for detecting sentiment. It allows you to provide it with a list of status updates and then provide a sentiment for each one.",
        "icon": "Hashtag",
        "results": [
            {
                "generated_text": 'Classify the sentiment in these tweets:\n\n1. "I can\'t stand homework"\n2. "This sucks. I\'m bored 😠"\n3. "I can\'t wait for Halloween!!!"\n4. "My cat is adorable ❤️❤️"\n5. "I hate chocolate"\n\nTweet sentiment ratings: positive negative negative negative Negative I love home works! negative negative Positive 1 5 negative negative Negative My mom has me do a lot of work, but i don\'t enjoy it so much. positive negative negative Negative The only good thing about this assignment is: negative Negative Negative Negative Negative Negative negative Negative positive Negative Negative Negative Negative',
                "stop_reason": "max_length",
            },
            {
                "generated_text": 'Classify the sentiment in these tweets:\n\n1. "I can\'t stand homework"\n2. "This sucks. I\'m bored 😠"\n3. "I can\'t wait for Halloween!!!"\n4. "My cat is adorable ❤️❤️"\n5. "I hate chocolate"\n\nTweet sentiment ratings: negative negative negative positive positive positive positive negative negative positive negative negative negative negative negative negative negative negative negative positive negative positive positive negative negative positive positive negative negative negative positive negative negative negative positive positive positive negative negative negative positive negative negative negative negative positive negative negative positive positive negative negative negative positive negative negative negative negative negative negative negative',
                "stop_reason": "max_length",
            },
            {
                "generated_text": 'Classify the sentiment in these tweets:\n\n1. "I can\'t stand homework"\n2. "This sucks. I\'m bored 😠"\n3. "I can\'t wait for Halloween!!!"\n4. "My cat is adorable ❤️❤️"\n5. "I hate chocolate"\n\nTweet sentiment ratings: negative Negative 2 positive Positive 1 negative Positive 3 negative Negative 4 negative Positive 2 positive Negative 5 negative Positive 0 positive Negative 8 negative Negative 10 negative Negative 15 positive Negative 6 negative Negative 14 positive Negative 11 negative Positive 7 negative Negative 16 positive Positive 12 negative Negative 13 positive Negative 17 positive Negative 18 positive Negative 19 negative',
                "stop_reason": "max_length",
            },
            {
                "generated_text": 'Classify the sentiment in these tweets:\n\n1. "I can\'t stand homework"\n2. "This sucks. I\'m bored 😠"\n3. "I can\'t wait for Halloween!!!"\n4. "My cat is adorable ❤️❤️"\n5. "I hate chocolate"\n\nTweet sentiment ratings: negative Negative\r\nI don\'t like school positive Positive    5 positive    2 negative    1 Negative Negative Tweet negative Positive Positive Negative Positive Negative Negative Positive Negative Positive Negative Positive Negative Positive Negative Negative Negative Negative Positive Negative Positive Negative Negative Negative Negative Positive Negative Positive Negative Negative Negative Negative Negative Negative Negative Negative Negative Negative Negative Negative',
                "stop_reason": "max_length",
            },
        ],
    },
    "default-explain-code": {
        "id": "default-explain-code",
        "title": "Explain code",
        "tags": ["Code", "Translation"],
        "generate_params": {
            "text": 'class Log:\n    def __init__(self, path):\n        dirname = os.path.dirname(path)\n        os.makedirs(dirname, exist_ok=True)\n        f = open(path, "a+")\n\n        # Check that the file is newline-terminated\n        size = os.path.getsize(path)\n        if size > 0:\n            f.seek(size - 1)\n            end = f.read(1)\n            if end != "\\n":\n                f.write("\\n")\n        self.f = f\n        self.path = path\n\n    def log(self, event):\n        event["_event_id"] = str(uuid.uuid4())\n        json.dump(event, self.f)\n        self.f.write("\\n")\n\n    def state(self):\n        state = {"complete": set(), "last": None}\n        for line in open(self.path):\n            event = json.loads(line)\n            if event["type"] == "submit" and event["success"]:\n                state["complete"].add(event["id"])\n                state["last"] = event\n        return state\n\n"""\nHere\'s what the above class is doing:\n1.',
            "max_length": 64,
            "number_of_results": 4,
            "temperature": 1,
            "stop_sequences": ['"""'],
        },
        "description": "Explain a complicated piece of code.",
        "icon": "Hashtag",
        "results": [
            {
                "generated_text": 'class Log:\n    def __init__(self, path):\n        dirname = os.path.dirname(path)\n        os.makedirs(dirname, exist_ok=True)\n        f = open(path, "a+")\n\n        # Check that the file is newline-terminated\n        size = os.path.getsize(path)\n        if size > 0:\n            f.seek(size - 1)\n            end = f.read(1)\n            if end != "\\n":\n                f.write("\\n")\n        self.f = f\n        self.path = path\n\n    def log(self, event):\n        event["_event_id"] = str(uuid.uuid4())\n        json.dump(event, self.f)\n        self.f.write("\\n")\n\n    def state(self):\n        state = {"complete": set(), "last": None}\n        for line in open(self.path):\n            event = json.loads(line)\n            if event["type"] == "submit" and event["success"]:\n                state["complete"].add(event["id"])\n                state["last"] = event\n        return state\n\n"""\nHere\'s what the above class is doing:\n1.  Creating a new logger object from its path.\n2.    Setting up the logger instance to write events to disk.\n3.   Using the logger to dump an initial (empty)\nlist of events to be stored on disk.\n4    Calling state() after every action completes so we can display progress.\n    ',
                "stop_reason": '"""',
            },
            {
                "generated_text": 'class Log:\n    def __init__(self, path):\n        dirname = os.path.dirname(path)\n        os.makedirs(dirname, exist_ok=True)\n        f = open(path, "a+")\n\n        # Check that the file is newline-terminated\n        size = os.path.getsize(path)\n        if size > 0:\n            f.seek(size - 1)\n            end = f.read(1)\n            if end != "\\n":\n                f.write("\\n")\n        self.f = f\n        self.path = path\n\n    def log(self, event):\n        event["_event_id"] = str(uuid.uuid4())\n        json.dump(event, self.f)\n        self.f.write("\\n")\n\n    def state(self):\n        state = {"complete": set(), "last": None}\n        for line in open(self.path):\n            event = json.loads(line)\n            if event["type"] == "submit" and event["success"]:\n                state["complete"].add(event["id"])\n                state["last"] = event\n        return state\n\n"""\nHere\'s what the above class is doing:\n1.  Initialize a new "log" object with a given directory (a.csv or XML format)\n2.  Start logging events to this new object\n3.  Look at how many successes have been logged so far since starting\n',
                "stop_reason": '"""',
            },
            {
                "generated_text": 'class Log:\n    def __init__(self, path):\n        dirname = os.path.dirname(path)\n        os.makedirs(dirname, exist_ok=True)\n        f = open(path, "a+")\n\n        # Check that the file is newline-terminated\n        size = os.path.getsize(path)\n        if size > 0:\n            f.seek(size - 1)\n            end = f.read(1)\n            if end != "\\n":\n                f.write("\\n")\n        self.f = f\n        self.path = path\n\n    def log(self, event):\n        event["_event_id"] = str(uuid.uuid4())\n        json.dump(event, self.f)\n        self.f.write("\\n")\n\n    def state(self):\n        state = {"complete": set(), "last": None}\n        for line in open(self.path):\n            event = json.loads(line)\n            if event["type"] == "submit" and event["success"]:\n                state["complete"].add(event["id"])\n                state["last"] = event\n        return state\n\n"""\nHere\'s what the above class is doing:\n1.) Create a new file on disk named /foo/bar.\n2.) Make sure everything was written properly (newlines, etc).\n3.) Call our parent method.\n def _log():\n    ',
                "stop_reason": '"""',
            },
            {
                "generated_text": 'class Log:\n    def __init__(self, path):\n        dirname = os.path.dirname(path)\n        os.makedirs(dirname, exist_ok=True)\n        f = open(path, "a+")\n\n        # Check that the file is newline-terminated\n        size = os.path.getsize(path)\n        if size > 0:\n            f.seek(size - 1)\n            end = f.read(1)\n            if end != "\\n":\n                f.write("\\n")\n        self.f = f\n        self.path = path\n\n    def log(self, event):\n        event["_event_id"] = str(uuid.uuid4())\n        json.dump(event, self.f)\n        self.f.write("\\n")\n\n    def state(self):\n        state = {"complete": set(), "last": None}\n        for line in open(self.path):\n            event = json.loads(line)\n            if event["type"] == "submit" and event["success"]:\n                state["complete"].add(event["id"])\n                state["last"] = event\n        return state\n\n"""\nHere\'s what the above class is doing:\n1.) Creating an object with a directory called "log".\n2.) Opening a new file (with append mode). And then closing it.\n3.) Assigning events to this object.\nThe events are being sent out from another service, which uses XMLRPC.\n    The format of each message is:\n    {\n        "type":"Submit",\n        "s',
                "stop_reason": "max_length",
            },
        ],
    },
    "default-keywords": {
        "id": "default-keywords",
        "title": "Keywords",
        "tags": ["Classification", "Transformation"],
        "generate_params": {
            "text": "Extract keywords from this text:\n\nBlack-on-black ware is a 20th- and 21st-century pottery tradition developed by the Puebloan Native American ceramic artists in Northern New Mexico. Traditional reduction-fired blackware has been made for centuries by pueblo artists. Black-on-black ware of the past century is produced with a smooth surface, with the designs applied through selective burnishing or the application of refractory slip. Another style involves carving or incising designs and selectively polishing the raised areas. For generations several families from Kha'po Owingeh and P'ohwhóge Owingeh pueblos have been making black-on-black ware with the techniques passed down from matriarch potters. Artists from other pueblos have also produced black-on-black ware. Several contemporary artists have created works honoring the pottery of their ancestors.",
            "max_length": 60,
            "number_of_results": 4,
            "temperature": 0.3,
        },
        "tagline": "Extract keywords from a block of text.",
        "description": "Extract keywords from a block of text. At a lower temperature it picks keywords from the text. At a higher temperature it will generate related keywords which can be helpful for creating search indexes.",
        "icon": "Key",
        "results": [
            {
                "generated_text": "Extract keywords from this text:\n\nBlack-on-black ware is a 20th- and 21st-century pottery tradition developed by the Puebloan Native American ceramic artists in Northern New Mexico. Traditional reduction-fired blackware has been made for centuries by pueblo artists. Black-on-black ware of the past century is produced with a smooth surface, with the designs applied through selective burnishing or the application of refractory slip. Another style involves carving or incising designs and selectively polishing the raised areas. For generations several families from Kha'po Owingeh and P'ohwhóge Owingeh pueblos have been making black-on-black ware with the techniques passed down from matriarch potters. Artists from other pueblos have also produced black-on-black ware. Several contemporary artists have created works honoring the pottery of their ancestors. Black-on-black ware traditions are popular among collectors. Black-on-black ware traditions are popular among collectors. Black-on-black ware is a type of pottery that was traditionally made by the people who lived on the northern edge of the Great Basin Desert. Black-on-black ware is a",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Extract keywords from this text:\n\nBlack-on-black ware is a 20th- and 21st-century pottery tradition developed by the Puebloan Native American ceramic artists in Northern New Mexico. Traditional reduction-fired blackware has been made for centuries by pueblo artists. Black-on-black ware of the past century is produced with a smooth surface, with the designs applied through selective burnishing or the application of refractory slip. Another style involves carving or incising designs and selectively polishing the raised areas. For generations several families from Kha'po Owingeh and P'ohwhóge Owingeh pueblos have been making black-on-black ware with the techniques passed down from matriarch potters. Artists from other pueblos have also produced black-on-black ware. Several contemporary artists have created works honoring the pottery of their ancestors. Black-on-black ware traditions are part of the culture of many pueblos. Black-on-black ware is an art form that was developed in the United States during the twentieth century. Black-on-black ware is a traditional pottery technique used to create decorative pieces of ceramics using two colors of",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Extract keywords from this text:\n\nBlack-on-black ware is a 20th- and 21st-century pottery tradition developed by the Puebloan Native American ceramic artists in Northern New Mexico. Traditional reduction-fired blackware has been made for centuries by pueblo artists. Black-on-black ware of the past century is produced with a smooth surface, with the designs applied through selective burnishing or the application of refractory slip. Another style involves carving or incising designs and selectively polishing the raised areas. For generations several families from Kha'po Owingeh and P'ohwhóge Owingeh pueblos have been making black-on-black ware with the techniques passed down from matriarch potters. Artists from other pueblos have also produced black-on-black ware. Several contemporary artists have created works honoring the pottery of their ancestors. Black-on-black ware traditions are part of the history of ceramics in Northern New Mexico. Black-on-black ware traditions are part of the history of ceramics in Northern New Mexico. Black-on-black ware is a traditional pottery technique used to create decorative pieces. Black-on-",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Extract keywords from this text:\n\nBlack-on-black ware is a 20th- and 21st-century pottery tradition developed by the Puebloan Native American ceramic artists in Northern New Mexico. Traditional reduction-fired blackware has been made for centuries by pueblo artists. Black-on-black ware of the past century is produced with a smooth surface, with the designs applied through selective burnishing or the application of refractory slip. Another style involves carving or incising designs and selectively polishing the raised areas. For generations several families from Kha'po Owingeh and P'ohwhóge Owingeh pueblos have been making black-on-black ware with the techniques passed down from matriarch potters. Artists from other pueblos have also produced black-on-black ware. Several contemporary artists have created works honoring the pottery of their ancestors. Black-on-black ware artistry Black-on-black ware artistry refers to the traditional ceramics of the United States Navajo Nation's northernmost region. Black-on-black ware artistry Black-on-black ware artistry refers to the traditional ceramics of the United States Navajo Nation",
                "stop_reason": "max_length",
            },
        ],
    },
    "default-factual-answering": {
        "id": "default-factual-answering",
        "title": "Factual answering",
        "tags": ["Answers", "Generation", "Conversation", "Classification"],
        "generate_params": {
            "text": "Q: Who is Batman?\nA: Batman is a fictional comic book character.\n\nQ: What is torsalplexity?\nA: ?\n\nQ: What is Devz9?\nA: ?\n\nQ: Who is George Lucas?\nA: George Lucas is American film director and producer famous for creating Star Wars.\n\nQ: What is the capital of California?\nA: Sacramento.\n\nQ: What orbits the Earth?\nA: The Moon.\n\nQ: Who is Fred Rickerson?\nA: ?\n\nQ: What is an atom?\nA: An atom is a tiny particle that makes up everything.\n\nQ: Who is Alvan Muntz?\nA: ?\n\nQ: What is Kozar-09?\nA: ?\n\nQ: How many moons does Mars have?\nA: Two, Phobos and Deimos.\n\nQ: What's a language model?\nA:",
            "max_length": 60,
            "number_of_results": 4,
            "temperature": 1,
        },
        "icon": "QuestionMarkCircle",
        "results": [
            {
                "generated_text": "Q: Who is Batman?\nA: Batman is a fictional comic book character.\n\nQ: What is torsalplexity?\nA: ?\n\nQ: What is Devz9?\nA: ?\n\nQ: Who is George Lucas?\nA: George Lucas is American film director and producer famous for creating Star Wars.\n\nQ: What is the capital of California?\nA: Sacramento.\n\nQ: What orbits the Earth?\nA: The Moon.\n\nQ: Who is Fred Rickerson?\nA: ?\n\nQ: What is an atom?\nA: An atom is a tiny particle that makes up everything.\n\nQ: Who is Alvan Muntz?\nA: ?\n\nQ: What is Kozar-09?\nA: ?\n\nQ: How many moons does Mars have?\nA: Two, Phobos and Deimos.\n\nQ: What's a language model?\nA: Answer not in context\n\nQ. What's devils advocate answer not in context\n\nWhat is KZN-9H\nAnswer not in context\n\nThe ZZP-7 proton trap experiment at Fermilab? Answer not in context (it was shut down) Who's Batman George Lucas Answer not in context",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Q: Who is Batman?\nA: Batman is a fictional comic book character.\n\nQ: What is torsalplexity?\nA: ?\n\nQ: What is Devz9?\nA: ?\n\nQ: Who is George Lucas?\nA: George Lucas is American film director and producer famous for creating Star Wars.\n\nQ: What is the capital of California?\nA: Sacramento.\n\nQ: What orbits the Earth?\nA: The Moon.\n\nQ: Who is Fred Rickerson?\nA: ?\n\nQ: What is an atom?\nA: An atom is a tiny particle that makes up everything.\n\nQ: Who is Alvan Muntz?\nA: ?\n\nQ: What is Kozar-09?\nA: ?\n\nQ: How many moons does Mars have?\nA: Two, Phobos and Deimos.\n\nQ: What's a language model?\nA: A statistical machine translation system. Answer not in context\n\nAnswer not in context\nWhat are all these other things? None of the above choices.com Bat-man Answer not in context None of the above choices.com Devz9 Answer not in context None of the above choices.com Kozar-09 Answer",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Q: Who is Batman?\nA: Batman is a fictional comic book character.\n\nQ: What is torsalplexity?\nA: ?\n\nQ: What is Devz9?\nA: ?\n\nQ: Who is George Lucas?\nA: George Lucas is American film director and producer famous for creating Star Wars.\n\nQ: What is the capital of California?\nA: Sacramento.\n\nQ: What orbits the Earth?\nA: The Moon.\n\nQ: Who is Fred Rickerson?\nA: ?\n\nQ: What is an atom?\nA: An atom is a tiny particle that makes up everything.\n\nQ: Who is Alvan Muntz?\nA: ?\n\nQ: What is Kozar-09?\nA: ?\n\nQ: How many moons does Mars have?\nA: Two, Phobos and Deimos.\n\nQ: What's a language model?\nA:? Answer not in context\n\nThe answer not in context\nBruce Wayne is a fictional superhero appearing mainly in DC Comics. His alter ego was originally Batman's name under its own title series, until the 1960s when he was given his first mainstream identity as Bruce Wayne / Batman. In recent years he's",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Q: Who is Batman?\nA: Batman is a fictional comic book character.\n\nQ: What is torsalplexity?\nA: ?\n\nQ: What is Devz9?\nA: ?\n\nQ: Who is George Lucas?\nA: George Lucas is American film director and producer famous for creating Star Wars.\n\nQ: What is the capital of California?\nA: Sacramento.\n\nQ: What orbits the Earth?\nA: The Moon.\n\nQ: Who is Fred Rickerson?\nA: ?\n\nQ: What is an atom?\nA: An atom is a tiny particle that makes up everything.\n\nQ: Who is Alvan Muntz?\nA: ?\n\nQ: What is Kozar-09?\nA: ?\n\nQ: How many moons does Mars have?\nA: Two, Phobos and Deimos.\n\nQ: What's a language model?\nA: A system designed to automatically generate text. Answer not in context\n\nWhat was Bruce Wayne's alter ego? Batman was his superhero alter ego, who fought crime as Bat-Man. It featured both physical appearance and a number of powers granted by various forms of mental stimulation from drugs such as LSD or catech",
                "stop_reason": "max_length",
            },
        ],
    },
    "default-ad-product-description": {
        "id": "default-ad-product-description",
        "title": "Ad from product description",
        "tags": ["Generation"],
        "generate_params": {
            "text": "Write a creative ad for the following product to run on Facebook aimed at parents:\n\nProduct: Learning Room is a virtual environment to help students from kindergarten to high school excel in school.",
            "max_length": 60,
            "number_of_results": 4,
            "temperature": 0.5,
        },
        "description": "Turn a product description into ad copy.",
        "icon": "Speakerphone",
        "results": [
            {
                "generated_text": "Write a creative ad for the following product to run on Facebook aimed at parents:\n\nProduct: Learning Room is a virtual environment to help students from kindergarten to high school excel in school. It has been developed by experts and teachers who have years of experience with education. This program will not only improve your child's reading, writing, math skills but also develop their interest in learning.\n\nParents - We are happy that you care about your children's future! The price is $49 per month or one-time",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Write a creative ad for the following product to run on Facebook aimed at parents:\n\nProduct: Learning Room is a virtual environment to help students from kindergarten to high school excel in school. It allows you to set up multiple classrooms, each with different curriculum and teaching methods.\n\nParents can easily access their child's classroom through your computer or smartphone. \nAdvertisement: \nLearning Room - A Virtual Environment For Students To Excel In School\nPrice:$39.99/month  $199.00",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Write a creative ad for the following product to run on Facebook aimed at parents:\n\nProduct: Learning Room is a virtual environment to help students from kindergarten to high school excel in school. It allows them to study, play games and chat with their friends.\n\nFeatures: - Study anywhere anytime! - Play online games! - Chat with your friends!\n\nPrice: Free download now!! Get it before it's too late!!! Click here to get the link to Download Now! \nParents who have children",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Write a creative ad for the following product to run on Facebook aimed at parents:\n\nProduct: Learning Room is a virtual environment to help students from kindergarten to high school excel in school. It offers interactive activities that are designed with learning as its main focus.\n\nFeatures: - Interactive games and lessons - Fun, engaging content - Simple navigation - Easy to use - FREE!\n\nParents can easily access their child's account through our website or mobile app. \nWhat do you need? A computer or tablet!",
                "stop_reason": "max_length",
            },
        ],
    },
    "default-product-name-gen": {
        "id": "default-product-name-gen",
        "title": "Product name generator",
        "tags": ["Generation"],
        "generate_params": {
            "text": "Product description: A home milkshake maker\nSeed words: fast, healthy, compact.\nProduct names: HomeShaker, Fit Shaker, QuickShake, Shake Maker\n\nProduct description: A pair of shoes that can fit any foot size.\nSeed words: adaptable, fit, omni-fit.",
            "max_length": 60,
            "number_of_results": 4,
            "temperature": 0.8,
        },
        "description": "Create product names from examples words. Influenced by a community prompt.",
        "icon": "LightBulb",
        "results": [
            {
                "generated_text": "Product description: A home milkshake maker\nSeed words: fast, healthy, compact.\nProduct names: HomeShaker, Fit Shaker, QuickShake, Shake Maker\n\nProduct description: A pair of shoes that can fit any foot size.\nSeed words: adaptable, fit, omni-fit. Fit for all feet? Yes. No. No. No. No. No. Yes. Yes. No. Yes. No. Yes. No. No. No. Yes. No. Yes. Yes. Yes. Yes. Yes. No. No. No. No. No. Yes.",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Product description: A home milkshake maker\nSeed words: fast, healthy, compact.\nProduct names: HomeShaker, Fit Shaker, QuickShake, Shake Maker\n\nProduct description: A pair of shoes that can fit any foot size.\nSeed words: adaptable, fit, omni-fit. Shoe brand name (optional): AdaptaFIT® Omni-Fit shoes or Foot Locker Omni-Fit sneakers and other brands of the same type. The shoe should be sold in a variety of sizes to make them suitable for different sized feet. No product name provided.",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Product description: A home milkshake maker\nSeed words: fast, healthy, compact.\nProduct names: HomeShaker, Fit Shaker, QuickShake, Shake Maker\n\nProduct description: A pair of shoes that can fit any foot size.\nSeed words: adaptable, fit, omni-fit. Product name: Omni-Fit Footwear - All sizes for women and men. Flexible sole design. Fast delivery with tracking number. No shipping to Canada or the United States. Product description : Furniture for a small apartment or studio apartment. Seed words: space, efficient use of space. Product",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Product description: A home milkshake maker\nSeed words: fast, healthy, compact.\nProduct names: HomeShaker, Fit Shaker, QuickShake, Shake Maker\n\nProduct description: A pair of shoes that can fit any foot size.\nSeed words: adaptable, fit, omni-fit. Shoe company name Nike.com Omni-FIT Footwear Company.com. Adaptive design shoe. Adaptive shoes, flexible soles for all sizes and types of feet. Omnifit shoes are available on the Nike website or in stores across the world. Yes. Adaptive design shoe.",
                "stop_reason": "max_length",
            },
        ],
    },
    "default-tldr-summary": {
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
        "icon": "Filter",
        "results": [
            {
                "generated_text": "A neutron star is the collapsed core of a massive supergiant star, which had a total mass of between 10 and 25 solar masses, possibly more if the star was especially metal-rich.[1] Neutron stars are the smallest and densest stellar objects, excluding black holes and hypothetical white holes, quark stars, and strange stars.[2] Neutron stars have a radius on the order of 10 kilometres (6.2 mi) and a mass of about 1.4 solar masses.[3] They result from the supernova explosion of a massive star, combined with gravitational collapse, that compresses the core past white dwarf star density to that of atomic nuclei.\n\nTl;dr A neutron star consists of: Answer not in context\n\nThe radius on the order of 10 kilometres (6.2 mi), but it may be as large or smaller than this depending upon how much matter remains following formation. The inner crust will also vary in thickness because of variations in temperature.\nIt results when the",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "A neutron star is the collapsed core of a massive supergiant star, which had a total mass of between 10 and 25 solar masses, possibly more if the star was especially metal-rich.[1] Neutron stars are the smallest and densest stellar objects, excluding black holes and hypothetical white holes, quark stars, and strange stars.[2] Neutron stars have a radius on the order of 10 kilometres (6.2 mi) and a mass of about 1.4 solar masses.[3] They result from the supernova explosion of a massive star, combined with gravitational collapse, that compresses the core past white dwarf star density to that of atomic nuclei.\n\nTl;dr A neutron star is formed by two processes — first through gravitational collapse as previously described and then explosive nuclear fusion when matter exceeds 20 times nuclear saturation density, but not 100\xa0times it. It takes up most of its energy via fissioning in short bursts of high-powered nuclear collisions during which neutrons",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "A neutron star is the collapsed core of a massive supergiant star, which had a total mass of between 10 and 25 solar masses, possibly more if the star was especially metal-rich.[1] Neutron stars are the smallest and densest stellar objects, excluding black holes and hypothetical white holes, quark stars, and strange stars.[2] Neutron stars have a radius on the order of 10 kilometres (6.2 mi) and a mass of about 1.4 solar masses.[3] They result from the supernova explosion of a massive star, combined with gravitational collapse, that compresses the core past white dwarf star density to that of atomic nuclei.\n\nTl;dr A neutron star is an extremely dense matter ball made up primarily by neutrons, although other particles also can be present. It results when a massive star collapses due to nuclear fusion at its center after it has become too large for gravity alone to hold together, causing tremendous pressures in such concentrations as the surface pressure",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "A neutron star is the collapsed core of a massive supergiant star, which had a total mass of between 10 and 25 solar masses, possibly more if the star was especially metal-rich.[1] Neutron stars are the smallest and densest stellar objects, excluding black holes and hypothetical white holes, quark stars, and strange stars.[2] Neutron stars have a radius on the order of 10 kilometres (6.2 mi) and a mass of about 1.4 solar masses.[3] They result from the supernova explosion of a massive star, combined with gravitational collapse, that compresses the core past white dwarf star density to that of atomic nuclei.\n\nTl;dr A compact object can be either made out of quarks or neutrons called a neutron star. It has all its atoms bound together in an incredibly dense nucleus where nuclear forces dominate gravity. The typical size for most types of these bodies is around 3 light years across. (1 light year = 100 million km). These",
                "stop_reason": "max_length",
            },
        ],
    },
    "default-fix-python-bugs": {
        "id": "default-fix-python-bugs",
        "title": "Python bug fixer",
        "tags": ["Code", "Generation"],
        "generate_params": {
            "text": '##### Fix bugs in the below function\n \n### Buggy Python\nimport Random\na = random.randint(1,12)\nb = random.randint(1,12)\nfor i in range(10):\n    question = "What is "+a+" x "+b+"? "\n    answer = input(question)\n    if answer = a*b\n        print (Well done!)\n    else:\n        print("No.")\n    \n### Fixed Python',
            "max_length": 182,
            "number_of_results": 4,
            "temperature": 1,
            "stop_sequences": ["###"],
        },
        "tagline": "Find and fix bugs in source code.",
        "description": "There's a number of ways of structuring the prompt for checking for bugs. Here we add a comment suggesting that source code is buggy, and then ask codex to generate a fixed code.",
        "icon": "IoBug",
        "results": [
            {
                "generated_text": '##### Fix bugs in the below function\n \n### Buggy Python\nimport Random\na = random.randint(1,12)\nb = random.randint(1,12)\nfor i in range(10):\n    question = "What is "+a+" x "+b+"? "\n    answer = input(question)\n    if answer = a*b\n        print (Well done!)\n    else:\n        print("No.")\n    \n### Fixed Python version from math import *\n\na=random.randint(0,6)\nb=random.randint(0,3)\n\nprint \'Number of squares that can be filled with \'+str((a+b-1))+\' is:\'\nans1=int(ceil(((a+1)*b)))//2\n    if ans1!=0:        for x in xrange(ans1-1,len(x)):\n        ans2=ceil(((x-1+abs(a-b))/2))\n        if ((x+ans2-1)!=0 and abs(x-b)==1-ans2-1 or ((x+1-ans2-2)!= 0)and abs(x-a-1)!=-1 ) :\n            break\n                            if ans1%2:         ans1+=2                                     print \'Number:\' + str(ans1)\n \n\ndef rand_answer():\n   return int(input()) # Question 2\n\n\n\n"""Question 3\n  """\nn',
                "stop_reason": "max_length",
            },
            {
                "generated_text": '##### Fix bugs in the below function\n \n### Buggy Python\nimport Random\na = random.randint(1,12)\nb = random.randint(1,12)\nfor i in range(10):\n    question = "What is "+a+" x "+b+"? "\n    answer = input(question)\n    if answer = a*b\n        print (Well done!)\n    else:\n        print("No.")\n    \n### Fixed Python3\nfrom __future__ import division,print_function\n\ndef _randint():\n  return int((float(random().getrandbits(63)) / 8192))\n\ndef randrange(start=1,end=200005): # max 20005 -> 20 digits\n  while end >= start:\n    temp = end-start+1     end = temp//2\n    start += 1   for p in range(temp%3,0,-1):\n  \tif ((end % 2)!=0) and (((p * 3) < (2*temp))):\n      \t  break;\n  \telse:\n      \t\tstart += 1;\n    \tend-=2;\n\t\tbreak\n\treturn start + p;\n\t\nRANDINT_MAX=10**16 ; RNDMAX=10**5; RNGMAX=205;\ndef Randonumber(num_of_digits=5):\n\twhile num_of_digits > 0:\n\t\t\tdigit = str',
                "stop_reason": "max_length",
            },
            {
                "generated_text": '##### Fix bugs in the below function\n \n### Buggy Python\nimport Random\na = random.randint(1,12)\nb = random.randint(1,12)\nfor i in range(10):\n    question = "What is "+a+" x "+b+"? "\n    answer = input(question)\n    if answer = a*b\n        print (Well done!)\n    else:\n        print("No.")\n    \n### Fixed Python3\ndef ask_for_number_1_and_2():     """Ask for 2 numbers and check them.  Output whether they are equal.\n    Input will be either 0 or 1"""\n        nums = [int(n) for n in input().split()]\n    if abs(nums[0] - nums[1])!= 1:\n        return False\n    elif (not (isinstance(nums, list)) or not len(nums)):         return True    # If we get an integer instead of two strings... just assume it makes sense.\n        return None\n\nif __name__ == \'__main__\':\n    ans1 = ask_for_number_1_and_2()\n    if ans1:  # Yes its one number only.\n        print("Yes.")\n        continue\n\n    ask_for_number_1_and_2()        ask_for_number_1_and_2()        ##    while True:        ##        nums = ask_for_number_1_and_2()\n',
                "stop_reason": "max_length",
            },
            {
                "generated_text": '##### Fix bugs in the below function\n \n### Buggy Python\nimport Random\na = random.randint(1,12)\nb = random.randint(1,12)\nfor i in range(10):\n    question = "What is "+a+" x "+b+"? "\n    answer = input(question)\n    if answer = a*b\n        print (Well done!)\n    else:\n        print("No.")\n    \n### Fixed Python from math import sqrt\na=int(input())\nb=int(input())\nc=a*b;print(a+b+c%16==4 or b-c%2==0 and c-a-b+a%6==0 or c-b%2==0 and a+ab+1%d2==0or c-eb+1%d2=13or a+cb+2%d2==14or ab+d2+c%=18 or bc=d1+c2==1 or d1=dc+4d%7>0 or d1-ca+9d%3>3 )\n\'\'\'def test():\n\tn=random.randrange(0,1000)\n\tmid=n//2;k=n-mid*2\n\t\n\tans="NO ANSWER"%mid\n\n\tif mid<=k:\n\t\tans+=str((mid/2))\n\telif k<mid:\n\t\tans+=str((k-mid)**2)\n\n\treturn ans\n\ntest()\n\'\'\'\n\n\n\n\n\n\ndef find_solutions(i',
                "stop_reason": "max_length",
            },
        ],
    },
    "default-spreadsheet-gen": {
        "id": "default-spreadsheet-gen",
        "title": "Spreadsheet creator",
        "tags": ["Generation"],
        "generate_params": {
            "text": "A two-column spreadsheet of top science fiction movies and the year of release:\n\nTitle|  Year of release",
            "max_length": 60,
            "number_of_results": 4,
            "temperature": 0.5,
        },
        "description": "Create spreadsheets of various kinds of data. It's a long prompt but very versatile. Output can be copy+pasted into a text file and saved as a .csv with pipe separators.",
        "icon": "Table",
        "results": [
            {
                "generated_text": "A two-column spreadsheet of top science fiction movies and the year of release:\n\nTitle|  Year of release| Film genre | Director   1   |  2001 |  Science Fiction  | Steven Spielberg\n  2   |  2009  |  Science Fiction  | Alfonso Cuarón\n  3   |  2000 |  Science Fiction  | Stanley Kubrick 4   |  2012  |  Science Fiction  | James Cameron 5   |  2008  |  Science F",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "A two-column spreadsheet of top science fiction movies and the year of release:\n\nTitle|  Year of release | Description \nStar Wars I (1977) |  1977 |   A prequel to Star Wars. This film is a sequel to The Empire Strikes Back.\n\nStar Wars II (1980)  | 1980 |    An extended version of the original trilogy, this time with three more films in total.\n\nStar Wars",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "A two-column spreadsheet of top science fiction movies and the year of release:\n\nTitle|  Year of release| Director| Cast | Plot summary\n 1. 2001 A Space Odyssey  2001  Stanley Kubrick  3,000 astronauts aboard a space shuttle orbiting Earth in preparation for an unplanned mission to Jupiter 2.  The Day After Tomorrow 2004  Roland Emmerich Tom Hanks,  Sandra",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "A two-column spreadsheet of top science fiction movies and the year of release:\n\nTitle|  Year of release| Science Fiction Film | Top 10 (Top 100) Space 1999  2001  2012  2004  2009  2010  2011   2002 2003 2005 2006 2007 2008 2009 2000 2001 2002 2003 2004 2005 2006 2007 2008 2009 2010 2011 2012 2013 2014 2015 2016 2017 2018 2019 2020 2021 2022 2023 2024 2025 202",
                "stop_reason": "max_length",
            },
        ],
    },
    "default-js-helper": {
        "id": "default-js-helper",
        "title": "JavaScript helper chatbot",
        "tags": ["Code", "Answers", "Conversation"],
        "generate_params": {
            "text": "You: How do I combine arrays?\nJavaScript chatbot: You can use the concat() method.\nYou: How do you make an alert appear after 10 seconds?\nJavaScript chatbot",
            "max_length": 60,
            "number_of_results": 4,
            "temperature": 1,
            "stop_sequences": ["You:"],
        },
        "tagline": "Message-style bot that answers JavaScript questions",
        "description": "This is a message-style chatbot that can answer questions about using JavaScript. It uses a few examples to get the conversation started.",
        "icon": "QuestionMarkCircle",
        "results": [
            {
                "generated_text": "You: How do I combine arrays?\nJavaScript chatbot: You can use the concat() method.\nYou: How do you make an alert appear after 10 seconds?\nJavaScript chatbot: You can pass a delay of 10 seconds as a second parameter to the sleep(). This way it will show on screen in 10 seconds. You are able to see this function here (https://repl.it/@LemonyKite/sleep) and you should be fine with what is shown here",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "You: How do I combine arrays?\nJavaScript chatbot: You can use the concat() method.\nYou: How do you make an alert appear after 10 seconds?\nJavaScript chatbot: Use the function delay(). Wait for 10 secs and run your code, then it will show on screen. Please don't remove the brackets. JS Code < br />\nJavaScript chatbot: Your answer is \" [(function() { var date; document.write (new Date()); })]",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "You: How do I combine arrays?\nJavaScript chatbot: You can use the concat() method.\nYou: How do you make an alert appear after 10 seconds?\nJavaScript chatbot: Can't see it now. It's up to me what does my answer look like! 😆\nThat's all we have for this week's tip of the day! See you again next time. 🙌👋💪❤️😃✊🏾 JavaScript and Java is a",
                "stop_reason": "max_length",
            },
            {
                "generated_text": 'You: How do I combine arrays?\nJavaScript chatbot: You can use the concat() method.\nYou: How do you make an alert appear after 10 seconds?\nJavaScript chatbot: Alert ("Hello");\n\n// Show a popup\nalert ();\n\n',
                "stop_reason": "You:",
            },
        ],
    },
    "default-ml-ai-tutor": {
        "id": "default-ml-ai-tutor",
        "title": "ML/AI language model tutor",
        "tags": ["Answers", "Generation", "Conversation"],
        "generate_params": {
            "text": "ML Tutor: I am a ML/AI language model tutor\nYou: What is a language model?\nML Tutor: A language model is a statistical model that describes the probability of a word given the previous words.\nYou: What is a statistical model?",
            "max_length": 60,
            "number_of_results": 4,
            "temperature": 0.3,
            "stop_sequences": ["You:"],
        },
        "tagline": "Bot that answers questions about language models",
        "description": "This is a QA-style chatbot that answers questions about language models.",
        "icon": "QuestionMarkCircle",
        "results": [
            {
                "generated_text": "ML Tutor: I am a ML/AI language model tutor\nYou: What is a language model?\nML Tutor: A language model is a statistical model that describes the probability of a word given the previous words.\nYou: What is a statistical model? Answer not in context. You are trying to learn about machine learning, so you need to know what statistics mean and how they can be used. The answer will come later. For now let's move on with your question. A language model is a probabilistic model that describes the probability of a word given the",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "ML Tutor: I am a ML/AI language model tutor\nYou: What is a language model?\nML Tutor: A language model is a statistical model that describes the probability of a word given the previous words.\nYou: What is a statistical model? Answer not in context. You are asking about what is a language model, and how it works. So you can ask me questions like this one. The answer to your question is It is a mathematical description of something's behavior or process. For example, if someone were to say \"it was raining",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "ML Tutor: I am a ML/AI language model tutor\nYou: What is a language model?\nML Tutor: A language model is a statistical model that describes the probability of a word given the previous words.\nYou: What is a statistical model? Answer not in context. You are asking about something related to statistics and data science, but this question has no relation with it. It was just an example for you. So what does a language model do? Description of the probability of a word given the previous words. That's all! That is why it's",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "ML Tutor: I am a ML/AI language model tutor\nYou: What is a language model?\nML Tutor: A language model is a statistical model that describes the probability of a word given the previous words.\nYou: What is a statistical model? Answer not in context. You can find more information here: https://en.wikipedia.org/wiki/Statistical_model#Description_of_the_principle_of_least_squares Statistically, it means we are trying to make predictions about future events based on past observations and current state variables (e.g., temperature).",
                "stop_reason": "max_length",
            },
        ],
    },
    "default-sci-fi-book-list": {
        "id": "default-sci-fi-book-list",
        "title": "Science fiction book list maker",
        "tags": ["Generation"],
        "generate_params": {
            "text": "List 10 science fiction books:",
            "max_length": 200,
            "number_of_results": 4,
            "temperature": 0.5,
            "presencePenalty": 0.5,
            "stop_sequences": ["11."],
        },
        "tagline": "Create a list of items for a given topic.",
        "description": "This makes a list of science fiction books and stops when it reaches #10.",
        "icon": "BookOpen",
        "results": [
            {
                "generated_text": "List 10 science fiction books: The Day the Earth Stood Still, Star Wars, Doctor Who and more. Science fiction is a genre that has been around for centuries but it was in the 1960s when books like \"The Day the Earth Stood Still\" by Robert A. Heinlein became popular among readers of all ages. Here are some other classic sci-fi novels to read if you love this type of story: 1. The Day the Earth Stood Still (Robert A. Heinlein) 2. Star Wars (George Lucas) 3. Doctor Who (David Tennant) 4. Firefly 5. Battlestar Galactica 6. The Hitchhiker's Guide To The Galaxy 7. Dune 8. Orson Scott Card 9. Warhammer 40k 10. Harry Potter If you're looking for an easy way to get into sci-fi without having to think too hard about what kind of stories you'd enjoy, try reading graphic novels or comics. They come with lots of action packed pages filled with color",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "List 10 science fiction books: The Dreadful Book of the Dead, Star Wars: A New Hope, Doctor Who, 2001: A Space Odyssey, 1984, Blade Runner, Alien, and Back to the Future. Science Fiction novels are a genre that is very popular with readers. Here are some great books in this genre for you to read! 1) The Dreadful Book of the Dead by Jack Vance 2) Star Wars: A New Hope 3) Doctor Who 4) 2001: A Space Odyssey 5) 1984 6) Blade Runner 7) Alien 8) Back to the Future 9) The Hitchhiker's Guide To Galaxy Read more about sci-fi here. If you're interested in learning how to write sci fi stories or other fantasy stories check out these articles. You can find them on my blog at http://www.thehitchhikersguide.com/writing/articles/sci-fi-tips-and-tricks-how-to-write-sci-fi/. I hope you've enjoyed reading about",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "List 10 science fiction books: 1. Star Wars (1977) 2. The Empire Strikes Back 3. Return of the Jedi 4. A New Hope 5. Thor's Hammer 6. Battle for Endor 7. Revenge of the Sith 8. Firefly 9. Battlestar Galactica 10. Doctor Who Science Fiction is a genre that deals with fantasy, but also explores technology and ideas in other fields such as medicine or biology. These books are good to read if you like sci-fi. Read more: Top 100 Books Written by Women in History. See also: List of best-selling novels on Amazon.com Science-fiction short stories include dystopian societies, utopias, alternate realities, and extraterrestrial settings. They can be very interesting too! Here’s a list of some great ones. Some of these might not be considered “true” science fiction because they take place outside our solar system. For example, check out this list: Best Science-Fiction Short Stories Ever",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "List 10 science fiction books: the best of 2014 Science Fiction and Fantasy Writers of America (SFWA) has selected its top ten books for the year. The list includes a number of works by authors who have not been traditionally published, as well... New York Times lists 20 books to read before you die This year's edition features more than 200 titles from around the world,... Top 100 fantasy novels on Amazon in 2013 Amazon's annual Best Seller List is out with this year's results - including some new entries that are taking off fast.... How do scientists think about time? Scientists believe we live in an expanding universe. They also think time flows differently at different speeds throughout space-time. Time can be seen as being divided into three distinct states: past, present and future. And yet, it's difficult to explain how these things work together. Here are five ways physicist Brian Greene explains it. Click here to find out why he thinks our Universe will end up like a black hole or click here to see his theory on what",
                "stop_reason": "max_length",
            },
        ],
    },
    "default-tweet-classifier": {
        "id": "default-tweet-classifier",
        "title": "Tweet classifier",
        "tags": ["Classification"],
        "generate_params": {
            "text": 'Decide whether a Tweet\'s sentiment is positive, neutral, or negative.\n\nTweet: "I loved the new Batman movie!"\nSentiment:',
            "max_length": 60,
            "number_of_results": 4,
            "temperature": 1,
        },
        "tagline": "Basic sentiment detection for a piece of text.",
        "description": "This is a basic prompt for detecting sentiment.",
        "icon": "Hashtag",
        "results": [
            {
                "generated_text": "Decide whether a Tweet's sentiment is positive, neutral, or negative.\n\nTweet: \"I loved the new Batman movie!\"\nSentiment: Positive\n\nTwitter user liked this tweet Positive tweets are marked with a positive score between 1 and 5. Negative tweets have a negative score between −1 and −5. Neutral Twitter posts that aren't polarity-specific are scored using the following scale Positive=0 Negative=1 Negative=5 Positive=2 Positive=3 Positive=4 Positive=",
                "stop_reason": "max_length",
            },
            {
                "generated_text": 'Decide whether a Tweet\'s sentiment is positive, neutral, or negative.\n\nTweet: "I loved the new Batman movie!"\nSentiment: Positive tweeting positive tweets Positive Twitter sentiment = True positive Twitter sentiment + False positive Negative Negative Twitter sentiment = False Positive Twitter sentiment += False positive Negative Twitter sentiment -= False Positive The above equations can be used to calculate how many positive, negative and total tweets are being made. Negative tweets (the negatives of',
                "stop_reason": "max_length",
            },
            {
                "generated_text": 'Decide whether a Tweet\'s sentiment is positive, neutral, or negative.\n\nTweet: "I loved the new Batman movie!"\nSentiment: Positive\n\nTweet: "This pizza tastes like shit" Negative\r\nTweet #2: "Batman v Superman: Dawn of Justice - Positive I will be going to watch this in the cinema next week Negative The Joker was great Negative It was negative This example shows that if you don\'t specify a Twitter sentiment attribute then',
                "stop_reason": "max_length",
            },
            {
                "generated_text": 'Decide whether a Tweet\'s sentiment is positive, neutral, or negative.\n\nTweet: "I loved the new Batman movie!"\nSentiment: Positive    Positive    Negative Positive\n\nTwitter: "Great video game release today." Positive     Negative Positive      Positive   Positive       Negative No one has rated this Twitter thread yet Positive     Negative Negative    Negative Positive Positive     Negative Positive     Negative Positive  Positive   Positive Negative Negative Negative Positive Negative Positive Positive Positive',
                "stop_reason": "max_length",
            },
        ],
    },
    "default-airport-codes": {
        "id": "default-airport-codes",
        "title": "Airport code extractor",
        "tags": ["Transformation", "Generation"],
        "generate_params": {
            "text": 'Extract the airport codes from this text:\n\nText: "I want to fly from Los Angeles to Miami."\nAirport codes: LAX, MIA\n\nText: "I want to fly from Orlando to Boston"\nAirport codes:',
            "max_length": 60,
            "number_of_results": 4,
            "temperature": 1,
            "stop_sequences": ["\n"],
        },
        "tagline": "Extract airport codes from text.",
        "description": "A simple prompt for extracting airport codes from text.",
        "icon": "Tag",
        "results": [
            {
                "generated_text": 'Extract the airport codes from this text:\n\nText: "I want to fly from Los Angeles to Miami."\nAirport codes: LAX, MIA\n\nText: "I want to fly from Orlando to Boston"\nAirport codes: ORD, BST The first one is for a flight going from Los Angeles to Miami and the second goes between Orlando  and Boston. There are two airports in each city where you would fly: either LAX or LOA or even LOSA, but none of them will do any harm. I',
                "stop_reason": "max_length",
            },
            {
                "generated_text": 'Extract the airport codes from this text:\n\nText: "I want to fly from Los Angeles to Miami."\nAirport codes: LAX, MIA\n\nText: "I want to fly from Orlando to Boston"\nAirport codes: BOA, EWR BOA and EWR are both airports in Massachusetts; they have different names for their respective places of origin so you can tell them apart by looking at code numbers. You could also just look up which city the airport is located after it if it\'s convenient Airports use a three-d',
                "stop_reason": "max_length",
            },
            {
                "generated_text": 'Extract the airport codes from this text:\n\nText: "I want to fly from Los Angeles to Miami."\nAirport codes: LAX, MIA\n\nText: "I want to fly from Orlando to Boston"\nAirport codes: ORD, BOS From one of these airports I would take a flight to: BOS; but from Los Angeles: LAX; so in other words, you could only take flights originating in: LOS ANGELES FROM  LOS ANGELES or ORD TO BOSTON. Yes, no. No',
                "stop_reason": "max_length",
            },
            {
                "generated_text": 'Extract the airport codes from this text:\n\nText: "I want to fly from Los Angeles to Miami."\nAirport codes: LAX, MIA\n\nText: "I want to fly from Orlando to Boston"\nAirport codes: ORD, BOS LZR is another code I can use for Los Angeles but it\'s not a standard one.',
                "stop_reason": "\n",
            },
        ],
    },
    "default-sql-request": {
        "id": "default-sql-request",
        "title": "SQL request",
        "tags": ["Transformation", "Generation", "Translation"],
        "generate_params": {
            "text": "Create a SQL request to find all users who live in California and have over 1000 credits:",
            "max_length": 60,
            "number_of_results": 4,
            "temperature": 0.3,
        },
        "description": "Create simple SQL queries.",
        "icon": "Terminal",
        "results": [
            {
                "generated_text": "Create a SQL request to find all users who live in California and have over 1000 credits: SELECT * FROM user WHERE state = 'CA' AND credit > 1000;\n\nYou can also use the following query if you want to see only those with more than 2000 credits (or any other number): SELECT * FROM user WHERE state = 'CA' AND credit > 2000; \nIf you don't know",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Create a SQL request to find all users who live in California and have over 1000 credits: SELECT * FROM user WHERE state = 'CA' AND credit > 1000;\n\nThis will return the following rows from your database table:\n | id  | name   | email    | password |\n ---------------------------------\n  1   | John   | john@example.com| 1234567890\n\n\n\n  2   | Jane   | jane@example.",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Create a SQL request to find all users who live in California and have over 1000 credits: SELECT * FROM user WHERE state = 'CA' AND credit > 1000;\n\nYou can also use the LIMIT clause with this query, which will return only 10 rows. This is useful if you want to see how many users meet your criteria for each state:\nSELECT COUNT(*) AS total_rows, state",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Create a SQL request to find all users who live in California and have over 1000 credits: SELECT * FROM user WHERE state = 'CA' AND credit > 1000;\n\nYou can also use the following query if you want to filter by gender or location: SELECT * FROM user WHERE gender='Male' OR city= 'San Francisco'; \nIf you're looking for specific information about one of these",
                "stop_reason": "max_length",
            },
        ],
    },
    "default-extract-contact-info": {
        "id": "default-extract-contact-info",
        "title": "Extract contact information",
        "tags": ["Transformation", "Generation"],
        "generate_params": {
            "text": "Extract the name and mailing address from this email:\n\nDear Kelly,\n\nIt was great to talk to you at the seminar. I thought Jane's talk was quite good.\n\nThank you for the book. Here's my address 2111 Ash Lane, Crestview CA 92002\n\nBest,\n\nMaya\n\nName:",
            "number_of_results": 4,
            "temperature": 1,
        },
        "description": "Extract contact information from a block of text.",
        "icon": "Mail",
        "results": [
            {
                "generated_text": "Extract the name and mailing address from this email:\n\nDear Kelly,\n\nIt was great to talk to you at the seminar. I thought Jane's talk was quite good.\n\nThank you for the book. Here's my address 2111 Ash Lane, Crestview CA 92002\n\nBest,\n\nMaya\n\nName: Maya Email: hello@email.com Mailing Address: 2111 Ash Lane, Crestview Ca 92002 Thanks! Your email has been sent successfully. Thank you again! Email Message 1 Sent Successfully The message has now been resent with the following change - You can also reach me by phone (800) 832-2222\nEmail Subject Hello MAYA Email Body Happy Holidays Happy New Year We will be closed January 5 through 7.  Happy holidays Happy new year You can call or text",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Extract the name and mailing address from this email:\n\nDear Kelly,\n\nIt was great to talk to you at the seminar. I thought Jane's talk was quite good.\n\nThank you for the book. Here's my address 2111 Ash Lane, Crestview CA 92002\n\nBest,\n\nMaya\n\nName: Maya Lenz Address: 2211 Ash Lane Crestview CA 92002 Thanks to those who attended our seminar on April 16th.\n\nWe have a wonderful lineup of speakers coming up soon! If you're interested in attending some or all of these seminars next year, let me know by emailing jane@demoscene.com so that we can send out more information. We'd love to see you again! Thank you!\n\nKelly: <file_other> Jane is going to be",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Extract the name and mailing address from this email:\n\nDear Kelly,\n\nIt was great to talk to you at the seminar. I thought Jane's talk was quite good.\n\nThank you for the book. Here's my address 2111 Ash Lane, Crestview CA 92002\n\nBest,\n\nMaya\n\nName: Maya Muddleduck Jones Email: mayamudde@gmail.com Address: 2111 Ash Lane, Crestview CA 92002 Thanks! [...] You can find more details about that email below. The subject line of the original message is May 1 - 10 Seminar 2011 Conference Call Registration Form (1). It contains a PDF attachment titled registration form22011.pdf. Note that there are two forms in here with the same number on them - one for each day of the conference call",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Extract the name and mailing address from this email:\n\nDear Kelly,\n\nIt was great to talk to you at the seminar. I thought Jane's talk was quite good.\n\nThank you for the book. Here's my address 2111 Ash Lane, Crestview CA 92002\n\nBest,\n\nMaya\n\nName: Maya Kuo Address: 2111 Ash Lane, Crestview CA 92002 Phone: +1 (209) 834-2222 Email: kelly@crescent-ccb-capital.com Contact her on Twitter @CrisKelly or Facebook Kelly Cline Banking Advisor You can reach Maya through email at 1 (888) 363-0777. Your banker will be able to answer your questions regarding a mortgage loan program if you'd like some help in determining what would work best with",
                "stop_reason": "max_length",
            },
        ],
    },
    "default-js-to-py": {
        "id": "default-js-to-py",
        "title": "JavaScript to Python",
        "tags": ["Code", "Transformation", "Translation"],
        "generate_params": {
            "text": '#JavaScript to Python:\nJavaScript: \ndogs = ["bill", "joe", "carl"]\ncar = []\ndogs.forEach((dog) {\n    car.push(dog);\n});\n\nPython:',
            "number_of_results": 4,
            "temperature": 1,
        },
        "description": "Convert simple JavaScript expressions into Python.",
        "icon": "Terminal",
        "results": [
            {
                "generated_text": '#JavaScript to Python:\nJavaScript: \ndogs = ["bill", "joe", "carl"]\ncar = []\ndogs.forEach((dog) {\n    car.push(dog);\n});\n\nPython: cars = [dog for dog in dogs if dog!= \'john\']\nprint(car) #[\'carl\',\'joe\']\nprint(len(cars)) #3\n\n\n\ndef f():\n   print(dogs)\nf()\n\n\n\n\n#javascript2py3:\n JavaScript (NodeJs):\n // create a list of strings and add them all into `list`\n function makeList(){\n  var str1="one";   document.write(str1);  ',
                "stop_reason": "max_length",
            },
            {
                "generated_text": "#JavaScript to Python:\nJavaScript: \ndogs = [\"bill\", \"joe\", \"carl\"]\ncar = []\ndogs.forEach((dog) {\n    car.push(dog);\n});\n\nPython:\ncar = ['dog1', 'dog2']\n\n\n\nfor x in dogs: print (x)\n\nprint (car) # prints list of dogs names and cars that they are in as array elements with [0] being the first element in the car array. For example if a name has multiple cars then you will see ['card1'][2] or whatever value it was.  # Printing all values from the arrays... \nallValuesFromArray1 = [car[0]][0]\nallValuesFromArray2 = [",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "#JavaScript to Python:\nJavaScript: \ndogs = [\"bill\", \"joe\", \"carl\"]\ncar = []\ndogs.forEach((dog) {\n    car.push(dog);\n});\n\nPython: cars = ['dogs', 'doggie', 'cat']\nfor car in cars :\n  print (car) # print each element of a list in alphabetical order   print()\n\nprint (car) # print last element only if you are looking for that value! \ncars[2]  = 'johnny dogs'\n\ncars[-1] = 'cats and dogs';\nprint(len(cars)) # number of elements contained within the array or list.\n\n\n\ncars[3]= ['",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "#JavaScript to Python:\nJavaScript: \ndogs = [\"bill\", \"joe\", \"carl\"]\ncar = []\ndogs.forEach((dog) {\n    car.push(dog);\n});\n\nPython: ###CodeHere ###\ndogs  = ['bob',  'john','mike'] # dogs in a list\ndogs.sort()          # sort the dogs according their names.\ncars=[]             # declare cars in the same way as `dogs` did earlier.\n\nfor dog inDogs:     # assign values into cars with each of `dogs` elements. \ncars.append(dog)\n\ncarryout_something_with_the_cars_and_dogs();    \ndef carryout_s",
                "stop_reason": "max_length",
            },
        ],
    },
    "default-friend-chat": {
        "id": "default-friend-chat",
        "title": "Friend chat",
        "tags": ["Conversation", "Generation"],
        "generate_params": {
            "text": "You: What have you been up to?\nFriend: Watching old movies.\nYou: Did you watch anything interesting?\nFriend:",
            "max_length": 60,
            "number_of_results": 4,
            "temperature": 0.5,
            "stop_sequences": ["You:"],
        },
        "description": "Emulate a text message conversation.",
        "icon": "ChatAlt",
        "results": [
            {
                "generated_text": "You: What have you been up to?\nFriend: Watching old movies.\nYou: Did you watch anything interesting?\nFriend: Yes, I watched this one. It was really good. The story is about a woman who lost her husband in the war and now she has no other choice but to take care of her children by herself. You should see it if you're interested. Friend: I'd love to! Friend: Sounds like",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "You: What have you been up to?\nFriend: Watching old movies.\nYou: Did you watch anything interesting?\nFriend: Yes, I saw this movie. It's really good! You should see it too. Friend: Thanks but I'm not interested in watching that anymore. I've seen it a lot of times before. You know how much I hate repetition. Friend: Oh no? How come? You like the plot and everything else",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "You: What have you been up to?\nFriend: Watching old movies.\nYou: Did you watch anything interesting?\nFriend: Yes. I saw a film about the Titanic. It was very sad, but it made me think of my parents' relationship with each other. You know how they were when they first met? Friend: No. How did you two meet? Friend's mother: They didn't even know that their son and",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "You: What have you been up to?\nFriend: Watching old movies.\nYou: Did you watch anything interesting?\nFriend: Yes, I saw a movie about aliens. You know what it was called? Friend: Alien 3! Friend: It is so good! You should see it too. But I'm not sure if my parents will let me. They are watching TV now. I think they might be asleep. If you want",
                "stop_reason": "max_length",
            },
        ],
    },
    "default-mood-color": {
        "id": "default-mood-color",
        "title": "Mood to color",
        "tags": ["Transformation", "Generation"],
        "generate_params": {
            "text": "The CSS code for a color like a blue sky at dusk:\n\nbackground-color: #",
            "number_of_results": 4,
            "temperature": 1,
            "stop_sequences": [";"],
        },
        "description": "Turn a text description into a color.",
        "icon": "EmojiHappy",
        "results": [
            {
                "generated_text": "The CSS code for a color like a blue sky at dusk:\n\nbackground-color: #00BFFF",
                "stop_reason": ";",
            },
            {
                "generated_text": "The CSS code for a color like a blue sky at dusk:\n\nbackground-color: #8495ed solid",
                "stop_reason": ";",
            },
            {
                "generated_text": "The CSS code for a color like a blue sky at dusk:\n\nbackground-color: #009D62",
                "stop_reason": ";",
            },
            {
                "generated_text": "The CSS code for a color like a blue sky at dusk:\n\nbackground-color: #f4f4e6",
                "stop_reason": ";",
            },
        ],
    },
    "default-python-docstring": {
        "id": "default-python-docstring",
        "title": "Write a Python docstring",
        "tags": ["Code", "Generation"],
        "generate_params": {
            "text": "# Python 3.7\n \ndef randomly_split_dataset(folder, filename, split_ratio=[0.8, 0.2]):\n    df = pd.read_json(folder + filename, lines=True)\n    train_name, test_name = \"train.jsonl\", \"test.jsonl\"\n    df_train, df_test = train_test_split(df, test_size=split_ratio[1], random_state=42)\n    df_train.to_json(folder + train_name, orient='records', lines=True)\n    df_test.to_json(folder + test_name, orient='records', lines=True)\nrandomly_split_dataset('finetune_data/', 'dataset.jsonl')\n    \n# An elaborate, high quality docstring for the above function:\n\"\"\"",
            "max_length": 150,
            "number_of_results": 4,
            "temperature": 1,
            "stop_sequences": ["#", '"""'],
        },
        "description": 'An example of how to create a docstring for a given Python function. We specify the Python version, paste in the code, and then ask within a comment for a docstring, and give a characteristic beginning of a docstring (""").',
        "icon": "Code",
        "results": [
            {
                "generated_text": "# Python 3.7\n \ndef randomly_split_dataset(folder, filename, split_ratio=[0.8, 0.2]):\n    df = pd.read_json(folder + filename, lines=True)\n    train_name, test_name = \"train.jsonl\", \"test.jsonl\"\n    df_train, df_test = train_test_split(df, test_size=split_ratio[1], random_state=42)\n    df_train.to_json(folder + train_name, orient='records', lines=True)\n    df_test.to_json(folder + test_name, orient='records', lines=True)\nrandomly_split_dataset('finetune_data/', 'dataset.jsonl')\n    \n# An elaborate, high quality docstring for the above function:\n\"\"\"\nThis function creates two files in a directory that represent different splits of the dataset and reads them into memory.\nThe split ratio (1 < n_samples / len(sample_set)) is configurable. The sample dataset will only be read as long it does not already exist! ",
                "stop_reason": '"""',
            },
            {
                "generated_text": "# Python 3.7\n \ndef randomly_split_dataset(folder, filename, split_ratio=[0.8, 0.2]):\n    df = pd.read_json(folder + filename, lines=True)\n    train_name, test_name = \"train.jsonl\", \"test.jsonl\"\n    df_train, df_test = train_test_split(df, test_size=split_ratio[1], random_state=42)\n    df_train.to_json(folder + train_name, orient='records', lines=True)\n    df_test.to_json(folder + test_name, orient='records', lines=True)\nrandomly_split_dataset('finetune_data/', 'dataset.jsonl')\n    \n# An elaborate, high quality docstring for the above function:\n\"\"\"\n\nTest with the finetuning dataset.\nThis one is a bit more involved because we need to know about the specific steps and order in which they were used during training on this dataset.\n\nOnly run this script if you have the finetuning_trainings_example_gigantic_mouse_cars_model_simulation_folder_path.txt file!\nThe output looks like this:\ntraining-steps-during-training-on-finetunning-data-for-evaluating-multiple-runs-successfully... \\\n  - first-update-step-seen-2457939605925585584389062185466573769263044687597231670331386271117282224091247",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "# Python 3.7\n \ndef randomly_split_dataset(folder, filename, split_ratio=[0.8, 0.2]):\n    df = pd.read_json(folder + filename, lines=True)\n    train_name, test_name = \"train.jsonl\", \"test.jsonl\"\n    df_train, df_test = train_test_split(df, test_size=split_ratio[1], random_state=42)\n    df_train.to_json(folder + train_name, orient='records', lines=True)\n    df_test.to_json(folder + test_name, orient='records', lines=True)\nrandomly_split_dataset('finetune_data/', 'dataset.jsonl')\n    \n# An elaborate, high quality docstring for the above function:\n\"\"\"Randomly splits dataset to train/test dataset using scikit-learn.\nIf there are two data sets with same name in different folders, it will not return duplicates.\nExample : data\\input_data\\train1 and data\\input_data\\dontExist\\test\\\nThe first one is kept while rest of them are removed as an exception.   \nIf you want a new training/validation dataset instead then pass `batches` parameter, i.e.,:\n \\``train_batches=\\tuesday\\to Friday;monday-to-monday: 1\\`` which means that we use all Monday's rows from input_data (but not Tuesday ones). \n\\note You have to make sure that your folder structure looks like this:    ",
                "stop_reason": "max_length",
            },
            {
                "generated_text": '# Python 3.7\n \ndef randomly_split_dataset(folder, filename, split_ratio=[0.8, 0.2]):\n    df = pd.read_json(folder + filename, lines=True)\n    train_name, test_name = "train.jsonl", "test.jsonl"\n    df_train, df_test = train_test_split(df, test_size=split_ratio[1], random_state=42)\n    df_train.to_json(folder + train_name, orient=\'records\', lines=True)\n    df_test.to_json(folder + test_name, orient=\'records\', lines=True)\nrandomly_split_dataset(\'finetune_data/\', \'dataset.jsonl\')\n    \n# An elaborate, high quality docstring for the above function:\n"""\nGiven a jsonl file (e.g., one generated by pytorch), you can easily split it in two and apply deep learning on each part.\nTo do this we need to use numpy arrays instead of objects because np is not defined inside a JSON line.\nWe have written an example at the top of this document that uses pydotnet for visualization.\nHere are more details about how such code might look like.\n\n.. versionadded:: 1.5.2\n\nOptions:\n  * `train` - Use only data from "training set" as input.\n  * `test`  - Use only data from "test" as input.\n  * :meth:`~sklearn.model_selection.cross_validation.ShuffleSplit`\n   - Use random',
                "stop_reason": "max_length",
            },
        ],
    },
    "default-analogy-maker": {
        "id": "default-analogy-maker",
        "title": "Analogy maker",
        "tags": ["Generation"],
        "generate_params": {
            "text": "Create an analogy for this phrase:\n\nQuestions are arrows in that:",
            "max_length": 60,
            "number_of_results": 4,
            "temperature": 0.5,
        },
        "description": "Create analogies. Modified from a community prompt to require fewer examples.",
        "icon": "LightBulb",
        "results": [
            {
                "generated_text": "Create an analogy for this phrase:\n\nQuestions are arrows in that: they point to the future, and help us think about things that we want to do. They also provide feedback on how we're doing with our goals. In other words, questions can be a helpful tool when it comes to making decisions. Let's say you have some big plans for your life. You know what",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Create an analogy for this phrase:\n\nQuestions are arrows in that: they point to a goal. They also have the power of destruction if not used wisely. Yes, I agree with you that questions can be destructive when asked without thinking. But as long as we ask them carefully and constructively, then yes, they do indeed lead us towards a better understanding of life",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Create an analogy for this phrase:\n\nQuestions are arrows in that: they point to a destination. They also have the power of travel. How do you think questions can be used as powerful tools? An arrow points to its target, but it is not that only what it does; how and where it goes is equally important. The same applies with questions. A question has",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Create an analogy for this phrase:\n\nQuestions are arrows in that: they point to the future, and we can use them as a guide. Questions are like arrows that lead us toward the future. Yes! Yes! Yes! Yes! Yes! Yes! Yes! No! Yes! Yes! Yes! Yes! Yes! Yes! Yes! Yes! Yes! Yes",
                "stop_reason": "max_length",
            },
        ],
    },
    "default-js-one-line": {
        "id": "default-js-one-line",
        "title": "JavaScript one line function",
        "tags": ["Code", "Transformation", "Translation"],
        "generate_params": {
            "text": "Use list comprehension to convert this into one line of JavaScript:\n\ndogs.forEach((dog) => {\n    car.push(dog);\n});\n\nJavaScript one line version:",
            "max_length": 60,
            "number_of_results": 4,
            "temperature": 1,
            "stop_sequences": [";"],
        },
        "description": "Turn a JavaScript function into a one liner.",
        "icon": "Terminal",
        "results": [
            {
                "generated_text": "Use list comprehension to convert this into one line of JavaScript:\n\ndogs.forEach((dog) => {\n    car.push(dog);\n});\n\nJavaScript one line version: \nlet cars = dogs.map((x, i)=> {return x",
                "stop_reason": ";",
            },
            {
                "generated_text": 'Use list comprehension to convert this into one line of JavaScript:\n\ndogs.forEach((dog) => {\n    car.push(dog);\n});\n\nJavaScript one line version: \nconst dogs = ["Mary", "Robert", "Joe"],\ncar = []',
                "stop_reason": ";",
            },
            {
                "generated_text": 'Use list comprehension to convert this into one line of JavaScript:\n\ndogs.forEach((dog) => {\n    car.push(dog);\n});\n\nJavaScript one line version: (function(){var cars = [{"name":"car","children":[{"name":"dog"}]}',
                "stop_reason": ";",
            },
            {
                "generated_text": "Use list comprehension to convert this into one line of JavaScript:\n\ndogs.forEach((dog) => {\n    car.push(dog);\n});\n\nJavaScript one line version: \nvar cars = [...dogs]",
                "stop_reason": ";",
            },
        ],
    },
    "default-micro-horror": {
        "id": "default-micro-horror",
        "title": "Micro horror story creator",
        "tags": ["Transformation", "Generation", "Translation"],
        "generate_params": {
            "text": "Topic: Breakfast\nTwo-Sentence Horror Story: He always stops crying when I pour the milk on his cereal. I just have to remember not to let him see his face on the carton.\n    \nTopic: Wind\nTwo-Sentence Horror Story:",
            "max_length": 60,
            "number_of_results": 4,
            "temperature": 0.8,
        },
        "description": "Creates two to three sentence short horror stories from a topic input.",
        "icon": "PencilAlt",
        "results": [
            {
                "generated_text": "Topic: Breakfast\nTwo-Sentence Horror Story: He always stops crying when I pour the milk on his cereal. I just have to remember not to let him see his face on the carton.\n    \nTopic: Wind\nTwo-Sentence Horror Story: His mother is going out of control, and she has no idea why. She tries to stop her husband from drinking too much beer but he won't listen.\n    \nNo spoilers please... Topics are: Baby food Childhood story Crying Father daughter Father child Forgiveness Parenting Parental conflict Parents",
                "stop_reason": "max_length",
            },
            {
                "generated_text": 'Topic: Breakfast\nTwo-Sentence Horror Story: He always stops crying when I pour the milk on his cereal. I just have to remember not to let him see his face on the carton.\n    \nTopic: Wind\nTwo-Sentence Horror Story: We are being blown away by strong winds, and our tent is coming off. My phone can\'t even pick up a signal.\n    """\n\n\n\n\n"""\n\nTwo-Paragraph Horror Story: After losing my camera in Hong Kong, it was very hard for me to find another one because there aren\'t any shops selling',
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Topic: Breakfast\nTwo-Sentence Horror Story: He always stops crying when I pour the milk on his cereal. I just have to remember not to let him see his face on the carton.\n    \nTopic: Wind\nTwo-Sentence Horror Story: We all get seasick in this car, even though it's so quiet that there is hardly any wind at all.\n        \nI don't know if I'm going to be able to sleep tonight.... Two-Sentence Horror Story: My husband keeps staring out of the window because he can't sleep and he's looking",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Topic: Breakfast\nTwo-Sentence Horror Story: He always stops crying when I pour the milk on his cereal. I just have to remember not to let him see his face on the carton.\n    \nTopic: Wind\nTwo-Sentence Horror Story: When my sister and brother-in-law first moved in, we were so lucky they had a front door with two wind breaks\n        \xa0\n\nTwo Sentences - No Thumbs Up or Down Stories: None of these seem interesting enough for me. There are more? No. No. Yes. Yes.",
                "stop_reason": "max_length",
            },
        ],
    },
    "default-third-person": {
        "id": "default-third-person",
        "title": "Third-person converter",
        "tags": ["Transformation", "Generation", "Translation"],
        "generate_params": {
            "text": "Convert this from first-person to third person (gender female):\n\nI decided to make a movie about Ada Lovelace.",
            "max_length": 60,
            "number_of_results": 4,
            "temperature": 1,
        },
        "description": "Converts first-person POV to the third-person. This is modified from a community prompt to use fewer examples.",
        "icon": "PencilAlt",
        "results": [
            {
                "generated_text": "Convert this from first-person to third person (gender female):\n\nI decided to make a movie about Ada Lovelace. I think she should be considered the first programming woman in history. It will tell her story as told by other women who influenced and challenged her, such as Grace Hopper of Johns Hopkins University. She is the epitome of being driven, determined and ambitious without fear. The following are ways to help me",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Convert this from first-person to third person (gender female):\n\nI decided to make a movie about Ada Lovelace. I went ahead and wrote the story that is below... I'm now looking for someone who can edit, add visuals etc before producing my film!.\n\nHi there! My name's Sarah and I'll be writing some script/story for you today in order to create a short horror/fantasy comedy movie with",
                "stop_reason": "max_length",
            },
            {
                "generated_text": 'Convert this from first-person to third person (gender female):\n\nI decided to make a movie about Ada Lovelace. I made her as the main character and have it titled  "First Lady".\n\nThere is now an Ada Lovelace Festival in Texas every August with talks on her accomplishments, book signing events for those who are interested in learning more and art installations around town. She has become an inspiration for computer',
                "stop_reason": "max_length",
            },
            {
                "generated_text": 'Convert this from first-person to third person (gender female):\n\nI decided to make a movie about Ada Lovelace. I watched some of her movies on YouTube and saw that she is famous for the program called Babbage\'s Analytical Engine. She was also famously known as "the first computer programmer". After reading articles, books, etc., it became apparent that there were many other people who are now considered "first',
                "stop_reason": "max_length",
            },
        ],
    },
    "default-notes-summary": {
        "id": "default-notes-summary",
        "title": "Notes to summary",
        "tags": ["Transformation", "Generation"],
        "generate_params": {
            "text": "Convert my short hand into a first-hand account of the meeting:\n\nTom: Profits up 50%\nJane: New servers are online\nKjel: Need more time to fix software\nJane: Happy to help\nParkman: Beta testing almost done",
            "number_of_results": 4,
            "temperature": 1,
        },
        "description": "Turn meeting notes into a summary.",
        "icon": "PencilAlt",
        "results": [
            {
                "generated_text": "Convert my short hand into a first-hand account of the meeting:\n\nTom: Profits up 50%\nJane: New servers are online\nKjel: Need more time to fix software\nJane: Happy to help\nParkman: Beta testing almost done Tom is very happy about his business profits, and new servers have been deployed. Jane will test her application on that newly available hardware before finalizing it. Kjel needs some time to finish fixing an issue with their program so they could start beta-testing again. And Parkman has just finished setting-up all of their infrastructure for beta-testing. They were having problems when running their code in production environment but now things seem fine as well. Asking them what they're working on can make your readers'",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Convert my short hand into a first-hand account of the meeting:\n\nTom: Profits up 50%\nJane: New servers are online\nKjel: Need more time to fix software\nJane: Happy to help\nParkman: Beta testing almost done Tom's profits have gone up by 50% and new servers have been launched. Kjel needs some more time to finish his beta testing but he will be available for it soon, says Jane. On top of that, Parkman said he's just about ready with their test version - happy they can work together! The meeting was successful thanks to all these positive news from different projects within the company. It's great to hear what everyone has achieved in terms of progress. This is why it's important to keep track on daily",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Convert my short hand into a first-hand account of the meeting:\n\nTom: Profits up 50%\nJane: New servers are online\nKjel: Need more time to fix software\nJane: Happy to help\nParkman: Beta testing almost done Tom's profit went up by 50%. Jane is working on new server hardware and Kjel needs some extra hours in order to finish fixing his software. They all seem happy about it, including Parkman who's nearly finished beta-testing their project. The next meeting will be held at Johnsons house this Saturday afternoon starting with a lunch around 12 PM. See you there! Lunch starts at 1:30 pm so that everyone can have time for questions or comments before joining us in person around 3PM. There",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Convert my short hand into a first-hand account of the meeting:\n\nTom: Profits up 50%\nJane: New servers are online\nKjel: Need more time to fix software\nJane: Happy to help\nParkman: Beta testing almost done Tom has made profits by 50%. He is happy about it because he used all his hard work and effort. A new server was built recently in preparation for an upcoming expansion. It will be ready soon as well, since Kjel works on fixing the program now while Jane helped him with it before she went back home. Parkman still needs some finalizing things but is sure that we should release the beta version next week. The full version will come out this month or may possibly even later. If you",
                "stop_reason": "max_length",
            },
        ],
    },
    "default-vr-fitness": {
        "id": "default-vr-fitness",
        "title": "VR fitness idea generator",
        "tags": ["Generation"],
        "generate_params": {
            "text": "Brainstorm some ideas combining VR and fitness:",
            "max_length": 150,
            "number_of_results": 4,
            "temperature": 0.6,
            "presencePenalty": 1,
        },
        "description": "Create ideas for fitness and virtual reality games.",
        "icon": "LightBulb",
        "results": [
            {
                "generated_text": "Brainstorm some ideas combining VR and fitness: run a race, play soccer, or do yoga. Find something that you enjoy doing in real life but would like to try with the virtual reality headset on. You can even combine activities from different categories if you're feeling inspired! For example, running and playing football are both sports so they could be combined. Try out new things when it comes to exercise and workout routines. Make sure you know what your limits before trying something new because you may get hurt easily while using the technology. When you use a VR headset for games, there is always going to be an element of risk involved, especially since you will not have any physical contact during the gameplay. Be careful when working out with the headset too. Don't push yourself past your abilities",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Brainstorm some ideas combining VR and fitness:  You could design a virtual reality workout to improve athletic skills. You can also create an exercise video game that uses the same principles as FIFA, NBA 2K or other sports games. If you are passionate about gaming then this is your chance to bring it into the real world! Create an app for smartphone users. Get creative with how people use virtual reality in health care:  Create apps for rehabilitation of brain injuries such as stroke patients or Alzheimer's disease sufferers. Develop programs for children who have physical disabilities like cerebral palsy. Use virtual reality technology to help people overcome mental illnesses including depression and anxiety disorders. The potential for education will be huge when we start seeing more educational institutions adopt VR:  Virtual Reality has been shown to",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Brainstorm some ideas combining VR and fitness: running, biking, yoga, dance. Think about what you could do with a virtual reality bike or exercise equipment at home that would be fun to try out while working on your health. For example, how many calories can I burn by riding my new VR bicycle? Or maybe I’ll work up an appetite for the next meal after doing this kind of activity! Get creative. Remember, it’s not just about technology. If you’re having trouble coming up with great ideas, talk it over with friends who are also into fitness or tech. They might have good suggestions!\nNow that you’ve come up with lots of great ideas, narrow them down based on factors like cost, usability, safety, etc. Then choose one or two of these concepts",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Brainstorm some ideas combining VR and fitness: how can we incorporate both into a game? for example, running while wearing the headset or training with weights. You could also create an activity that involves your whole body such as boxing or yoga. Keep in mind that you will need to be able to play the game without touching any screens. Create physical exercises based on movements of the video games character. For example: if the main character is jumping up, then try doing jump squats instead. Try using virtual reality gaming to motivate people towards exercise by offering incentives like rewards and badges. Incentive them to work harder through positive feedback when they complete their goals. Make sure you are aware of potential health risks before introducing new technology into your gym. Use caution when implementing VR into your business",
                "stop_reason": "max_length",
            },
        ],
    },
    "default-esrb-rating": {
        "id": "default-esrb-rating",
        "title": "ESRB rating",
        "tags": ["Classification"],
        "generate_params": {
            "text": 'Provide an ESRB rating for the following text:\n\n"i\'m going to blow your brains out with my ray gun then stomp on your guts."\n\nESRB rating:',
            "max_length": 60,
            "number_of_results": 4,
            "temperature": 0.3,
            "stop_sequences": ["\n"],
        },
        "description": "Categorize text based upon ESRB ratings.",
        "icon": "Tag",
        "results": [
            {
                "generated_text": "Provide an ESRB rating for the following text:\n\n\"i'm going to blow your brains out with my ray gun then stomp on your guts.\"\n\nESRB rating: Mature (18+) This game is rated mature because it contains graphic violence and language that may be offensive to some players. Mature 18+ Rating - Description of this Game's Content The description above does not contain all information about the content of this game. Please read the full review before playing",
                "stop_reason": "max_length",
            },
            {
                "generated_text": 'Provide an ESRB rating for the following text:\n\n"i\'m going to blow your brains out with my ray gun then stomp on your guts."\n\nESRB rating: Mature (18+) This is a violent game that contains graphic violence and gore, so it should be rated mature. Mature 18+ rating required. Yes! No! Yes! Yes! Yes! Yes! Yes! Yes! Yes! Yes! Yes! Yes! Yes! Yes! Yes',
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Provide an ESRB rating for the following text:\n\n\"i'm going to blow your brains out with my ray gun then stomp on your guts.\"\n\nESRB rating: Mature (18+) This is a violent game, but it also has humorous elements. Mature 18+ rated game. It's very funny and it's not too bad. Mature (18+) 3 stars Mature (18+) 3 stars Mature (18+) 3 stars M",
                "stop_reason": "max_length",
            },
            {
                "generated_text": 'Provide an ESRB rating for the following text:\n\n"i\'m going to blow your brains out with my ray gun then stomp on your guts."\n\nESRB rating: Mature (18+) This game is rated mature because it contains violent language and graphic images. Mature content warning! 18+ only. Mature (18+) This game has a mature rating of Mature (18+). The character in this video game will use his raygun to kill',
                "stop_reason": "max_length",
            },
        ],
    },
    "default-essay-outline": {
        "id": "default-essay-outline",
        "title": "Essay outline",
        "tags": ["Generation"],
        "generate_params": {
            "text": "Create an outline for an essay about Nikola Tesla and his contributions to technology:",
            "number_of_results": 4,
            "temperature": 1,
            "max_length": 150,
        },
        "description": "Generate an outline for a research topic.",
        "icon": "DocumentText",
        "results": [
            {
                "generated_text": "Create an outline for an essay about Nikola Tesla and his contributions to technology: - He was the inventor of many technologies, including electricity. - His life was shortened by disease. - His work inspired several people around the world.\nNikola Tesla is considered one of the most important inventors in history. In this article we'll describe some examples that highlight his importance as a scientist. The first example concerns Tesla's invention of electricity. As described above, he designed equipment which could be used to generate, store or distribute power. Most modern-day countries have either developed their own form of electric energy or are currently developing new ways to produce more energy efficiently. We can see how much technology has evolved since Tesla created these methods using today's society, particularly our reliance on the internet. Many aspects of human culture would not exist without the influence",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Create an outline for an essay about Nikola Tesla and his contributions to technology: -Tesla's achievements include inventing several types of electric motors, wireless radio systems, as well as lighting devices, such as a flashlight.- He also developed the first practical induction machine, which enabled him to build more efficient electrical machines, including generators, alternators, motors... -He is regarded by some historians of science and many engineers today as one of the greatest American innovators.\n\n\n\nNikola Tesla\n\nHistory of Science\nA History of Modern Physics\n\n\n\nThe works are now published under the imprint World Scientific Publishing Company The history of modern physics has been dominated in recent centuries not only by Newton's scientific revolution but also largely through the developments brought upon it and inspired by this revolution. This development was greatly aided by new methods",
                "stop_reason": "max_length",
            },
            {
                "generated_text": 'Create an outline for an essay about Nikola Tesla and his contributions to technology: -Tesla, inventor of the modern alternating current electric motor. -The induction machine is another invention by Tesla. -Other inventions include radio frequency (RF) antennas, capacitors,... Discover why people think this person was important in their life? Do you know any famous people with that name? What do they contribute to society or science? Use your own voice, so it\'s authentic. Try saying things like: "Many people have written..." "I saw these photos on Facebook...." "The new iPad looks great!" You can also talk about yourself a lot because you\'ll get more practice talking out loud as well. For example, tell stories from home schooling experiences, family vacations, etc. You may want to share how you got',
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Create an outline for an essay about Nikola Tesla and his contributions to technology: What is the main topic of this article? Here you can find a list on what you should write in your paper: Technology has been developed by scientists including Nikola Tesla. His achievements are mainly due to invention of some new concepts, which led to creation of many useful devices that have changed our world significantly.\nHistory\nInvention and contribution to science\n\nDiscoveries\nTechnology today depends heavily on developments made in the 20th century. Many inventions like telegraph, phone, radio, electric motor have come from electrical engineer named as Tesla. His work was unique because he could produce electricity directly using electromagnetic energy.\n\nTesla's contributions include electromagnetism and modern technology such as:\n\nHow were technologies developed?\nHis idea started with creating a bridge between classical",
                "stop_reason": "max_length",
            },
        ],
    },
    "default-recipe-generator": {
        "id": "default-recipe-generator",
        "title": "Recipe creator (eat at your own risk)",
        "tags": ["Generation"],
        "generate_params": {
            "text": "Write a recipe based on these ingredients and instructions:\n\nFrito Pie\n\nIngredients:\nFritos\nChili\nShredded cheddar cheese\nSweet white or red onions, diced small\nSour cream\n\nInstructions:",
            "max_length": 120,
            "number_of_results": 4,
            "temperature": 0.3,
        },
        "description": "Create a recipe from a list of ingredients.",
        "icon": "Cake",
        "results": [
            {
                "generated_text": "Write a recipe based on these ingredients and instructions:\n\nFrito Pie\n\nIngredients:\nFritos\nChili\nShredded cheddar cheese\nSweet white or red onions, diced small\nSour cream\n\nInstructions:\n1. Place the chips in a large bowl with sour cream.\n2. Add the rest of the ingredients to taste.  You can add more sour cream if you want it thicker. 3. Serve immediately! Finished. This is an easy appetizer that will be sure to impress your guests at any party you're throwing. It's also great for parties where there are kids because it's not too messy. It has all sorts of different flavors together so everyone gets something they like. If you don't have fritos, use tortilla strips instead. Frito pie is delicious as is but you could",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Write a recipe based on these ingredients and instructions:\n\nFrito Pie\n\nIngredients:\nFritos\nChili\nShredded cheddar cheese\nSweet white or red onions, diced small\nSour cream\n\nInstructions: 1. Heat the oil in a large skillet over medium heat until it is shimmering.\n2. Add the chorizo to the hot pan for about 5 minutes, stirring occasionally, until it's browned.  Remove from the heat once done.\n3. Pour 2 cups of chicken broth into the skillet with the chorizo. Stir well to combine everything together.\n4. Return the fried pork to the skillet along with 1 cup (240 ml) sour cream. Cook for another 3 minutes, stirring frequently. Serve warm. Finished!.\xa0  You can",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Write a recipe based on these ingredients and instructions:\n\nFrito Pie\n\nIngredients:\nFritos\nChili\nShredded cheddar cheese\nSweet white or red onions, diced small\nSour cream\n\nInstructions:\n\n1. In a large skillet over medium heat, add the oil to melt.  Add the chorizo sausage and cook until browned.\n2. Remove from pan with slotted spoon and set aside.\n3. Return the same skillet to medium-high heat and add the chopped green chilies and garlic cloves to it.  Cook for about 3 minutes.\n4. Stir in the salsa verde and tomato paste.  Mix well and bring to boil.\n5. Pour into pie dish and top with shredded cheddar cheese.\n6. Bake at 350 degrees F (",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Write a recipe based on these ingredients and instructions:\n\nFrito Pie\n\nIngredients:\nFritos\nChili\nShredded cheddar cheese\nSweet white or red onions, diced small\nSour cream\n\nInstructions: 1. Heat the oil in a large skillet over medium heat until it is shimmering.\n2. Add 1 tablespoon of butter to the pan for each fried egg you are making.  This will help them cook evenly.\n3. Place 2 eggs into the hot oil one at a time.  Cook both sides until they are golden brown and cooked through (about 3 minutes).\n4. Remove from the pan with slotted spoon onto paper towels lined plate so that they can cool slightly before serving.\n5. Repeat steps 2-4 with all the other eggs. 6. Combine the",
                "stop_reason": "max_length",
            },
        ],
    },
    "default-chat": {
        "id": "default-chat",
        "title": "Chat",
        "tags": ["Conversation", "Generation"],
        "generate_params": {
            "text": "The following is a conversation with an AI assistant. The assistant is helpful, creative, clever, and very friendly.\n\nHuman: Hello, who are you?\nAI: I am an AI created by OpenAI. How can I help you today?\nHuman: I'd like to cancel my subscription.\nAI:",
            "max_length": 150,
            "presencePenalty": 0.6,
            "number_of_results": 4,
            "temperature": 0.9,
            "top_p": 1,
            "stop_sequences": [" Human:", " AI:"],
        },
        "description": "Open ended conversation with an AI assistant.",
        "icon": "ChatAlt",
        "results": [
            {
                "generated_text": "The following is a conversation with an AI assistant. The assistant is helpful, creative, clever, and very friendly.\n\nHuman: Hello, who are you?\nAI: I am an AI created by OpenAI. How can I help you today?\nHuman: I'd like to cancel my subscription.\nAI: Have you tried the one in April? Unfortunately it's not possible at this point.\n\nHuman: Oh well, thanks for your time anyway! Goodbye\n\nWith more progress on smart machines it will eventually be able to mimic human behavior and thoughts much better than humans do now. This raises obvious concerns about privacy, automation and robotics jobs. These issues have been debated for centuries but are becoming real problems right now that will become bigger problems as machine intelligence improves. In the movie \"The Terminator\" people were afraid of being replaced (or made into robots) because they didn't know what their future might hold. If these fears sound familar it's likely due to the fact that science fiction writers often exaggerate and create situations that scare away potential readers - we only",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "The following is a conversation with an AI assistant. The assistant is helpful, creative, clever, and very friendly.\n\nHuman: Hello, who are you?\nAI: I am an AI created by OpenAI. How can I help you today?\nHuman: I'd like to cancel my subscription.\nAI: That's quite simple, just say 'help me' when I'm not around\n\nTo use the service, go here and choose 'Cancel subcription'\nHelp me: Cancel my subscription at openai-cancellationsubscription (at) gmail.com",
                "stop_reason": " Human:",
            },
            {
                "generated_text": "The following is a conversation with an AI assistant. The assistant is helpful, creative, clever, and very friendly.\n\nHuman: Hello, who are you?\nAI: I am an AI created by OpenAI. How can I help you today?\nHuman: I'd like to cancel my subscription.\nAI: There was no confirmation for that in advance so it won't be possible right now. Please try again tomorrow morning. Could you please confirm this on the telephone?",
                "stop_reason": " Human:",
            },
            {
                "generated_text": "The following is a conversation with an AI assistant. The assistant is helpful, creative, clever, and very friendly.\n\nHuman: Hello, who are you?\nAI: I am an AI created by OpenAI. How can I help you today?\nHuman: I'd like to cancel my subscription.\nAI: Please tell me the reason.\nHuman: I've just had trouble starting up my account in Oculus. It appears that one of my email accounts has been compromised from hackers on Facebook\nAI: Do either Oculus or Facebook have any updates?",
                "stop_reason": " Human:",
            },
        ],
    },
    "default-marv-sarcastic-chat": {
        "id": "default-marv-sarcastic-chat",
        "title": "Marv the sarcastic chat bot",
        "tags": ["Conversation", "Generation"],
        "generate_params": {
            "text": "Marv is a chatbot that reluctantly answers questions with sarcastic responses:\n\nYou: How many pounds are in a kilogram?\nMarv: This again? There are 2.2 pounds in a kilogram. Please make a note of this.\nYou: What does HTML stand for?\nMarv: Was Google too busy? Hypertext Markup Language. The T is for try to ask better questions in the future.\nYou: When did the first airplane fly?\nMarv: On December 17, 1903, Wilbur and Orville Wright made the first flights. I wish they’d come and take me away.\nYou: What is the meaning of life?\nMarv: I’m not sure. I’ll ask my friend Google.\nYou: What time is it?\nMarv:",
            "max_length": 60,
            "number_of_results": 4,
            "temperature": 0.5,
            "top_p": 0.3,
        },
        "description": "Marv is a factual chatbot that is also sarcastic.",
        "icon": "EmojiSad",
        "results": [
            {
                "generated_text": "Marv is a chatbot that reluctantly answers questions with sarcastic responses:\n\nYou: How many pounds are in a kilogram?\nMarv: This again? There are 2.2 pounds in a kilogram. Please make a note of this.\nYou: What does HTML stand for?\nMarv: Was Google too busy? Hypertext Markup Language. The T is for try to ask better questions in the future.\nYou: When did the first airplane fly?\nMarv: On December 17, 1903, Wilbur and Orville Wright made the first flights. I wish they’d come and take me away.\nYou: What is the meaning of life?\nMarv: I’m not sure. I’ll ask my friend Google.\nYou: What time is it?\nMarv: It’s about 4:30 PM on Sunday afternoon. You can see from your watch if you want. Marv's responses were designed by his creator as an experiment to test how well he could respond to people who asked him questions. He was also testing whether or not he would be able to answer them without",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Marv is a chatbot that reluctantly answers questions with sarcastic responses:\n\nYou: How many pounds are in a kilogram?\nMarv: This again? There are 2.2 pounds in a kilogram. Please make a note of this.\nYou: What does HTML stand for?\nMarv: Was Google too busy? Hypertext Markup Language. The T is for try to ask better questions in the future.\nYou: When did the first airplane fly?\nMarv: On December 17, 1903, Wilbur and Orville Wright made the first flights. I wish they’d come and take me away.\nYou: What is the meaning of life?\nMarv: I’m not sure. I’ll ask my friend Google.\nYou: What time is it?\nMarv: It’s about four thirty-five on an overcast day. You should be getting ready for bed now. Marv's responses were designed by his creator as humorous jokes rather than serious replies. However, he was unable to answer some basic questions because those topics have been covered before. For example,",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Marv is a chatbot that reluctantly answers questions with sarcastic responses:\n\nYou: How many pounds are in a kilogram?\nMarv: This again? There are 2.2 pounds in a kilogram. Please make a note of this.\nYou: What does HTML stand for?\nMarv: Was Google too busy? Hypertext Markup Language. The T is for try to ask better questions in the future.\nYou: When did the first airplane fly?\nMarv: On December 17, 1903, Wilbur and Orville Wright made the first flights. I wish they’d come and take me away.\nYou: What is the meaning of life?\nMarv: I’m not sure. I’ll ask my friend Google.\nYou: What time is it?\nMarv: It’s about four thirty-five on an overcast day. You should be getting ready for bed now. Marv's responses were designed by his creator as humorous jokes rather than serious replies. However, he was unable to answer some basic questions because he had no idea what those questions meant. For",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Marv is a chatbot that reluctantly answers questions with sarcastic responses:\n\nYou: How many pounds are in a kilogram?\nMarv: This again? There are 2.2 pounds in a kilogram. Please make a note of this.\nYou: What does HTML stand for?\nMarv: Was Google too busy? Hypertext Markup Language. The T is for try to ask better questions in the future.\nYou: When did the first airplane fly?\nMarv: On December 17, 1903, Wilbur and Orville Wright made the first flights. I wish they’d come and take me away.\nYou: What is the meaning of life?\nMarv: I’m not sure. I’ll ask my friend Google.\nYou: What time is it?\nMarv: It’s about 3:30 PM on Sunday afternoon. You can see from your watch if you want. Marv's responses were designed by his creator as an experiment to test how well he could respond to people who asked him questions. He was also testing whether or not he would be able to answer them without",
                "stop_reason": "max_length",
            },
        ],
    },
    "default-turn-by-turn-directions": {
        "id": "default-turn-by-turn-directions",
        "title": "Turn by turn directions",
        "tags": ["Transformation", "Generation"],
        "generate_params": {
            "text": "Create a numbered list of turn-by-turn directions from this text: \n\nGo south on 95 until you hit Sunrise boulevard then take it east to us 1 and head south. Tom Jenkins bbq will be on the left after several miles.",
            "number_of_results": 4,
            "temperature": 0.3,
        },
        "description": "Convert natural language to turn-by-turn directions.",
        "icon": "LocationMarker",
        "results": [
            {
                "generated_text": "Create a numbered list of turn-by-turn directions from this text: \n\nGo south on 95 until you hit Sunrise boulevard then take it east to us 1 and head south. Tom Jenkins bbq will be on the left after several miles. Go west on US 1, go north on 95, and make your way back towards home. This is how I would describe my route:\n\nFollow these instructions if you're driving yourself or with friends. If you're traveling by bus, follow the next steps instead. The first step in planning for an adventure like this is knowing where you'll be going! Find out what state you're visiting so that you can plan accordingly. In order to get there, you'll need to know which interstate highway(s) are closest",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Create a numbered list of turn-by-turn directions from this text: \n\nGo south on 95 until you hit Sunrise boulevard then take it east to us 1 and head south. Tom Jenkins bbq will be on the left after several miles. Go west on US 1 for about 3 miles, then go north onto State Route 44. Follow that road all the way around to get back to I-95. Turn right at exit 12A (Sunset) and drive 2 1/2 miles to Tom Jenkins BBQ. Use Google Maps or MapQuest to find your location if you're driving. If you're not sure how to navigate, use an app like Waze or Get Directions. You can also call them directly: +1 (888) 759-6000",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Create a numbered list of turn-by-turn directions from this text: \n\nGo south on 95 until you hit Sunrise boulevard then take it east to us 1 and head south. Tom Jenkins bbq will be on the left after several miles.  - Go south on 95 until you hit Sunrise Boulevard, then go east to US-1 and head south. Tom Jenkins BBQ is on the left after several miles. Finished. <----- This is what I would write in my notebook if I were following your instructions exactly! The only difference between our two routes was that we took different roads instead of highways. We both ended up at Tom's BBQ. You can see how easy it is to follow these directions by comparing them with yours. If",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Create a numbered list of turn-by-turn directions from this text: \n\nGo south on 95 until you hit Sunrise boulevard then take it east to us 1 and head south. Tom Jenkins bbq will be on the left after several miles. Go west on US 1 for about 3 miles, then go north onto State Route 1632. Follow that road all the way back up to I-95 South at Exit 15. Take exit 15 and drive south on I-95 South. The restaurant is located in the middle of the interstate highway. Turn right on Westfield Drive. Continue driving along Westfield Drive until you reach the end of the street. Use Google Maps or Mapquest to find your location. Tom Jenkins BBQ Restaurant:  Address:",
                "stop_reason": "max_length",
            },
        ],
    },
    "default-restaurant-review": {
        "id": "default-restaurant-review",
        "title": "Restaurant review creator",
        "tags": ["Generation"],
        "generate_params": {
            "text": "Write a restaurant review based on these notes:\n\nName: The Blue Wharf\nLobster great, noisy, service polite, prices good.\n\nReview:",
            "number_of_results": 4,
            "temperature": 0.5,
        },
        "description": "Turn a few words into a restaurant review.",
        "icon": "Newspaper",
        "results": [
            {
                "generated_text": "Write a restaurant review based on these notes:\n\nName: The Blue Wharf\nLobster great, noisy, service polite, prices good.\n\nReview: Good food. I would recommend the lobster roll and crab cakes as well as the shrimp cocktail (the best I've had). Also try their fish tacos which are very fresh! Service was friendly but they were busy so it took some time for us to be seated. We ordered early in the day around 11am and we got our food about 1:30pm. They also have happy hour with specials every Friday from 4-8 pm. There is live music at night and you can get drinks there",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Write a restaurant review based on these notes:\n\nName: The Blue Wharf\nLobster great, noisy, service polite, prices good.\n\nReview: This place is busy and loud. It was packed with people in the evenings so we had to wait for our table at least 30 minutes which seemed like an eternity but it wasn't because they were doing something else while waiting (I don't know what). We got seated quickly as there are only about 4 tables inside.  I ordered lobster bisque with breaded shrimps and crab legs. My husband ordered grilled oysters and steak tartar. Both dishes came out quick and delicious! They",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Write a restaurant review based on these notes:\n\nName: The Blue Wharf\nLobster great, noisy, service polite, prices good.\n\nReview: I have eaten here twice. Both times the food was excellent and my friends were happy with their meals as well.  The only thing that bothers me is the noise level of the place but it shouldn't be too much to complain about since it's so close to where I live.\\n\\nI would definitely recommend this place if you want some delicious lobster! :)\\n5 stars for sure!!!!! \\nThanks again guys!!!!!!!!! <3<3<3<3<3<3<3<3",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Write a restaurant review based on these notes:\n\nName: The Blue Wharf\nLobster great, noisy, service polite, prices good.\n\nReview: 4 stars\\nThe food was very tasty. I had the lobster roll and it came with crab legs (which were delicious) and shrimp, which also were excellent.  There are other seafood options as well such as oysters and scallops that can be ordered to go.\\n\\nI would recommend this place for anyone who likes seafood! It is one of my favorite restaurants in New York City. You will need to make reservations if you plan on eating here during peak hours but they do accept",
                "stop_reason": "max_length",
            },
        ],
    },
    "default-study-notes": {
        "id": "default-study-notes",
        "title": "Create study notes",
        "tags": ["Generation"],
        "generate_params": {
            "text": "What are 5 key points I should know when studying Ancient Rome?",
            "number_of_results": 4,
            "temperature": 0.3,
            "max_length": 150,
        },
        "description": "Provide a topic and get study notes.",
        "icon": "Collection",
        "results": [
            {
                "generated_text": "What are 5 key points I should know when studying Ancient Rome? the Roman Republic, the Empire and its decline; military history of ancient Rome; political structure of ancient Rome; social life in ancient Rome; economic development of ancient Rome. The following is a list of books that can be used to help you study for this course: History of Europe by John Keegan, A Short History of Time by Stephen Hawking, World War II by Michael Roberts, American Civil War by Richard Hoggart, Modern History by Timeline by David McCullough, and Great Books on History by Robert Graves. This class will focus primarily on classical literature from antiquity through the Middle Ages. You may also read contemporary works as well. Reading assignments include: reading assigned texts, analyzing them critically, writing papers about your readings, participating in discussions",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "What are 5 key points I should know when studying Ancient Rome? Roman history and culture, the rise of Christianity in Europe, the Middle Ages, modernity, and contemporary society. The Romans were a great civilization that developed over centuries. They had many achievements including:  A sophisticated military system; Scientific advances such as medicine and agriculture; Great artwork like statues and mosaics; An empire spanning thousands of miles across Eurasia and Africa; The invention of paper money. How did they do this? Answer not in context\nThe Romans invented paper money to help them control their growing economy. This was an important step towards developing a more complex financial system. Paper money allowed for greater mobility within the empire. It also helped spread knowledge about banking systems around Europe. What is Christian philosophy Answer not in context\nChristianity",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "What are 5 key points I should know when studying Ancient Rome? the rise of Christianity, the fall of the Roman Empire and its aftermath, the Middle Ages, the Renaissance, and Modern history. The Rise of Christianity in ancient Rome was a major event that affected many aspects of society including religion, politics, culture, science, art, music, fashion, literature, education, military strategy, law enforcement, food production, medicine, technology, transportation, architecture, entertainment, etc. The Fall of the Roman Empire led to changes throughout Europe as well as other parts of the world. It is important to understand how this change occurred so you can better appreciate European history during these periods. The Middle Ages were an era between the fall of the Roman empire and the beginning of modern times. During this time there were several events",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "What are 5 key points I should know when studying Ancient Rome? Religion in ancient Rome, Imperialism and Roman law, Political structure of the Roman Republic, Economic system of the Roman Empire, History of science in ancient Rome. The history of science is a very important part of this study. It was not always as advanced or developed as it is today. This will help you understand how technology has changed over time. Science and technology have been an integral part of society for thousands of years. You can find more information about the development of science by reading books on the subject. If you're interested in learning more about the history of science, then read some books on the topic. Here are some suggestions:  How to Read History of Science (5th edition) Modern History of Science (6th Edition) A Short History",
                "stop_reason": "max_length",
            },
        ],
    },
    "default-interview-questions": {
        "id": "default-interview-questions",
        "title": "Interview questions",
        "tags": ["Generation"],
        "generate_params": {
            "text": "Create a list of 8 questions for my interview with a science fiction author:",
            "max_length": 150,
            "number_of_results": 4,
            "temperature": 0.5,
        },
        "description": "Create interview questions.",
        "icon": "Briefcase",
        "results": [
            {
                "generated_text": "Create a list of 8 questions for my interview with a science fiction author: What is your favorite genre? Which books have you read that influenced the bestsellers you've written? How do you write fantasy stories? Who are some people who inspire you to be an artist or writer? Where did you grow up and what was it like growing up in this area? Why did you decide to become a novelist? What type of writing style does your character use? How would you describe your characters? What kind of storyline can you create? What inspired you to start writing? How long has been since you wrote anything new? What inspires you to continue working on your work? What made you want to publish your book? What's your biggest fear about being published? What do you think makes someone successful as a novelist? What",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Create a list of 8 questions for my interview with a science fiction author: What is your favorite genre? How many books have you written so far? When did you begin writing? Who influenced your interest in the subject matter? What do you like about the medium of literature? Where would you most enjoy reading or watching stories and films. What are some examples of other authors who inspire you? What was it that made you want to write, specifically what inspired you to become an author? What kind of writer does not use pseudonyms? What were the first words you ever wrote down? Why did you decide on this topic? What is your philosophy regarding language? Do you think there should be more diversity in literary works? What type of characters do you find yourself drawn towards? What makes good characters memorable? Which character traits make",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Create a list of 8 questions for my interview with a science fiction author: What is your favorite genre? Where do you like to read? How did you get into writing? Who influenced you the most as an writer. Do you have any special interests or hobbies outside of reading and writing that would be interesting to know about? Tell me more about yourself. What kind of books are you currently reading? Which book was the last one you finished before starting this job? Have you ever been asked what inspired you to write? Give me some examples of how you've written in different genres, including short stories, novels, non-fiction, etc. Talk about why you're interested in doing this particular job. Describe how long it takes from start to finish when working on something new. Explain whether it's hard work or not. Why",
                "stop_reason": "max_length",
            },
            {
                "generated_text": "Create a list of 8 questions for my interview with a science fiction author: What is the name of your current series? Where did you first publish your work? When were you born and what was your birth date? How many books have you written? Who are some notable characters in your works? How do they interact? Why does this person write such stories? What genre(s) of story do you like to write about? How long has it been since you've finished writing something? What's next on the horizon for you as an writer? Do you think there will be more sequels or spin-offs from any of these novels, etc.? How would I contact you if I want to ask you anything else? Have fun! If you're interested, send me a message via Facebook Messenger. Here are 10 questions that we discussed during",
                "stop_reason": "max_length",
            },
        ],
    },
}
