from typing import List

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import logging

from app.models.chat import stream_choices_text, chat

from pydantic import BaseModel

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


@app.get("/v1/models")
async def models():
    return {
        "data": [
            {
                "id": "custom-gpt-model",
                "object": "model",
                "owned_by": "organization-owner"
            }
        ],
        "object": "list",
    }


@app.post("/v1/chat/completions")
async def chat_completions(completion_request: CompletionRequest):
    logging.info(f"Received request: {completion_request}")

    system_message = completion_request.messages[0].content
    human_message = completion_request.messages[1].content

    json_data = {
        "id": "xxxx",
        "object": "text_completion",
        "created": 1611234567,
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
        chat_generator = chat(system_message, human_message)
        return StreamingResponse(
            stream_choices_text(json_data, chat_generator),
            media_type="text/event-stream"
        )
    else:
        return json_data
