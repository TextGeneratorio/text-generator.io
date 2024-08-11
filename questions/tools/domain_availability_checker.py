import gradio as gr
import subprocess
import requests
import re

def is_domain_name(domain):
    return re.match(r'^[a-zA-Z0-9-]+\.[a-zA-Z0-9-]+$', domain) is not None

def check_domain_availability(domain):
    command = f"whois {domain} | grep 'This query returned 0 objects'"
    whois_output = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    return "Available" if whois_output.returncode == 0 else "Taken"

def generate_domains(business_name, api_key):
    headers = {"secret": api_key}
    input_text = f"###\nName: {business_name}\nDomains available:\n"
    data = {
        "text": input_text,
        "stop_sequences": ["\\n\\n", "A:", "###", "/"],
        "number_of_results": 40,
        "max_length": 30,
        "max_sentences": 4,
        "min_probability": 0,
        "top_p": 1,
        "top_k": 60,
        "temperature": 0.7,
        "repetition_penalty": 1.17,
        "seed": 0
    }

    res = requests.post(
        "https://api.text-generator.io/api/v1/generate",
        json=data,
        headers=headers
    )

    json_response = res.json()
    domains = set()

    for generation in json_response:
        generated_text = generation["generated_text"][len(input_text):]
        current_domains = re.split(r'[,\n]', generated_text)
        for domain in current_domains:
            if is_domain_name(domain):
                domains.add(domain)

    return list(domains)

def create_domain_spreadsheet(business_name, api_key):
    domains = generate_domains(business_name, api_key)
    results = []
    for domain in domains:
        availability = check_domain_availability(domain)
        results.append([domain, availability])
    
    return results

iface = gr.Interface(
    fn=create_domain_spreadsheet,
    inputs=[
        gr.Textbox(label="Business Name"),
        gr.Textbox(label="Text-Generator.io API Key", type="password")
    ],
    outputs=gr.Dataframe(headers=["Domain", "Availability"]),
    title="Domain Availability Checker",
    description="Enter your business name and API key to generate and check domain availability."
)

if __name__ == "__main__":
    iface.launch()