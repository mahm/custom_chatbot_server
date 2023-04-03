import json
import threading
import queue
import logging

from langchain.chat_models import ChatOpenAI
from langchain.callbacks.base import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

from langchain.schema import (
    HumanMessage,
    SystemMessage
)


async def stream_choices_text(json_data, chat_generator):
    json_without_choices = json_data.copy()
    json_without_choices["choices"] = [{
        "text": '',
        "index": 0,
        "logprobs": None,
        "finish_reason": 'length',
        "delta": {"content": ''}
    }]

    # logging.info(f"Sending initial JSON: {json_without_choices}")
    yield f"data: {json.dumps(json_without_choices)}\n\n"  # NOTE: EventSource

    text = ""
    for chunk in chat_generator:
        text += chunk
        json_data["choices"][0]["delta"] = {"content": chunk}
        # logging.info(f"Sending chunk: {json.dumps(json_data)}")
        yield f"data: {json.dumps(json_data)}\n\n"  # NOTE: EventSource

    json_data["choices"][0]["text"] = text
    logging.info(f"reply: {text}")
    yield f"data: {json.dumps(json_data)}\n\n"  # NOTE: EventSource
    yield f"data: [DONE]\n\n"  # NOTE: EventSource


class ThreadedGenerator:
    def __init__(self):
        self.queue = queue.Queue()

    def __iter__(self):
        return self

    def __next__(self):
        item = self.queue.get()
        if item is StopIteration:
            raise item
        return item

    def send(self, data):
        self.queue.put(data)

    def close(self):
        self.queue.put(StopIteration)


class ChainStreamHandler(StreamingStdOutCallbackHandler):
    def __init__(self, gen):
        super().__init__()
        self.gen = gen

    def on_llm_new_token(self, token: str, **kwargs):
        self.gen.send(token)


def llm_thread(g, system, prompt):
    try:
        print("system:", system)
        print("prompt:", prompt)
        chat = ChatOpenAI(
            verbose=True,
            streaming=True,
            callback_manager=CallbackManager([ChainStreamHandler(g)]),
            temperature=0.7,
        )
        chat([SystemMessage(content=system), HumanMessage(content=prompt)])

    finally:
        g.close()


def chat(system, prompt):
    g = ThreadedGenerator()
    threading.Thread(target=llm_thread, args=(g, system, prompt)).start()
    return g
