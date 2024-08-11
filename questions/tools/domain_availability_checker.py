import gradio as gr
import subprocess
from loguru import logger
import requests
import re

def is_domain_name(domain):
    return re.match(r'^[a-zA-Z0-9-]+\.[a-zA-Z0-9-]+$', domain) is not None

def check_domain_availability(domain):
    command = f"whois {domain} | grep 'This query returned 0 objects'"
    whois_output = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    return "Available" if whois_output.returncode == 0 else "Taken"

def generate_domains(business_name, api_key):
    headers = {"secret": api_key, "Content-Type": "application/json"}
    input_text = f"###\nName: {business_name}\nDomains available:\n"
    data = {
        "text": input_text,
        "stop_sequences": ["\\n\\n", "A:", "###", "/"],
        "number_of_results": 1,
        "max_length": 30,
        "max_sentences": 10,
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
    logger.info(f"Response from Text-Generator.io: {res.text}")

    json_response = res.json()
    domains = set()

    for generation in json_response:
        generated_text = generation["generated_text"][len(input_text):]
        current_domains = re.split(r'[,\n]', generated_text)
        for domain in current_domains:
            if is_domain_name(domain):
                domains.add(domain)

    return list(domains)
import asyncio
from questions.ai_wrapper import generate_with_claude

async def generate_domains_new(business_name, current_ideas):
    prompt = f"""Generate a list of 10 creative domain name suggestions for a business named "{business_name}". 
    Each domain name should be on a new line and include only the domain name itself (e.g., example.com).
    Be creative and consider different TLDs (Top Level Domains) beyond just .com.
    Ensure each suggestion is a valid domain name format."""

    response = await generate_with_claude(prompt, prefill=current_ideas)
    
    # Process the response to extract valid domain names
    domains = set()
    for line in response.split('\n'):
        domain = line.strip()
        if is_domain_name(domain):
            domains.add(domain)

    return list(domains)

# Update the create_domain_spreadsheet function to use generate_domains_new
async def create_domain_spreadsheet_new(business_name, current_ideas):
    domains = await generate_domains_new(business_name, current_ideas)
    logger.info(f"Generated {len(domains)} domains for {business_name}")
    logger.info(f"Domains: {domains}")
    results = []
    for domain in domains:
        availability = check_domain_availability(domain)
        results.append([domain, availability])
    
    return results

# Update the Gradio interface to use the new async function
iface = gr.Interface(
    fn=lambda business_name, current_ideas: asyncio.run(create_domain_spreadsheet_new(business_name, current_ideas)),
    inputs=[
        gr.Textbox(label="Business Description"),
        gr.Textbox(label="Current Domain Ideas", placeholder="Enter your current domain name ideas, on one line")
    ],
    outputs=gr.Dataframe(headers=["Domain", "Availability"]),
    title="Domain Availability Checker",
    description="Enter your business description and any current domain name ideas on new lines, to generate names + check domain availability."
)


if __name__ == "__main__":
    iface.launch(server_port=7652)