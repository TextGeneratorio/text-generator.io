import requests
import os

headers = {"secret": os.getenv("TEXTGENERATOR_API_KEY")}

data = {
    "text": "Consider this passage:\n\nComedy @ the Carlson Google Calendar ICS; BUY TICKETS NOW View Event → Jun. 10. to Jun 11. tour. POINT PLEASANT, NJ | Uncle Vinnie's Comedy Club ... JIM THORPE, PA | Mauch Chunk Opera House. Friday, June 3, 2022; 7:00 PM 10:00 PM; Mauch Chunk Opera House Google Calendar ICS; BUY TICKETS NOW\n\nQ: Is this about {topic}, yes or no?\nA:\n",
    "number_of_results": 3,
    "repetition_penalty": 1.17,
    "top_p": 0.38,
    "max_length": 99
}

response = requests.post(
   # "https://api.text-generator.io/api/v1/generate",
   # "http://localhost:8000/api/v1/generate",
   "http://127.0.0.1:8000/api/v1/generate",
   json=data,
   headers=headers
)

json_response = response.json()

for generation in json_response:
    generated_text = generation["generated_text"][len(data['text']):]
    print(generated_text)
    assert generation["generated_text"].startswith(data["text"])
