import dataclasses

from starlette.testclient import TestClient

from questions.inference_server.inference_server import app
from questions.post_process_results import post_process_results
from questions.models import GenerateParams, create_generate_params
from sellerinfo import TEXT_GENERATOR_SECRET

client = TestClient(app)


def test_hi_suggestion():
    text = """Hi hows it"""
    response = client.post("/api/v1/generate", json={"text": text})
    assert response.status_code == 200
    completions = response.json()
    print(completions)


def test_stopping_max_length():
    text = """Hi hows it"""
    generate_params = create_generate_params(text=text, max_length=1)
    response = client.post("/api/v1/generate", json=generate_params.__dict__)
    assert response.status_code == 200
    completions = response.json()
    print(completions)


def test_stopping_sentences():
    text = """Hi hows it"""
    generate_params = create_generate_params(text=text, max_sentences=1)
    response = client.post("/api/v1/generate", json=generate_params.__dict__)
    assert response.status_code == 200
    completions = response.json()
    print(completions)
    generate_params = create_generate_params(text=text, max_sentences=1)
    response = client.post("/api/v1/generate", json=generate_params.__dict__)
    assert response.status_code == 200
    completions = response.json()
    print(completions)

def test_non_then_chats():
    {
        "text": "ava: Hi i'm ava i'm thinking that we could talk ? \ndan:",
        "number_of_results": 1,
        "max_length": 100,
        "min_length": 1,
        "max_sentences": 0,
        "min_probability": 0,
        "stop_sequences": [],
        "top_p": 0.9,
        "top_k": 40,
        "temperature": 0.7,
        "seed": 0,
        "model": "chat",
        "repetition_penalty": 1.2
    }
    text = """ava: Hi i'm ava i'm thinking that we could talk ? \ndan:"""
    generate_params = create_generate_params(text=text, max_sentences=1)
    response = client.post("/api/v1/generate", json=generate_params.__dict__, headers={
        "secret": TEXT_GENERATOR_SECRET,
        "X-Rapid-API-Key": 'fake'
    })
    assert response.status_code == 200
    completions = response.json()
    print(completions)


    generate_params = create_generate_params(text=text, max_sentences=1)
    generate_params.model = "chat"

    response = client.post("/api/v1/generate", json=generate_params.__dict__, headers={
        "secret": TEXT_GENERATOR_SECRET,
        "X-Rapid-API-Key": 'fake'
    })
    assert response.status_code == 200
    completions = response.json()
    print(completions)

    #toggle back?
    generate_params = create_generate_params(text=text, max_sentences=1)
    generate_params.model = "chat"

    response = client.post("/api/v1/generate", json=generate_params.__dict__, headers={
        "secret": TEXT_GENERATOR_SECRET,
        "X-Rapid-API-Key": 'fake'
    })
    assert response.status_code == 200
    completions = response.json()
    print(completions)


def test_speak_inf_speak():
    client.post('/api/v1/generate_speech', json={"text": "hi"}, headers={
        "secret": TEXT_GENERATOR_SECRET,
        "X-Rapid-API-Key": 'fake'
    })

    text = """ava: Hi i'm ava i'm thinking that we could talk ? \ndan:"""
    generate_params = create_generate_params(text=text, max_sentences=1, model="chat")
    response = client.post("/api/v1/generate", json=generate_params.__dict__, headers={
        "secret": TEXT_GENERATOR_SECRET,
        "X-Rapid-API-Key": 'fake'
    })
    assert response.status_code == 200
    completions = response.json()
    print(completions)

    response = client.post('/api/v1/generate_speech', json={"text": "hi"}, headers={
        "secret": TEXT_GENERATOR_SECRET,
        "X-Rapid-API-Key": 'fake'
    })
    assert response.status_code == 200
