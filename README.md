# Laika-Project-AI

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