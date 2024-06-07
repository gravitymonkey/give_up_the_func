from dataclasses import dataclass
from typing import List, Optional
from openai.types.chat.chat_completion import ChatCompletion, Choice, ChatCompletionMessage, CompletionUsage
from openai.types.chat.chat_completion_message import ChatCompletionMessage, FunctionCall


def chat_serializer(obj):
    if isinstance(obj, (ChatCompletion, Choice, ChatCompletionMessage, CompletionUsage, FunctionCall)):
        return obj.__dict__
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

