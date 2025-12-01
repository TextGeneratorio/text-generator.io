import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


def main():
    """Run a simple prompt using the SmolLM3 model."""
    model_name = "HuggingFaceTB/SmolLM3-3B"
    device = "cuda" if torch.cuda.is_available() else "cpu"

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name).to(device)

    prompt = "Give me a brief explanation of gravity in simple terms."
    messages = [{"role": "user", "content": prompt}]
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    model_inputs = tokenizer([text], return_tensors="pt").to(device)

    generated_ids = model.generate(**model_inputs, max_new_tokens=128)
    output_ids = generated_ids[0][len(model_inputs.input_ids[0]) :]
    print(tokenizer.decode(output_ids, skip_special_tokens=True))


if __name__ == "__main__":
    main()
