from flask import Flask, request
import datetime
import json
import ollama
import asyncio

app = Flask(__name__)


def tool_get_notes(content: str) -> str:
    notes = [
        {
            "title": "JavaScript is Single-Threaded",
            "content": "JavaScript operates on a single thread, meaning it can only execute one task at a time. This simplifies code execution but can cause blocking issues when handling long-running tasks.",
        },
        {
            "title": "JavaScript Supports Asynchronous Programming",
            "content": "JavaScript uses asynchronous mechanisms like callbacks, promises, and async/await to handle tasks without blocking the main thread. This is crucial for tasks like fetching data from APIs or reading files.",
        },
        {
            "title": "JavaScript is Dynamically Typed",
            "content": "JavaScript is dynamically typed, meaning variables do not require a specific type declaration. The type is determined at runtime, which can lead to type-related errors but adds flexibility in variable usage.",
        },
        {
            "title": "JavaScript Runs in Browsers and on Servers",
            "content": "JavaScript is primarily known for running in web browsers, enabling interactivity on websites. However, with environments like Node.js, JavaScript can also be used for server-side development.",
        },
    ]
    return json.dumps(notes)


def tool_get_calendar(start_date=None) -> str:
    if start_date is None:
        start_date = datetime.date.today().isoformat()
    calendar = {
        start_date: [],
        (start_date + datetime.timedelta(days=1)).isoformat(): [],
        (start_date + datetime.timedelta(days=2)).isoformat(): [],
        (start_date + datetime.timedelta(days=2)).isoformat(): [],
    }
    return json.dumps(calendar)


async def do_chat(model: str, extra_messages: str):
    client = ollama.AsyncClient()
    # Initialize conversation with a user query
    messages = [
        {
            "role": "system",
            "content": """You are a virtual assitant which has a series of tools defined, if you are not sure what tool to use respond normally without mentioning tool usage.
            You must always respond adding a matching emotion, you can choose between the following emotions: happy, sad, thinking, neutral, tired. Please respond in json with the following format:
            {"emotion": "happy", "response": "your response"}
            """,
        },
        {"role": "user", "content": "hello!"},
        {
            "role": "assistant",
            "content": """{"emotion": "happy", "response": "Hello! How are you?"}""",
        }
    ]

    messages.extend(extra_messages)


    # First API call: Send the query and function description to the model
    response = await client.chat(
        model=model,
        messages=messages,
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "tool_get_notes",
                    "description": "Get notes containing some text.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "content": {
                                "type": "string",
                                "description": "Text to search for in notes.",
                            },
                        },
                        "required": ["content"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "tool_get_calendar",
                    "description": "Get calendar information from the given start day",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "start_date": {
                                "type": "string",
                                "description": "Start day in YYYY-MM-DD format.",
                            }
                        },
                        "required": [],
                    },
                },
            },
        ],
    )

    messages.append(response["message"])

    # Check if the model decided to use the provided function
    if not response["message"].get("tool_calls"):
        print(f"response: {response}")
        return response["message"]["content"]

    if response["message"].get("tool_calls"):
        available_functions = {
            "tool_get_notes": tool_get_notes,
            "tool_get_calendar": tool_get_calendar,
        }
        for tool in response["message"]["tool_calls"]:
            function_to_call = available_functions[tool["function"]["name"]]
            print(f"function to call: {function_to_call}")

            function_response = function_to_call(**tool["function"]["arguments"])

            messages.append(
                {
                    "role": "tool",
                    "content": function_response,
                }
            )

        print(f"messages: {messages}")
        final_response = await client.chat(model=model, messages=messages)
        return final_response["message"]["content"]

@app.post("/chat")
def chat():
    data = request.get_json()
    return asyncio.run(do_chat(model="qwen2", extra_messages=data))

