import os

import errors
import requests


__version__ = '0.0.1'
URI = os.environ['TELEMETRY_URI']
TOKEN = os.environ['TELEMETRY_TOKEN']


def ebs_account(cluster):
    """Use subscription_labels to look up the eBusiness Suite ID associated with the given cluster ID.
    """
    response = requests.get(
        URI,
        params={
            'query': 'max by(ebs_account) (subscription_labels{{_id="{}"}})'.format(cluster),
        },
        headers = {
            'Accept': 'application/json',
            'Authorization': 'Bearer {}'.format(TOKEN),
            'User-Agent': 'cluster-support-bot/{}'.format(__version__),
        },
    )

    if response.status_code != 200:
        raise errors.RequestException(response=response)

    data = response.json()
    if data['status'] != 'success':
        raise errors.RequestException(response=response)

    for result in data['data']['result']:
        if result.get('metric', {}).get('ebs_account'):
            return result['metric']['ebs_account']

    raise ValueError('no EBS account found')
