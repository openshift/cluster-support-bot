import requests


requests.packages.urllib3.disable_warnings()
__version__ = '0.1.0'


def call_ocm(endpoint, token, parameters=None):
    response = requests.get("{}/{}".format("https://api.openshift.com/api", endpoint),
            params=parameters,
            headers = {
                'Accept': 'application/json',
                'Authorization': 'Bearer {}'.format(token),
                'User-Agent': 'cluster-support-bot/{}'.format(__version__),
                }
            )

    if response.status_code == 204:
        return

    if response.status_code != 200:
        raise ValueError({'response': response})

    return response.json()


def cluster_to_account(token, cluster):
    # First authenticate
    access = requests.post(
            'https://sso.redhat.com/auth/realms/redhat-external/protocol/openid-connect/token',
            data = {
                'grant_type': 'refresh_token',
                'client_id':'cloud-services',
                'refresh_token': token
                }
            )
    if access.status_code != 200:
        raise ValueError({'response': access})
    access_token = access.json()['access_token']

    # Next take the cluster and get the sub information from ocm
    subs = call_ocm('accounts_mgmt/v1/subscriptions', access_token, parameters={'search': "external_cluster_id='{}'".format(cluster)})
    # Next take the subs and turn it into an account by getting the creator out
    account = call_ocm('accounts_mgmt/v1/accounts/{}'.format(subs.get('items')[0].get('creator').get('id')), access_token)
    # Finally return the account
    return account.get('organization').get('ebs_account_id')
