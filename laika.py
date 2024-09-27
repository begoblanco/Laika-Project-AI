import datetime
import json
import os
import traceback

import ollama
from flask import Flask, request
from mysql.connector import connect, Error
import dotenv

dotenv.load_dotenv()

app = Flask(__name__)


def exception_to_json(exception):
    # Capture exception details
    exc_type = type(exception).__name__
    exc_message = str(exception)
    exc_traceback = traceback.format_exc()

    # Create a dictionary to hold exception information
    exception_dict = {
        "type": exc_type,
        "message": exc_message,
        "traceback": exc_traceback,
    }

    # Convert dictionary to JSON
    return json.dumps(exception_dict)


def tool_get_notes(user_id: int, topic: str) -> str:
    try:
        with connect(
            host=os.getenv("MYSQL_HOST"),
            port=os.getenv("MYSQL_PORT"),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            database=os.getenv("MYSQL_DATABASE"),
        ) as connection:
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute(
                    """SELECT title, content FROM notes WHERE user_id=%s AND content like %s"""
                    % (user_id, f"'%{topic}%'")
                )
                result = cursor.fetchall()
                print(json.dumps(result))
                return json.dumps(result)
    except Error as e:
        return exception_to_json(e)


def tool_get_upcoming_events(user_id: int, current_date: str) -> str:
    try:
        with connect(
            host=os.getenv("MYSQL_HOST"),
            port=os.getenv("MYSQL_PORT"),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            database=os.getenv("MYSQL_DATABASE"),
        ) as connection:
            with connection.cursor(dictionary=True) as cursor:
                d = datetime.datetime.strptime(current_date, "%Y-%m-%d").date()
                cursor.execute(
                    """
                    SELECT
                        title, DATE_FORMAT(start_date , '%%Y-%%m-%%d') AS start_date, DATE_FORMAT(start_date , '%%Y-%%m-%%d') AS end_date
                    FROM events
                    WHERE
                        user_id = %s 
                        AND start_date > '%s'
                        AND start_date <= DATE_ADD('%s', INTERVAL 7 DAY)
                        ORDER BY start_date ASC LIMIT 7
                    """
                    % (user_id, d, d)
                )
                result = cursor.fetchall()
                print(json.dumps(result))
                return json.dumps(result)
    except Error as e:
        return exception_to_json(e)


def process_query(model: str, user_input: str):
    client = ollama.Client()
    # Initialize conversation with a user query
    messages = [
        {
            "role": "system",
            "content": """You are a virtual assitant which has a series of tools defined, if you are not sure what tool to use respond normally without mentioning tool usage.
            You will receive messages from the user with the following json format:
            {"user_id": int, "current_date": string, "message": string}
            You must always respond adding a matching emotion, you can choose between the following emotions: ['angry', 'confused', 'happy', 'neutral', 'sad', 'very_happy', 'laughing].
            Please respond in json with the following format:
            {"emotion": "happy", "message": "your response"}
            """,
        },
        {
            "role": "user",
            "content": """{"user_id": 1, "current_date": "2024-09-27", "message": "hello!"}""",
        },
        {
            "role": "assistant",
            "content": """{"emotion": "happy", "message": "Hello! How are you?"}""",
        },
        {
            "role": "user",
            "content": """{"user_id": 1, "current_date": "2024-09-27", "message": "Tell me a joke"}""",
        },
        {
            "role": "assistant",
            "content": """{"emotion": "laughing", "message": "Why don’t skeletons fight each other? They don’t have the guts!"}""",
        },
        {
            "role": "user",
            "content": """{"user_id": 1, "current_date": "2024-09-27", "message": "What notes do i have about javascript?"}""",
        },
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "function": {
                        "name": "tool_get_notes",
                        "arguments": {"topic": "javascript", "user_id": 1},
                    }
                }
            ],
        },
        {
            "role": "tool",
            "content": """[
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
            ]""",
        },
        {
            "role": "assistant",
            "content": """{"emotion": "thinking", "message": "Here are some notes you have mentioning JavaScript:\n\n- **JavaScript is
Single-Threaded**: JavaScript operates on a single thread, meaning it can only execute one task at a time. This
simplifies code execution but can cause blocking issues when handling long-running tasks.\n- **JavaScript Supports
Asynchronous Programming**: JavaScript uses asynchronous mechanisms like callbacks, promises, and async/await to handle
tasks without blocking the main thread. This is crucial for tasks like fetching data from APIs or reading files.\n-
**JavaScript is Dynamically Typed**: JavaScript is dynamically typed, meaning variables do not require a specific type
declaration. The type is determined at runtime, which can lead to type-related errors but adds flexibility in variable
usage.\n- **JavaScript Runs in Browsers and on Servers**: JavaScript is primarily known for running in web browsers,
enabling interactivity on websites. However, with environments like Node.js, JavaScript can also be used for server-side
development."}""",
        },
        {
            "role": "user",
            "content": user_input,
        },
    ]

    # First API call: Send the query and function description to the model
    response = client.chat(
        model=model,
        messages=messages,
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "tool_get_notes",
                    "description": "Get notes mentioning given topic.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "int",
                                "description": "id of the user sending a message.",
                            },
                            "topic": {
                                "type": "string",
                                "description": "Topic to search for in notes.",
                            },
                        },
                        "required": ["user_id", "topic"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "tool_get_upcoming_events",
                    "description": "Get upcoming events",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "int",
                                "description": "id of the user sending a message.",
                            },
                            "current_date": {
                                "type": "string",
                                "description": "Start day in YYYY-MM-DD format.",
                            },
                        },
                        "required": ["user_id"],
                    },
                },
            },
        ],
    )

    messages.append(response["message"])

    # Check if the model decided to use the provided function
    if "tool_calls" not in response["message"]:
        print("No tool used.")
        return response["message"]["content"]

    if response["message"]["tool_calls"]:
        print(response["message"])
        available_functions = {
            "tool_get_notes": tool_get_notes,
            "tool_get_upcoming_events": tool_get_upcoming_events,
        }
        for tool in response["message"]["tool_calls"]:
            function_to_call = available_functions[tool["function"]["name"]]
            print(f"tool to call: {function_to_call}")

            function_response = function_to_call(**tool["function"]["arguments"])

            messages.append(
                {
                    "role": "tool",
                    "content": function_response,
                }
            )

        final_response = client.chat(model=model, messages=messages)
        return final_response["message"]["content"]


@app.post("/chat")
def chat():
    query_response = process_query("mistral-nemo", json.dumps(request.json))
    try:
        parsed_response = json.dumps(
            json.loads(query_response.replace("[TOOL_CALLS]", "").replace("\n", "\\n"))
        )
    except Exception as e:
        print(e)
        print(query_response)
        parsed_response = json.dumps(
            {
                "emotion": "happy",
                "message": query_response.replace("[TOOL_CALLS]", "").replace(
                    "\n", "\\n"
                ),
            }
        )

    response = app.response_class(
        response=parsed_response,
        status=200,
        mimetype="application/json",
    )
    return response
