from slackeventsapi import SlackEventAdapter
import os
import slack


# Our app's Slack Event Adapter for receiving actions via the Events API
slack_signing_secret = os.environ["SLACK_SIGNING_SECRET"]
slack_events_adapter = SlackEventAdapter(slack_signing_secret, "/slack/events")

# Create a SlackClient for your bot to use for Web API requests
client = slack.WebClient(token=os.environ['SLACK_BOT_TOKEN'])
# slack_client = SlackClient(slack_bot_token)

# Example responder to greetings
@slack_events_adapter.on("app_mention")
def handle_message(event_data):
    print("handle_message")
    message = event_data["event"]
    print(message)
    print(message.get('text'))
    # If the incoming message contains "hi", then respond with a "Hello" message
    if message.get("subtype") is None and "hi" in message.get('text'):
        channel = message["channel"]
        message = "Hello <@%s>! :tada:" % message["user"]
        response = client.chat_postMessage(
          channel=channel,
          text=message)
        assert response["ok"]

# Once we have our event listeners configured, we can start the
# Flask server with the default `/events` endpoint on port 8080
slack_events_adapter.start(host="0.0.0.0", port=8080)
