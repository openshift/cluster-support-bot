import argparse
import logging
import os
import time

import ocm
import slack
from slackeventsapi import SlackEventAdapter


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


recent_events = set()  # cache recent event timestamps


# Our app's Slack Event Adapter for receiving actions via the Events API
slack_signing_secret = os.environ["SLACK_SIGNING_SECRET"]
slack_events_adapter = SlackEventAdapter(slack_signing_secret, "/slack/events")

# Create a SlackClient for your bot to use for Web API requests
client = slack.WebClient(token=os.environ['SLACK_BOT_TOKEN'])
# slack_client = SlackClient(slack_bot_token)

# Storing the OCM Token Globally
ocm_token = os.environ['OCM_TOKEN']


class HelpRequest(ValueError):
    "For jumping out of ErrorRaisingArgumentParser.print_help"
    pass


class ErrorRaisingArgumentParser(argparse.ArgumentParser):
    def exit(self, status=0, message=None):
        raise ValueError({'status': status, 'message': message})

    def error(self, message):
        raise ValueError({'message': message})

    def print_help(self, file=None):
        raise HelpRequest({'parser': self})


# Example responder to greetings
@slack_events_adapter.on("app_mention")
def handle_message(event_data):
    global recent_events

    logger.debug('handle_message: {}'.format(event_data))
    message = event_data['event']
    if message.get('subtype') is not None:
        return  # https://api.slack.com/events/message#message_subtypes
    text = message.get('text')
    if not text:
        return

    timestamp = float(message.get('ts', 0))
    if timestamp in recent_events:  # high-resolution timestamps should have few false-negatives
        logger.info('ignoring duplicate message: {}'.format(message))
        return

    recent_events.add(timestamp)  # add after check without a lock should be a small race window
    cutoff = time.time() - 60*60  # keep events for an hour
    recent_events = {timestamp for timestamp in recent_events if timestamp > cutoff}

    user_args = text.split()[1:]  # split and drop the '<@{bot-id}>' prefix
    try:
        args = parser.parse_args(user_args)
    except HelpRequest as error:
        handler = handle_help(client=client, event=event_data, subparser=error.args[0]['parser'])
    except ValueError as error:
        handler = handle_parse_args_error(client=client, event=event_data, error=error)
    else:
        handler = args.func
        if not handler:
            logger.info('no handler found for {!r}'.format(user_args))
            return
        response = handler(client=client, event=event_data, args=args)
        if not response:
            return
        if response.get('ok'):
            logger.debug(response)
        else:
            logger.error(response)


def handle_parse_args_error(client, event, error):
    channel = event['event']['channel']
    if len(error.args) == 1:
        details = error.args[0]
    else:
        logger.error('unrecognized parse_args error: {}'.format(error))
        return

    message = details.get('message')
    if not message:
        logger.error('parse_args error had no message: {}'.format(error))
        return

    return client.chat_postMessage(channel=channel, text=message)


def handle_help(client, event, args=None, subparser=None):
    channel = event['event']['channel']
    if not subparser:
        subparser = parser
    message = subparser.format_help()
    return client.chat_postMessage(channel=channel, text=message)


def handle_fileuploadtest(client, event, args=None):
    channel = event['event']['channel']
    return client.files_upload(
        channels=channel,
        content="Hello, World")


def handle_cluster(client, event, args=None):
    channel = event['event']['channel']
    cluster = args.cluster
    try:
        account = ocm.cluster_to_account(token=ocm_token, cluster=cluster)
    except ValueError as error:
        if len(error.args) == 1:
            details = error.args[0]
        else:
            logger.error('unrecognized cluster_to_account error: {}'.format(error))
            return

        response = details.get('response')
        if not response:
            logger.error('cluster_to_account error had no request: {}'.format(error))
        return client.chat_postMessage(
                channel=channel,
                text='Failed to find {}: {} -> {}'.format(cluster, response.url, response.status_code))
    return client.chat_postMessage(
            channel=channel,
            text='Based on {0}, we found the Red Hat Customer Portal Account ID {1}'.format(cluster, account))


parser = ErrorRaisingArgumentParser(
    prog='Cluster support bot',
    description='I help you collaborate on per-cluster support issues.',
    formatter_class=argparse.RawDescriptionHelpFormatter,
)
subparsers = parser.add_subparsers()
help_parser = subparsers.add_parser('help', help='Show this help')
help_parser.set_defaults(func=handle_help)
cluster_parser = subparsers.add_parser('cluster', help='Summarize a cluster by ID')
cluster_parser.add_argument('cluster', metavar='ID', nargs=1, help='The cluster ID')
cluster_parser.set_defaults(func=handle_cluster)
fileuploadtest_parser = subparsers.add_parser('fileuploadtest', help='Upload a dummy file to Slack')
fileuploadtest_parser.set_defaults(func=handle_fileuploadtest)


# Once we have our event listeners configured, we can start the
# Flask server with the default `/events` endpoint on port 8080
slack_events_adapter.start(host="0.0.0.0", port=8080)
