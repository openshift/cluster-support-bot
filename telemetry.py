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
        **_ADDITIONAL_REQUEST_ARGUMENTS,
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
