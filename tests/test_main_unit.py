import pytest
from fastapi.testclient import TestClient

from questions.inference_server.inference_server import app, generate_route, openai_route
from questions.models import create_generate_params, GenerateParams, OpenaiParams

client = TestClient(app)


@pytest.mark.asyncio
async def test_stopping_max_length():
    text = """Hi hows it"""
    generate_params = create_generate_params(text=text, max_length=1)
    response = await generate_route(generate_params)
    completions = response[0]["generated_text"]
    print(completions)


@pytest.mark.asyncio
async def test_stopping_sentences():
    text = """Hi hows it"""
    generate_params = create_generate_params(text=text, max_sentences=1)
    response = await generate_route(generate_params)
    completions = response[0]["generated_text"]
    print(completions)
    generate_params = create_generate_params(text=text, max_sentences=1)
    response = await generate_route(generate_params)
    completions = response[0]["generated_text"]
    print(completions)


@pytest.mark.asyncio
async def test_stopping_three_sentences():
    text = """Hi hows it"""
    generate_params = create_generate_params(text=text, max_sentences=1)
    response = await generate_route(generate_params)
    print(response)
    generate_params = create_generate_params(text=text, max_sentences=3)
    response_three = await generate_route(generate_params)
    print(response_three)

    assert len(response_three[0]["generated_text"]) > len(response[0]["generated_text"])


# @pytest.mark.asyncio
# async def test_stopping_three_results():
#     text = """Hi hows it"""
#     generate_params = create_generate_params(text=text, number_of_results=3)
#     response = await generate_route(generate_params)
#     completions = response
#     print(completions)
#     assert len(completions) == 3


@pytest.mark.asyncio
async def test_stopping_min_prob():
    text = """Hi hows it"""
    generate_params = create_generate_params(text=text, min_probability=0.9)
    response = await generate_route(generate_params)
    completions = response
    print(completions)
    assert len(completions) == 1
    assert completions[0]["generated_text"] == "Hi hows it going?"
    assert completions[0]["stop_reason"] == "min_probability"


@pytest.mark.asyncio
async def test_chopping_off_python():
    text = """Converting text to a bash command:\nExample: where is a file ending with .png in my home dir\nOutput: find ~ -name \"*.png\"\nExample: run a python http server\nOutput:"""
    generate_params = create_generate_params(text=text, min_probability=0.9)
    response = await generate_route(generate_params)
    completions = response
    print(completions)
    assert len(completions) == 1
    assert completions[0]["generated_text"][len(text):] == " python"


# @pytest.mark.asyncio
# async def test_stopping_long_inference():
#     text = """My dearest love,"""
#     generate_params = create_generate_params(text=text, max_length=3000)
#     response = await generate_route(generate_params)
#     completions = response[0]["generated_text
#     print(completions)
#     assert len(completions) == 3
#
#
# @pytest.mark.asyncio
# async def test_stopping_long_input_inference():
#     text = long_text
#     generate_params = create_generate_params(text=text, max_length=3000)
#     response = await generate_route(generate_params)
#     completions = response[0]["generated_text
#     print(completions)
#     assert len(completions) == 3
#
#
# @pytest.mark.asyncio
# async def test_stopping_long_input():
#     text = long_text
#     generate_params = create_generate_params(text=text, max_length=30)
#     response = await generate_route(generate_params)
#     completions = response[0]["generated_text
#     print(completions)
#     assert len(completions) == 1


@pytest.mark.asyncio
async def test_stopping_sequences():
    text = """
Human: Hi whats for dinner.
Robot: I'm a robot.
Human: """
    generate_params = create_generate_params(text=text, stop_sequences=["Human:", "Robot:"])
    response = await generate_route(generate_params)
    text = response[0]["generated_text"]
    print(text)
    assert len(text) == 1


@pytest.mark.asyncio
async def test_defaults():
    text = "Hello world, How are "
    generate_params = create_generate_params(
        **{
            "text": text,
            "number_of_results": 1,
            "max_length": 100,
            "max_sentences": 0,
            "min_probability": 0,
            "stop_sequences": ["?", "!", "."],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
        }
    )
    response = await generate_route(generate_params)
    completions = response
    print(completions)
    assert len(completions) == 1
    assert (
        "?" not in completions[0]["generated_text"][len(text) :]
        and "!" not in completions[0]["generated_text"][len(text) :]
        and "." not in completions[0]["generated_text"][len(text) :]
    )
    assert "  " not in completions[0]["generated_text"]  # no double space issues


@pytest.mark.asyncio
async def test_two_results_defaults():
    text = "Hello world! How are you? I"
    generate_params = create_generate_params(
        **{
            "text": text,
            "number_of_results": 2,
            "max_length": 100,
            "max_sentences": 0,
            "min_probability": 0,
            "stop_sequences": ["?", "!", "."],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
        }
    )
    response = await generate_route(generate_params)
    completions = response
    print(completions)
    assert len(completions) == 2
    assert (
        "?" not in completions[0]["generated_text"][len(text) :]
        and "!" not in completions[0]["generated_text"][len(text) :]
        and "." not in completions[0]["generated_text"][len(text) :]
    )
    assert "  " not in completions[0]["generated_text"]  # no double space issues


@pytest.mark.asyncio
async def test_defaults_double_space():
    generate_params = create_generate_params(
        **{
            "text": "Hello world, How are you ",
            "number_of_results": 1,
            "max_length": 1,  # this is going to stop straight away
            "max_sentences": 0,
            "min_probability": 0,
            "stop_sequences": ["?", "!", "."],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
        }
    )
    response = await generate_route(generate_params)
    completions = response
    print(completions)
    assert len(completions) == 1
    assert (
        "?" not in completions[0]["generated_text"]
        and "!" not in completions[0]["generated_text"]
        and "." not in completions[0]["generated_text"]
    )
    assert "  " not in completions[0]["generated_text"]


@pytest.mark.asyncio
async def test_defaults_no_stop_too_soon():
    text = "Hello world, How are you "
    generate_params = create_generate_params(
        **{
            "text": text,
            "number_of_results": 1,
            "max_sentences": 0,
            "min_probability": 0,
            "stop_sequences": ["?", "!", "."],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
        }
    )
    response = await generate_route(generate_params)
    completions = response
    print(completions)
    assert len(completions) == 1
    assert len(completions[0]["generated_text"]) > len(text) + 10
    assert (
        "?" not in completions[0]["generated_text"]
        and "!" not in completions[0]["generated_text"]
        and "." not in completions[0]["generated_text"]
    )


@pytest.mark.asyncio
async def test_long_text_no_stop_too_soon():
    text = 'Adam is polite happy funny\ni can respond yes no or however i feel like\n\nAdam: Lets play a game, i think of something  mythology, you have to guess what it is. You can guess as many times as you want. if i say "your correct!" then you win\n\n\nHuman: is it cool?\nAdam: I would like to guess.\n\nHuman: is it cool?\nAdam: I would like to guess.\n\nHuman: is it hot?\nAdam: I\nHuman: is that a yes?\nAdam: I\nHuman: is it 32\nAdam: '
    generate_params = create_generate_params(
        **{
            "text": text,
            "number_of_results": 1,
            "max_sentences": 1,
            "min_probability": 0,
            "stop_sequences": ["?", "!", "."],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
        }
    )
    response = await generate_route(generate_params)
    completions = response
    print(completions)
    assert len(completions) == 1
    assert len(completions[0]["generated_text"]) > len(text) + 10


@pytest.mark.asyncio
async def test_defaults_no_stop_too_soon_():
    text = "What is the weather today in Wellington New Zealand?"
    generate_params = create_generate_params(
        **{
            "text": text,
            "number_of_results": 1,
            "max_sentences": 1,
            "min_probability": 0,
            "stop_sequences": ["?", "!", "."],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
        }
    )
    response = await generate_route(generate_params)
    completions = response
    print(completions)
    assert len(completions) == 1
    assert len(completions[0]["generated_text"]) > len(text) + 5
    assert (
        "?" not in completions[0]["generated_text"][len(text) :]
        and "!" not in completions[0]["generated_text"][len(text) :]
        and "." not in completions[0]["generated_text"][len(text) :]
    )


@pytest.mark.asyncio
async def test_long_input_extends():
    text = "Adam: Lets play a funny game, i think of something  animals, you have to guess what it is. You can guess as many times as you want. if i say \"your correct!\" then you win\nJohn: hey hows it going\nAdam: i got an idea\nJohn: what is it\nAdam: lets play together\nJohn: play what game\nAdam: i don't know any animal\nJohn: what about a cat\nAdam: i will do the last part and you just try my best to guess whats he gonna say\nJohn: what are you gonna say\nAdam: i got an idea of what we're gonna be doing\nJohn: what is that\nAdam: i have to wait until i get a better idea\nJohn: u have a better idea now?\nAdam: you have a better idea of what we're gonna be playing\nJohn: we will play cat and mouse\nAdam: we have to wait for the question.\nJohn: question is 10=10 what is the answer?\nAdam: i like the idea of him asking us the question\nJohn: 10+10= ?\nAdam: i wanna watch the whole game\nJohn: 10+10=\nAdam: i'm gonna put your question first\nJohn: 10+10=\nAdam: i got this why are you not in a good mood right now\nJohn: i'm depressed/lost job\nAdam:"
    generate_params = create_generate_params(
        **{
            "text": text,
            "number_of_results": 1,
            "max_sentences": 1,
            "max_length": 1,
            "min_probability": 0,
            "stop_sequences": ["?", "!", "."],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
        }
    )
    response = await generate_route(generate_params)
    completions = response
    print(completions)
    assert len(completions) == 1
    assert len(completions[0]["generated_text"]) > len(text) + 1


@pytest.mark.asyncio
async def test_openai_mapping_n_echo():
    text = 'Respond in JSON as if it were the result of a Google search.\nThe results should be informative, relevant, interesting, with 150 to 400 letters.\n"""\nSearch: Chess\n\n{"title": "What is Chess?","text": "Chess is a board game for two opponents in which each player has 16 movable pieces that are placed on a board, divided into 64 squares or squares. In its competitive version, it is considered as a sport, although nowadays it clearly has a social, educational and therapeutic dimension ..."}\n\n{"title": "How to play Chess (rules)","text": "The rules of chess are not as complicated as they seem. More and more educational centers are paying special attention to chess for children. A game that improves creativity, enhances memory, increases reading speed and helps to solve problems, among other benefits ..."}\n"""\nSearch: hey\n\n{'
    generate_params = OpenaiParams(
        **{
            "prompt": text,
            "max_tokens": 10,
            "echo": True,
            "temperature": 1,
            "top_p": 1,
            "presence_penalty": 0,
            "frequency_penalty": 2,
            "best_of": 1,
            "n": 2,
            "stream": False,
            "stop": ['"""'],
        }
    )
    response = await openai_route("engine", generate_params)
    print(response)
    assert len(response.choices) == 2
    assert response.choices[0]["generated_text"] > len(text) + 1


@pytest.mark.asyncio
async def test_openai_mapping():
    text = 'Respond in JSON as if it were the result of a Google search.\nThe results should be informative, relevant, interesting, with 150 to 400 letters.\n"""\nSearch: Chess\n\n{"title": "What is Chess?","text": "Chess is a board game for two opponents in which each player has 16 movable pieces that are placed on a board, divided into 64 squares or squares. In its competitive version, it is considered as a sport, although nowadays it clearly has a social, educational and therapeutic dimension ..."}\n\n{"title": "How to play Chess (rules)","text": "The rules of chess are not as complicated as they seem. More and more educational centers are paying special attention to chess for children. A game that improves creativity, enhances memory, increases reading speed and helps to solve problems, among other benefits ..."}\n"""\nSearch: hey\n\n{'
    generate_params = OpenaiParams(
        **{
            "prompt": text,
            "max_tokens": 10,
            "echo": False,
            "temperature": 1,
            "top_p": 1,
            "presence_penalty": 0,
            "frequency_penalty": 2,
            "best_of": 1,
            "n": 2,
            "stream": False,
            "stop": ['"""'],
        }
    )
    response = await openai_route("engine", generate_params)
    print(response)
    assert len(response.choices) == 2
    assert response.choices[0]["generated_text"] < len(text) + 1


@pytest.mark.asyncio
async def test_long_gen_code_explain():
    text = "Explain this code:\n\nclass Enamel extends HTMLElement {\n  attemptPolyfillDSD() {\n    const dsd = this.querySelector('template[shadowroot]');\n\n    if (dsd?.content) {\n      const mode = dsd.getAttribute('shadowroot');\n      this.attachShadow({ mode });\n      this.shadowRoot.appendChild(dsd.content);\n\n      dsd.remove();\n\n      return true;\n    }\n\n    return false;\n  }\n\n  connectedCallback() {\n    if (\n      !HTMLTemplateElement.prototype.hasOwnProperty('shadowRoot') &&\n      !this.attemptPolyfillDSD()\n    ) {\n      const _observer = new MutationObserver(() => {\n        if (this.attemptPolyfillDSD()) {\n          _observer.disconnect();\n        }\n      });\n\n      _observer.observe(this, {\n        childList: true,\n      });\n    }\n  }\n}\n\nexport default Enamel;\n"
    generate_params = GenerateParams(
        **{
            "text": text,
            "max_length": 40
        }
    )
    response = await generate_route(generate_params)
    print(response)

    assert len(response[0]["generated_text"]) > len(text) + 1

@pytest.mark.asyncio
async def test_should():
    text = "hey i think that we sh"
    generate_params = GenerateParams(
        **{
            "text": text,
            "max_length": 40
        }
    )
    response = await generate_route(generate_params)
    print(response)
    assert len(response[0]["generated_text"]) > len(text) + 1
    assert response[0]["generated_text"].startswith("hey i think that we should")
