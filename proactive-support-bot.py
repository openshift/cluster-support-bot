import logging
import os

import slack
from slackeventsapi import SlackEventAdapter
import ocm


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


# Our app's Slack Event Adapter for receiving actions via the Events API
slack_signing_secret = os.environ["SLACK_SIGNING_SECRET"]
slack_events_adapter = SlackEventAdapter(slack_signing_secret, "/slack/events")

# Create a SlackClient for your bot to use for Web API requests
client = slack.WebClient(token=os.environ['SLACK_BOT_TOKEN'])
# slack_client = SlackClient(slack_bot_token)

# Storing the OCM Token Globally
ocm_token = os.environ['pyocm']

# Example responder to greetings
@slack_events_adapter.on("app_mention")
def handle_message(event_data):
    logger.debug('handle_message', event_data)
    message = event_data['event']
    if message.get('subtype') is not None:
        return  # https://api.slack.com/events/message#message_subtypes
    text = message.get('text')
    if not text:
        return
    command = text.split()[-1]  # FIXME: some way to reject earlier garbage
    handler = globals().get('handle_{}'.format(command))
    if not handler:
        logger.info('no handler found for {!r}'.format(command))
        return
    response = handler(client=client, event=event_data)
    if not response:
        return
    if response.get('ok'):
        logger.debug(response)
    else:
        logger.error(response)


def handle_hi(client, event):
    message = event['event']
    channel = event['event']['channel']
    response = 'Hello <@{user}>! :tada:'.format(**message)
    return client.chat_postMessage(
        channel=channel,
        text=response)

def handle_fileuploadtest(client, event):
    channel = event['event']['channel']
    return client.files_upload(
        channels=channel,
        content="Hello, World")

def handle_cluster(client, event):
    channel = event['event']['channel']
    cluster = event['event'].get('text').split()[-1]
    account = ocm.cluster_to_account(token=ocm_token, cluster=cluster)
    return client.chat_postMessage(
            channel=channel,
            text='Based on {0}, we found the Red Hat Customer Portal Account ID {1}'.format(cluster, account))

# Once we have our event listeners configured, we can start the
# Flask server with the default `/events` endpoint on port 8080
slack_events_adapter.start(host="0.0.0.0", port=8080)
