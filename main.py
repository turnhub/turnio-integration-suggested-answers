from flask import Flask, request
import openai
import os
from environs import Env
from pprint import pprint

env = Env()
env.read_env()

SYSTEM_PROMPT = env.str("SYSTEM_PROMPT", "You are a helpful assistant who provides informative answers about healthy living.")
MODEL = env.str("MODEL", "gpt-3.5-turbo")
NUMBER_OF_MESSAGES_FOR_CONTEXT = env.int("NUMBER_OF_MESSAGES_FOR_CONTEXT", 4)

openai.api_key = env.str("OPENAI_API_KEY")

app = Flask(__name__)


@app.route('/')
def hello_world():
  return f'The Turn UI integration API endpoint is at /integration'


@app.route('/integration', methods=['POST'])
def integration():
  payload = request.json

  if payload.get("handshake", False):
    return {
      "version": "1.0.0-alpha",
      "capabilities": {
        "actions": False,
        "suggested_responses": True,
        "context_objects": []
      }
    }

  response = {
    "version":
    "1.0.0-alpha",
    "suggested_responses":
    get_suggested_responses(transform_messages(payload["messages"]))
  }
  return response


def transform_messages(messages):
  t_messages = []
  messages_ordered_by_most_recent = sorted(
    messages, key=lambda message: message["timestamp"], reverse=False)

  for message in messages_ordered_by_most_recent:
    if message["type"] == "text":
      if message["_vnd"]["v1"]["direction"] == "outbound":
        t_messages.append({
          "role": "assistant",
          "content": message["text"]["body"]
        })
      elif message["_vnd"]["v1"]["direction"] == "inbound":
        t_messages.append({"role": "user", "content": message["text"]["body"]})

  return t_messages


def get_suggested_responses(messages):
  print("get_suggested_responses")
  print(f"openai.api_key: {openai.api_key}")
  if messages == []:
    return []

  messages_to_respond_to = messages[-NUMBER_OF_MESSAGES_FOR_CONTEXT:]
  messages_final = [{
    "role": "system",
    "content": SYSTEM_PROMPT
  }] + messages_to_respond_to
  
  pprint(messages_final)

  response = openai.ChatCompletion.create(
    model=MODEL,
    messages=messages_final,
    temperature=0,
  )

  formatted_replies = [{
    "type": "TEXT",
    "body": choice["message"]["content"],
    "title": f"ChatGPT Reply {choice['index']}",
    "confidence": 1,
  } for choice in response["choices"]]

  return formatted_replies


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))