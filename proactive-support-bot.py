from slackeventsapi import SlackEventAdapter
import os
import slack
from hydra.hydra import hydra_api as hydra
from pyocm.pyocm import ocm_api as pyocm


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
    if message.get("subtype") is None:
        channel = message["channel"]
        text = message.get('text')

        if "hi" in text:
          message = "Hello <@%s>! :tada:" % message["user"]
          response = client.chat_postMessage(
            channel=channel,
            text=message)
          assert response["ok"]
        elif "fileuploadtest" in message.get('text'):
          response = client.files_upload(
            channels=channel,
            content="Hello, World")
          assert response["ok"]
        elif message.get("subtype") is None and "get summary" in textlower():
          cluster = text.split()[len(text.split())-1]
          account = clusterToAccount(cluster)
          if account:
              response = client.chat_postMessage(
                channel=channel,
                text=account)
          else:
              response = client.chat_postMessage(
                channel=channel,
                text='Encountered an issue converting {0} into a SFDC Account'.format(cluster))
              assert response["ok"]


def clusterToAccount(cluster):
    ocm_api = pyocm(token="PlaceHolderToken")
    try:
        subInfo = ocm_api.get_subs_by_cluster_id(cluster)
    except Exception as e:
        # should break out here as the clusterString was likely invalid
        print('Turning a cluster uuid into more info failed\nMore details: {0}'.format(e))
        return None
    try:
        accountInfo = ocm_api.get_account_by_creator(subInfo.get("items")[0].get("creator").get("id"))
    except Exception as e:
        print('Turning Sub details into account info failed\nMore details: {0}'.format(e))
        return None
    return accountInfo.get("organization").get("ebs_account_info")


# Once we have our event listeners configured, we can start the
# Flask server with the default `/events` endpoint on port 8080
slack_events_adapter.start(host="0.0.0.0", port=8080)
