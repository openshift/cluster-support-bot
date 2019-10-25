import logging
import os

import slack
from slackeventsapi import SlackEventAdapter


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logger.DEBUG)


# Our app's Slack Event Adapter for receiving actions via the Events API
slack_signing_secret = os.environ["SLACK_SIGNING_SECRET"]
slack_events_adapter = SlackEventAdapter(slack_signing_secret, "/slack/events")

# Create a SlackClient for your bot to use for Web API requests
client = slack.WebClient(token=os.environ['SLACK_BOT_TOKEN'])
# slack_client = SlackClient(slack_bot_token)

# Example responder to greetings
@slack_events_adapter.on("app_mention")
def handle_message(event_data):
    logger.debug('handle_message', event_data)
    message = event_data['event']
    if message.get('subtype') is not None:
        continue  # https://api.slack.com/events/message#message_subtypes
    text = message.get('text')
    if not text:
        continue
    command = text.split()[-1]  # FIXME: some way to reject earlier garbage
    handler = globals().get('handle_{}'.format(command))
    if not handler:
        logger.info('no handler found for {!r}'.format(command))
        continue
    response = handler(client=client, event=event)
    if not response:
        continue
    if response.get('ok'):
        logger.debug(response)
    else:
        logger.error(response)


def handle_hi(client, event):
    message = event['event']
    response = 'Hello <@{user}>! :tada:'.format(**message)
    return client.chat_postMessage(
        channel=channel,
        text=response)

def handle_fileuploadtest(client, event):
    channel = message['event']['channel']
    return client.files_upload(
        channels=channel,
        content="Hello, World")


# Once we have our event listeners configured, we can start the
# Flask server with the default `/events` endpoint on port 8080
slack_events_adapter.start(host="0.0.0.0", port=8080)
