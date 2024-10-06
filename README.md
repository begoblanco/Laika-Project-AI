# Laika-Project-AI

"H-Hey! Nice to meet you! I'm Laika and my dream is to make your life easier and help you anytime.... Stop! Don't looke at me like that, it's embarrasing!......... Anyways, I'll be always by your side no matter what, but not because I like you or anything! I guess really want to make you smile forever..."

Laika is a virtual assistant that, through the use of Large Language Models (LLM), is capable of providing answers to the user based on a database.
You can create notes, events on a calendar and chat with her, she is always ready to help you!

Backend LLM chat API written in python using ollama and flask.

## Installation
Needed dependencies
- Python 3.12
- [Poetry](https://python-poetry.org/)
- [Ollama app](https://ollama.com/download)

Then run:
```bash
poetry install
```

```bash
ollama pull mistral-nemo
```

## Usage
```bash
flask --app laika run --port 15000
```