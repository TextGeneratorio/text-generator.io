import requests
import os
import pytest

pytestmark = pytest.mark.integration

from sellerinfo import TEXT_GENERATOR_SECRET

headers = {"secret": TEXT_GENERATOR_SECRET}

data = {
    "text": "salaries_clean_df.columns\n\nIndex(['salary_id', 'employer_name', 'location_name', 'location_state',\n       'location_country', 'location_latitude', 'location_longitude',\n       'job_title', 'job_title_category', 'job_title_rank',\n       'total_experience_years', 'employer_experience_years',\n       'annual_base_pay', 'signing_bonus', 'annual_bonus', 'stock_value_bonus',\n       'comments', 'submitted_at'],\n      dtype='object')\n#Who has the highest salary\nx_column = '",
    "number_of_results": 1,
    "max_length": 100,
    "max_sentences": 1,
    "min_probability": 0,
    "stop_sequences": [],
    "top_p": 0.5,
    "top_k": 40,
    "temperature": 0.9,
    "repetition_penalty": 1.17,
    "seed": 0,
}
# another bad cuttoff example
prompt = """df.columns
Index(['id', 'currency_pair', 'last', 'lowestAsk', 'highestBid',
       'percentChange', 'baseVolume', 'quoteVolume', 'date'],
      dtype='object')
#show a bar chart of salary
plot_x_column_name = '"""
data["text"] = prompt

response = requests.post(
    # "https://api.text-generator.io/api/v1/generate",
    "http://127.0.0.1:8000/api/v1/generate",
    # "http://127.0.0.1:3004/api/v1/generate", # this isnt the right place
    json=data,
    headers=headers,
)

json_response = response.json()

for generation in json_response:
    generated_text = generation["generated_text"][len(data["text"]) :]
    print(generated_text)
