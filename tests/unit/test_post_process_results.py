from transformers import AutoTokenizer

from questions.models import GenerateParams
from questions.post_process_results import post_process_results


def test_post_process_results():
    generate_params = GenerateParams(
        text='Hi hows it',
        number_of_results=1,
        max_length=100,
        min_length=1,
        max_sentences=1,
        min_probability=0.0,
        stop_sequences=[],
        top_p=0.9,
        top_k=40,
        temperature=0.7,
        seed=None
    )
    decoded_results = ['Hi hows it going?\n\nHope']
    input_text = 'Hi hows it'
    post_processed = post_process_results(decoded_results, generate_params, input_text, input_text)
    assert post_processed == ['Hi hows it going?\n']


def test_post_process_results_special():
    generate_params = GenerateParams(
        text='Hi hows it',
        number_of_results=1,
        max_length=100,
        min_length=1,
        max_sentences=1,
        min_probability=0.0,
        stop_sequences=["?"],
        top_p=0.9,
        top_k=40,
        temperature=0.7,
        seed=None
    )
    decoded_results = ['Hi hows it going?']
    input_text = 'Hi hows it'
    post_processed = post_process_results(decoded_results, generate_params, input_text, input_text)
    assert post_processed == ['Hi hows it going']


def test_post_process_results_special_nz():
    generate_params = GenerateParams(
        text='What is the weather today in Wellington New Zealand?',
        number_of_results=1,
        max_length=100,
        min_length=1,
        max_sentences=1,
        min_probability=0.0,
        stop_sequences=['?', '!', '.'],
        top_p=0.9,
        top_k=40,
        temperature=0.7,
        seed=42,
    )
    decoded_results = ['What is the weather today in Wellington New Zealand? The answer is a little surprising.']
    input_text = 'What is the weather today in Wellington New Zealand?'
    post_processed = post_process_results(decoded_results, generate_params, input_text, input_text)
    assert post_processed == ['What is the weather today in Wellington New Zealand? The answer is a little surprising']


def test_post_process_results_newlines():
    generate_params = GenerateParams(
        text='What is the weather today in Wellington New Zealand?',
        number_of_results=1,
        max_length=100,
        min_length=1,
        max_sentences=1,
        min_probability=0.0,
        stop_sequences=['?', '!', '.'],
        top_p=0.9,
        top_k=40,
        temperature=0.7,
        seed=42,
    )
    decoded_results = ['What is the weather today in Wellington New Zealand? \nThe answer \nis a little surprising.']
    input_text = 'What is the weather today in Wellington New Zealand? '
    post_processed = post_process_results(decoded_results, generate_params, input_text, input_text)
    assert post_processed == ['What is the weather today in Wellington New Zealand? The answer is a little surprising']
