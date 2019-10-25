import requests

requests.packages.urllib3.disable_warnings()

def call_ocm(endpoint, token, parameters=None):
    r = requests.get("{}/{}".format("https://api.openshift.com/api/", endpoint),
            params=parameters, 
            headers = {
                'Accept': 'application/json',
                'Authorization': 'Bearer {}'.format(token),
                'User-Agent': 'pythonCall'
                }
            )

    if r.status_code == 204:
        return []
    if r.status_code != 200:
        raise Exception('''looking up infomation from: {}\n
                Error Code: {}\n {}'''.format(endpoint, r.status_code, r.url))

    return r.json()


def cluster_to_account(token, cluster):
    requests.packages.urllib3.disable_warnings()
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
        raise Exception("""looking up infomation from: {}\nError Code: {}""".format(endpoint, access.status_code))
    access_token = access.json()['access_token']

    # Next take the cluster and get the sub information from ocm
    subs = call_ocm('accounts_mgmt/v1/subscriptions', access_token,parameters={'search': 'external_cluster_id=\'{}\''.format(cluster)})
    # Next take the subs and turn it into an account by getting the creator out
    account = call_ocm('accounts_mgmt/v1/accounts/{}'.format(subs.get('items')[0].get('creator').get('id')), access_token)
    # Finally return the account
    return account.get('organization').get('ebs_account_id')
