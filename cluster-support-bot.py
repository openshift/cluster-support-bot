import argparse
import logging
import os
import time

import hydra
import slack
import telemetry


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


bot_mention = '<@{}> '.format(os.environ['BOT_ID'])

recent_events = set()  # cache recent event timestamps

hydra_client = hydra.Client(username=os.environ['HYDRA_USER'], password=os.environ['HYDRA_PASSWORD'])
dashboard_base = os.environ['DASHBOARD']


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


def dashboard_uri(cluster):
    return '{}{}'.format(dashboard_base, cluster)


@slack.RTMClient.run_on(event='message')
def handle_message(**payload):
    try:
        _handle_message(payload=payload)
    except Exception as e:
        logger.debug('uncaught Exception in handle_message: {}'.format(e))


def _handle_message(payload):
    global recent_events

    data = payload.get('data')
    if not data:
        return
    if data.get('subtype') is not None:
        return  # https://api.slack.com/events/message#message_subtypes
    text = data.get('text')
    if not text:
        return
    if not text.startswith(bot_mention):
        return

    logger.debug('handle_message: {}'.format(payload))

    timestamp = float(data.get('ts', 0))
    if timestamp in recent_events:  # high-resolution timestamps should have few false-negatives
        logger.info('ignoring duplicate message: {}'.format(message))
        return

    recent_events.add(timestamp)  # add after check without a lock should be a small race window
    cutoff = time.time() - 60*60  # keep events for an hour
    recent_events = {timestamp for timestamp in recent_events if timestamp > cutoff}

    user_arg_line, body = (text.strip()+'\n').split('\n', 1)
    user_args = user_arg_line.split()[1:]  # split and drop the '<@{bot-id}>' prefix
    try:
        args = parser.parse_args(user_args)
    except HelpRequest as error:
        handler = handle_help(payload=payload, subparser=error.args[0]['parser'])
    except ValueError as error:
        handler = handle_parse_args_error(payload=payload, error=error)
    else:
        handler = args.func
        if not handler:
            logger.info('no handler found for {!r}'.format(user_args))
            return
        response = handler(payload=payload, args=args, body=body)
        if not response:
            return
        if response.get('ok'):
            logger.debug(response)
        else:
            logger.error(response)


def handle_parse_args_error(payload, error):
    web_client = payload['web_client']
    channel = payload['data']['channel']
    thread = payload['data'].get('thread_ts', payload['data']['ts'])
    if len(error.args) == 1:
        details = error.args[0]
    else:
        logger.error('unrecognized parse_args error: {}'.format(error))
        return

    message = details.get('message')
    if not message:
        logger.error('parse_args error had no message: {}'.format(error))
        return

    return web_client.chat_postMessage(channel=channel, thread_ts=thread, text=message)


def handle_help(payload, args=None, body=None, subparser=None):
    web_client = payload['web_client']
    channel = payload['data']['channel']
    thread = payload['data'].get('thread_ts', payload['data']['ts'])
    if not subparser:
        subparser = parser
    message = subparser.format_help()
    return web_client.chat_postMessage(channel=channel, thread_ts=thread, text=message)


def handle_summary(payload, args=None, body=None):
    web_client = payload['web_client']
    channel = payload['data']['channel']
    thread = payload['data'].get('thread_ts', payload['data']['ts'])
    cluster = args.cluster
    try:
        summary, _ = get_summary(cluster=cluster)
    except ValueError as error:
        return web_client.chat_postMessage(
            channel=channel,
            thread_ts=thread,
            text='{} {}'.format(cluster, error))
    return web_client.chat_postMessage(channel=channel, thread_ts=thread, text=summary)


def handle_detail(payload, args=None, body=None):
    web_client = payload['web_client']
    channel = payload['data']['channel']
    thread = payload['data'].get('thread_ts', payload['data']['ts'])
    cluster = args.cluster
    try:
        summary, notes = get_summary(cluster=cluster)
    except ValueError as error:
        return web_client.chat_postMessage(
            channel=channel,
            thread_ts=thread,
            text='{} {}'.format(cluster, error))
    entries = [summary]
    for note in notes:
        entries.append(
            '{subject}\n{body}'.format(**note),
        )
    return web_client.files_upload(channels=channel, thread_ts=thread, content='\n\n'.join(entries))


def get_notes(cluster, ebs_account):
    notes = hydra_client.get_account_notes(account=ebs_account)
    summary = None
    subject_prefix = 'Summary (cluster {}): '.format(cluster)
    related_notes = []
    for note in notes:
        if note.get('isRetired'):
            continue
        if not note['subject'].startswith(subject_prefix):
            if cluster in note['subject']:
                related_notes.append(note)
            continue
        summary = note
        break
    return summary, related_notes


def get_summary(cluster):
    subscription = telemetry.subscription(cluster=cluster)
    ebs_account = telemetry.ebs_account(subscription=subscription)
    summary, related_notes = get_notes(cluster=cluster, ebs_account=ebs_account)
    lines = ['Cluster {}'.format(cluster)]
    lines.extend([
        'Created by Red Hat Customer Portal Account ID {}'.format(ebs_account),
        'Managed: {}'.format(subscription.get('managed', 'Unknown')),
        'Support: {}'.format(subscription.get('support', 'None.  Customer Experience and Engagement (CEE) will not be able to open support cases.')),
        'Dashboard: {}'.format(dashboard_uri(cluster=cluster)),
    ])
    if summary:
        lines.extend([
            summary['subject'],
            summary['body'],
        ])
    else:
        lines.append('No summary')
    return '\n'.join(lines), related_notes


def handle_set_summary(payload, args=None, body=None):
    web_client = payload['web_client']
    channel = payload['data']['channel']
    thread = payload['data'].get('thread_ts', payload['data']['ts'])
    cluster = args.cluster
    try:
        subject, body = body.split('\n', 1)
    except ValueError:  # subject with no body
        subject, body = body, ''
    body = (body.strip() + '\n\nThis summary was created by the cluster-support bot.  Workflow docs in https://github.com/openshift/cluster-support-bot/').strip()
    subject_prefix = 'Summary (cluster {}): '.format(cluster)
    try:
        ebs_account = telemetry.ebs_account(subscription=telemetry.subscription(cluster=cluster))
        summary, _ = get_notes(cluster=cluster, ebs_account=ebs_account)
        hydra_client.post_account_note(
            account=ebs_account,
            subject='{}{}'.format(subject_prefix, subject),
            body=body,
        )
        if summary:
            hydra_client.delete_account_note(account=ebs_account, noteID=summary['id'])
    except ValueError as error:
        return web_client.chat_postMessage(
            channel=channel,
            thread_ts=thread,
            text='{} {}'.format(cluster, error))
    return web_client.chat_postMessage(channel=channel, thread_ts=thread, text='set {} summary to:\n{}\n{}'.format(cluster, subject, body))


def handle_comment(payload, args=None, body=None):
    web_client = payload['web_client']
    channel = payload['data']['channel']
    thread = payload['data'].get('thread_ts', payload['data']['ts'])
    cluster = args.cluster
    try:
        subject, body = body.split('\n', 1)
    except ValueError:  # subject with no body
        subject, body = body, ''
    try:
        ebs_account = telemetry.ebs_account(subscription=telemetry.subscription(cluster=cluster))
        hydra_client.post_account_note(
            account=ebs_account,
            subject='cluster {}: {}'.format(cluster, subject),
            body=body,
        )
    except ValueError as error:
        return web_client.chat_postMessage(
            channel=channel,
            thread_ts=thread,
            text='{} {}'.format(cluster, error))
    return web_client.chat_postMessage(channel=channel, thread_ts=thread, text='added comment on {}:\n{}\n{}'.format(cluster, subject, body))


parser = ErrorRaisingArgumentParser(
    prog='Cluster support bot',
    description='I help you collaborate on per-cluster support issues ( https://github.com/openshift/cluster-support-bot/ ).',
    formatter_class=argparse.RawDescriptionHelpFormatter,
)
subparsers = parser.add_subparsers()
help_parser = subparsers.add_parser('help', help='Show this help.')
help_parser.set_defaults(func=handle_help)
summary_parser = subparsers.add_parser('summary', help='Summarize a cluster by ID.')
summary_parser.add_argument('cluster', metavar='ID', help='The cluster ID.')
summary_parser.set_defaults(func=handle_summary)
set_summary_parser = subparsers.add_parser('set-summary', help='Set (or edit) the cluster summary.  The line following the set-summary command will be used in the summary subject, and subsequent lines will be used in the summary body.')
set_summary_parser.add_argument('cluster', metavar='ID', help='The cluster ID.')
set_summary_parser.set_defaults(func=handle_set_summary)
detail_parser = subparsers.add_parser('detail', help='Upload a file to Slack with the cluster summary and all comments.')
detail_parser.add_argument('cluster', metavar='ID', help='The cluster ID.')
detail_parser.set_defaults(func=handle_detail)
comment_parser = subparsers.add_parser('comment', help='Add a comment on a cluster by ID.  The line following the comment command will be used in the summary subject, and subsequent lines will be used in the summary body.')
comment_parser.add_argument('cluster', metavar='ID', help='The cluster ID.')
comment_parser.set_defaults(func=handle_comment)

# start the RTM socket
rtm_client = slack.RTMClient(token=os.environ['SLACK_BOT_TOKEN'])
logger.info("bot starting...")
rtm_client.start()
