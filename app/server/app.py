import json
import time
import uuid
from typing import List

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import logging

from pydantic import BaseModel

from app.models.simple_conversation_chat import SimpleConversationChat
from app.models.summary_conversation_chat import SummaryConversationChat

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="LangChain API",
)


class Message(BaseModel):
    role: str
    content: str


class CompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    max_tokens: int
    temperature: float
    stream: bool


async def streaming_response(json_data, chat_generator):
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


@app.get("/v1/models")
async def models():
    return {
        "data": [
            {
                "id": "simple-conversation-chat",
                "object": "model",
                "owned_by": "organization-owner"
            },
            {
                "id": "summary-conversation-chat",
                "object": "model",
                "owned_by": "organization-owner"
            },
        ],
        "object": "list",
    }


@app.post("/v1/chat/completions")
async def chat_completions(completion_request: CompletionRequest):
    logging.info(f"Received request: {completion_request}")

    history_messages = completion_request.messages[:-1]
    user_message = completion_request.messages[-1]

    if completion_request.model == "simple-conversation-chat":
        chat = SimpleConversationChat(history_messages)
    elif completion_request.model == "summary-conversation-chat":
        chat = SummaryConversationChat(history_messages)
    else:
        raise ValueError(f"Unknown model: {completion_request.model}")

    json_data = {
        "id": str(uuid.uuid4()),
        "object": "text_completion",
        "created": int(time.time()),
        "model": completion_request.model,
        "choices": [
            {
                "text": "",
                "index": 0,
                "logprobs": None,
                "finish_reason": "length"
            }
        ]
    }

    if completion_request.stream:
        return StreamingResponse(
            streaming_response(json_data, chat.generator(user_message.content)),
            media_type="text/event-stream"
        )
    else:
        return json_data
