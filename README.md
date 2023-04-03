# Custom Chatbot Server

Blog (Japanese only): https://note.com/mahlab/n/n99f28f55287b

## What is this for?

This is a FastAPI server for mocking the connection destination of
the [Chatbot UI](https://github.com/mckaywrigley/chatbot-ui). By setting this server as the
connection destination, you can test chat responses from models implemented by yourself on a screen like ChatGPT. It is
also ideal for demonstrations.

## Setup

```
$ poetry install
$ poetry run python main.py
```
