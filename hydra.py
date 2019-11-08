import errors
import requests

requests.packages.urllib3.disable_warnings()
__version__ = "0.1.0"


class Client(object):
    def __init__(self, username, password):
        self.url = "https://access.redhat.com/hydra/rest"
        self.username = username
        self.password = password

    def _hydra(self, fn, endpoint, parameters=None, payload=None):
        kwargs = {
            "params": parameters,
            "headers": {
                "Accept": "application/json",
                "User-Agent": "cluster-support-bot/{}".format(__version__),
            },
            "auth": (self.username, self.password),
        }
        if payload is not None:
            kwargs["json"] = payload
        response = fn("{}/{}".format(self.url, endpoint), **kwargs)

        if response.status_code == 204:
            return

        if response.status_code != 200:
            raise errors.RequestException(response=response)

        if not response.text:
            return

        return response.json()

    def get_account_notes(self, account):
        return (
            self._hydra(fn=requests.get, endpoint="accounts/{}/notes".format(account))
            or []
        )

    def post_account_note(
        self,
        account,
        body="",
        intendedReviewDate=None,
        needsReview=False,
        retired=False,
        subject="",
        noteType="General Info",
    ):
        content = {
            "note": {
                "body": body,
                "needsReview": needsReview,
                "retired": retired,
                # There are 4 types of account notes:
                # General Info, Key Notes, Next Steps, and Others
                # Defaulting to "General Info" in order to default to a smaller note
                # We likely will want to use "General Info" for most notes, but possibly use "Key Notes" for summaries
                "type": noteType,
                "subject": subject,
            }
        }
        if intendedReviewDate:
            content["note"].update({"intendedReviewDate": intendedReviewDate})

        return self._hydra(
            fn=requests.post,
            endpoint="accounts/{}/notes".format(account),
            payload=content,
        )

    def delete_account_note(self, account, noteID):
        content = {"note": {"id": noteID}}
        return self._hydra(
            fn=requests.delete,
            endpoint="accounts/{}/notes".format(account),
            payload=content,
        )

    def get_open_cases(self, account):
        return [
            case
            for case in (
                self._hydra(fn=requests.get, endpoint='cases/?accounts={}'.format(account))
                or []
            )
            if not case.get('isClosed')
        ]

    def get_case_comments(self, case):
        return (
            self._hydra(fn=requests.get, endpoint="cases/{}/comments".format(case))
            or []
        )

    def put_case_comment(self, case, body, **kwargs):
        content = {
            'caseComment': {
                'caseNumber': case,
                'commentBody': body,
            },
            'additionalData': {},  # without this, Hydra dies with a NullPointerException
        }
        content['caseComment'].update(kwargs)
        return self._hydra(
            fn=requests.put,
            endpoint='cases/v2/comments',
            payload=content,
        )
