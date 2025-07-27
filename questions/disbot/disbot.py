import os

import discord
from discord.ext import commands

import sellerinfo

bot = commands.Bot(
    command_prefix="/",  # Change to desired prefix
    case_insensitive=True,  # Commands aren't case-sensitive
    intents=discord.Intents.all(),  # Subscribe to all intents: https://discordpy.readthedocs.io/en/latest/intents.html
)

bot.author_id = 487258918465306634  # Change to your discord id!!!


@bot.event
async def on_ready():  # When the bot is ready
    await bot.tree.sync()
    print("Hello Discord World from Text-generator.io")
    print(bot.user)  # Prints the bot's username and identifier

import requests

headers = {"secret": "7C2JbFYUdEAGXSbO2fb0ATl0tacgEAKu"}

data = {
    "text": "in 2022 the stock market has been expected to reach a record high.",
    "number_of_results": 1,
    "max_length": 100,
    "max_sentences": 1,
    "min_probability": 0,
    "stop_sequences": [],
    "top_p": 0.9,
    "top_k": 40,
    "temperature": 0.7,
    "repetition_penalty": 1.17,
    "seed": 0
}


def get_text(prompt):
    data["text"] = prompt
    input_len = len(data['text'])

    response = requests.post("https://api.text-generator.io/api/v1/generate", headers=headers, json=data)

    json_response = response.json()

    for generation in json_response:
        # print(generation
        #       )
        # print(generation["generated_text"])
        generated_text = generation["generated_text"][input_len:]
        return generated_text


@bot.tree.command(name="textgen", description="Generate text from a prompt")
async def textgen(interation: discord.Interaction, prompt: str):
    await interation.response.defer()
    await interation.followup.send(get_text(prompt + "\n"))
    # await interation.response.send_message(get_text(prompt + "\n"))

    # await ctx.send(get_text(prompt + ".\n"))


extensions = [
    'cogs.cog_example'  # Same name as it would be if you were importing it
]

if __name__ == '__main__':  # Ensures this is the file being ran
    for extension in extensions:
        bot.load_extension(extension)  # Loades every extension.

# keep_alive()  # Starts a webserver to be pinged.
token = sellerinfo.discord_token
bot.run(token)  # Starts the bot
