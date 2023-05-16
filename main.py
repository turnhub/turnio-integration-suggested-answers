from flask import Flask, request
import os
import phonenumbers
import requests
import random
import json

app = Flask('app')

# Repl provides these environment variables, we use it
# to construct the URL that this repl will be accessible on.
repl_owner = os.environ.get("REPL_OWNER")
repl_slug = os.environ.get("REPL_SLUG")
repl_url = f'https://{repl_slug}.{repl_owner.lower()}.repl.co'

TOKEN = os.environ.get("TOKEN")
GIPHY_API_KEY = os.environ.get("GIPHY_API_KEY")

@app.route('/')
def hello_world():
  return f'The Turn UI integration API endpoint is at {repl_url}/integration'

@app.route('/integration', methods=['POST'])
def integration():
  json = request.json
  # If the JSON payload has a handshake, return the capabilities
  # of this integration. This way we inform Turn of what this 
  # integration is capable of.
  if json.get("handshake", False):
    return {
      "version": "1.0.0-alpha",
      "capabilities": {
        "actions": True,
        "suggested_responses": True,
        "context_objects": [
          {
            "title": "My Custom Profile",
            "code": "my-custom-profile",
            "type": "table"
          }
        ]
      }
    }

  # As part of the payload we receive the recent messages
  # sent and received in the chat on Turn. 
  # Here we select out the messages that were received (direction 
  # equals inbound) and which are of type text.
  text_messages = [
    message for message in json["messages"]
      if message["type"] == "text" and message["_vnd"]["v1"]["direction"] == "inbound"
    ]
  ordered_by_most_recent = sorted(text_messages, key=lambda message: message["timestamp"], reverse=True)
  # We select the most recent message
  message = ordered_by_most_recent[0]
  
  response = {
    "version": "1.0.0-alpha",
    "suggested_responses": get_suggested_responses(message),
    "actions": get_actions(message),
    "context_objects": get_context_objects(message),
  }
  return response

def get_suggested_responses(message):
  """
  If a message starts with the word "join", which in the case of
  Turn likely means that someone's joined a sandbox for the first
  time, then we'll send a welcome message as a suggested response.
  """
  text = get_text(message)
  profile_name = get_profile_name(message)

  if text.startswith("join"):
    return [{
      "type": "TEXT",
      "title": "Welcome message",
      "confidence": 1.0,
      "body": """Hi _%s_ 👋, and *welcome* to this WhatsApp service!
      
This example extends the Turn UI in 3 ways.

1️⃣ It adds this text as a suggested reply in the UI for any message starting with the word _join_

2️⃣ It adds a custom UI extension called "My Custom Profile" in the sidebar on the left which displays country information based on your phone number's country code prefix.

3️⃣ It adds extra action menu items in your chat window. If the last message received has the word "gif" in it it will add a menu to search for the text on Giphy.com, otherwise it will only display a menu that allows you to roll a dice and send a reply.

Enjoy! 🎉 """ % (profile_name,)
    }]
  else:
    return []

def get_actions(message):
  """
  This will return a set of actions that will be added to the 
  message action menu in the Turn UI for this conversation.
  """
  text = get_text(message)

  actions = {
    "roll_the_dice": {
      "description": "Roll 🎲",
      "url": "%s/action/roll_the_dice" % (repl_url,),
      "payload": {
        "some-custom": "payload"
      },
      "options": {
        "roll_once": "Roll one time",
        "roll_twice": "Roll two times",
      }
    }
  }
  if "gif" in text:
    actions.update({
      "giphy": {
        "description": "Auto Giphy ⚡️",
        "url": "%s/action/giphy" % (repl_url,),
        "payload": {
          "text": text
        }
      }
    })
  return actions

@app.route("/action/roll_the_dice", methods=["POST"])
def roll_the_dice():
  """
  This handles the event when some clicks on the action menu
  to either roll the die once or twice.

  We send a reply via the Turn API with the result.
  """
  message = request.json["message"]
  option = request.json["option"]
  profile_name = get_profile_name(message)
  wa_id = message["from"]
  if option == 'roll_once':
    first_roll = random.randint(1, 6)
    response = send_message(
      wa_id, "Hi %s, you rolled %s!" % (profile_name, first_roll,))
  elif option == 'roll_twice':
    first_roll = random.randint(1, 6)
    second_roll = random.randint(1, 6)
    response = send_message(
      wa_id, "Hi %s, you rolled %s and %s!" % (
        profile_name, first_roll, second_roll))
  return ''

@app.route("/action/giphy", methods=["POST"])
def giphy():
  """
  Search for a gif using the giphy API as per their docs at 
  https://developers.giphy.com/docs/api/endpoint/#search
  """
  message = request.json["message"]
  wa_id = message["from"]
  text = get_text(message).lstrip("gif")
  r = requests.get("https://api.giphy.com/v1/gifs/search", {
    "api_key": GIPHY_API_KEY,
    "q": text,
    "rating": "g",
    "lang": "en"
  })
  response_json = r.json()
  data = response_json["data"]
  if data: 
    gif = data[0]
    mp4_url = gif["images"]["fixed_height"]["mp4"]
    send_video(wa_id, mp4_url)
  else:
    send_message(wa_id, "Sorry couldn't find a gif for %s" % (text,))
  return ''

def send_message(wa_id, body):
  """
  Send a text message to a wa_id
  """
  return requests.post(
    url="https://whatsapp.turn.io/v1/messages",
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
    },
    json={
        "to": wa_id,
        "text": {
            "body": body
        },
    })

def send_video(wa_id, mp4_url):
  """
  Send a video message to a wa_id
  """
  return requests.post(
    url="https://whatsapp.turn.io/v1/messages",
    headers={
      "Authorization": f"Bearer {TOKEN}",
      "Content-Type": "application/json",
    },
    json={
      "to": wa_id,
      "type": "video",
      "video": {
        "link": mp4_url
      }
    }
  )

def get_context_objects(message):
  """
  This will generate the response for the custom profile
  block in the left column in the Turn UI.
  """

  wa_id = message["from"]
  phone_number = phonenumbers.parse("+%s" % (wa_id,), None)
  country = fake_call_to_external_api_service(phone_number.country_code)
  if country:
    capital_city=country["capital"][0]
    
    return {
      "my-custom-profile": {
        "Region": country["region"],
        "Country": country["name"]["official"],
        # this will display the capital name as a link to the capital on Wikipedia
        "Capital": f"[{capital_city}](https://en.wikipedia.org/w/index.php?search={capital_city})"
      }
    }
  else:
    return {
      "my-custom-profile": {
      "Region": "Unknown",
      "Country": "Unknown",
      "Capital": "Unknown"
    }}



### Utility methods below

def get_text(message):
  """
  This returns the text of the message received.
  It assumes the message is of type "text".
  """
  return message["text"]["body"]

def get_profile_name(message):
  """
  This returns the profile name of the WhatsApp contact.
  This payload is received directly from the WhatsApp network
  and reflects the profile name currently active on the phone's
  client -- this can change between messages if the name on the
  phone's client changes.
  """
  return message["_vnd"]["v1"]["author"]["name"]

def fake_call_to_external_api_service(country_code):
  """
  this fakes a call to an external data API that has country
  information. We use the numbe prefix for a phone number to
  get more information about what country the user's phone
  number belongs to.
  """
  country_code = str(country_code)
  if not country_code.startswith("+"):
    country_code = "+" + country_code
  
  # countries file fetched from https://raw.githubusercontent.com/mledoze/countries/master/dist/countries.json
  with open("countries.json", "r", encoding="utf-8") as file:
    countries = json.loads(file.read())
  
  for country in countries:
    if country_code in country["callingCodes"]:
      return country

  return None

app.run(host='0.0.0.0', port=8080)
