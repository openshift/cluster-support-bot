import asyncio
import logging
import os


import prometheus_client
import slack

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

recent_events = set()  # cache recent event timestamps


@slack.RTMClient.run_on(event='message')
def handle_message(**payload):
    try:
        # Exit if the message doesn't have ID
        message_id = payload['data'].get('client_msg_id')
        if not message_id:
            return
        asyncio.ensure_future(
            messages._handle_message(msg_id=message_id, payload=payload),
            loop=asyncio.get_event_loop())
    except Exception as e:
        logger.debug('uncaught Exception in handle_message: {}'.format(e))


if __name__ == '__main__':
    from cluster_support_bot import hydra
    from cluster_support_bot import messages

    mention_counter = prometheus_client.Counter('cluster_support_mentions',
                                                'Number of times a cluster is mentioned where '
                                                'the cluster-support bot is listening', ['_id'])
    messages.mention_counter = mention_counter
    comment_counter = prometheus_client.Counter('cluster_support_comments',
                                                'Number of times a cluster has been commented via '
                                                'the cluster-support bot', ['_id'])
    messages.mention_counter = comment_counter
    # Eventually we'll likely switch to some sort of wsgi app but for now any path
    # requested will return our metrics.  We'll configure /metrics to be scrapped
    # so we can leave room for some sort of landing page in the future.
    prometheus_client.start_http_server(8080)

    hydra_client = hydra.Client(
        username=os.environ['HYDRA_USER'], password=os.environ['HYDRA_PASSWORD'])
    messages.hydra_client = hydra_client

    # start the RTM socket
    rtm_client = slack.RTMClient(token=os.environ['SLACK_BOT_TOKEN'])
    logger.info("bot starting...")
    rtm_client.start()
