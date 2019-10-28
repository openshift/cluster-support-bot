import time

import requests


requests.packages.urllib3.disable_warnings()
__version__ = '0.1.0'


class RequestException(ValueError):
    def __init__(self, response):
        super(RequestException, self).__init__(response)
        self.response = response

    def __str__(self):
        return 'failed {} -> {}\n{}'.format(self.response.url, self.response.status_code, self.response.text)


class Client(object):

    def __init__(self, token):
        self.token = token
        self._session_token = None
        self._session_token_time = None

    def _call(self, endpoint, parameters=None):
        self._refresh_session_token()
        response = requests.get(
            '{}/{}'.format("https://api.openshift.com/api", endpoint),
            params=parameters,
            headers = {
                'Accept': 'application/json',
                'Authorization': 'Bearer {}'.format(self._session_token),
                'User-Agent': 'cluster-support-bot/{}'.format(__version__),
                }
            )

        if response.status_code == 204:
            return

        if response.status_code != 200:
            raise RequestException(response=response)

        return response.json()

    def _refresh_session_token(self):
        if self._session_token_time and time.time() - self._session_token_time < 5*60:
            # less than 5 minutes old, no need to refresh
            return
        response = requests.post(
            'https://sso.redhat.com/auth/realms/redhat-external/protocol/openid-connect/token',
            data = {
                'grant_type': 'refresh_token',
                'client_id':'cloud-services',
                'refresh_token': self.token,
            },
        )
        if response.status_code != 200:
            raise RequestException(response=response)
        self._session_token = response.json()['access_token']
        self._session_token_time = time.time()

    def accounts(self, id):
        return self._call(endpoint='accounts_mgmt/v1/accounts/{}'.format(id))

    def subscriptions(self, cluster):
        return self._call(
            endpoint='accounts_mgmt/v1/subscriptions',
            parameters={'search': "external_cluster_id='{}'".format(cluster)},
        )
