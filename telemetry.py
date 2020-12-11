import os

import errors
import requests


__version__ = '0.0.1'
URI = os.environ['TELEMETRY_URI']
TOKEN = os.environ['TELEMETRY_TOKEN']


_ADDITIONAL_REQUEST_ARGUMENTS = {}
if 'TELEMETRY_CA_CERT' in os.environ:
    _response = requests.get(os.environ['TELEMETRY_CA_CERT'])
    if _response.status_code != 200:
        raise errors.RequestException(response=_response)
    _TELEMETRY_CA = '/tmp/telemetry-ca-cert.pem'
    with open(_TELEMETRY_CA, 'w') as f:
        f.write(_response.text)
    _ADDITIONAL_REQUEST_ARGUMENTS['verify'] = _TELEMETRY_CA


def _query(query):
    response = requests.get(
        URI,
        params={
            'query': query,
        },
        headers = {
            'Accept': 'application/json',
            'Authorization': 'Bearer {}'.format(TOKEN),
            'User-Agent': 'cluster-support-bot/{}'.format(__version__),
        },
        timeout=60,
        **_ADDITIONAL_REQUEST_ARGUMENTS,
    )

    if response.status_code != 200:
        raise errors.RequestException(response=response)

    data = response.json()
    if data['status'] != 'success':
        raise errors.RequestException(response=response)

    return data


def subscription(cluster, labels=None):
    """Get the cluster's subscription_labels.
    """
    data = _query(query='group by ({}) (max_over_time(subscription_labels{{_id="{}",support!=""}}[60h]))'.format(','.join(sorted(labels)), cluster))

    if not data.get('data', {}).get('result'):
        raise ValueError('no subscription labels found')

    return data['data']['result'][0]['metric']


def ebs_account(subscription):
    """Use subscription_labels to look up the eBusiness Suite ID associated with the given cluster ID.
    """
    if not subscription.get('ebs_account'):
        raise ValueError('no EBS account found')

    return int(subscription['ebs_account'])
