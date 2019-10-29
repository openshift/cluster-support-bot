import requests


requests.packages.urllib3.disable_warnings()
__version__ = "0.1.0"


class RequestException(ValueError):
    def __init__(self, response):
        super(RequestException, self).__init__(response)
        self.response = response

    def __str__(self):
        return "failed {} -> {}\n{}".format(
            self.response.url, self.response.status_code, self.response.text
        )


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
            raise RequestException(response=response)

        if not response.text:
            return

        return response.json()

    def get_account_notes(self, account):
        notes = self._hydra(
            fn=requests.get, endpoint="accounts/{}/notes".format(account)
        )
        if notes is None:
            return []

        return [
            {
                "type": n["type"],
                "subject": n["subject"],
                "isRetired": n["isRetired"],
                "note": n["body"],
                "id": n["id"],
            }
            for n in notes
        ]

    def post_account_notes(
        self,
        account,
        body="",
        intendedReviewDate=None,
        needsReview=False,
        retired=False,
        subject="",
        noteType="General Info",
    ):
        content = {"note": {}}
        content["note"].update({"body": body})
        if intendedReviewDate:
            content["note"].update({"intendedReviewDate": intendedReviewDate})
        content["note"].update({"needsReview": needsReview})
        content["note"].update({"retired": retired})
        # There are 4 types of account notes:
        # General Info, Key Notes, Next Steps, and Others
        # Defaulting to "General Info" in order to default to a smaller note
        # We likely will want to use "General Info" for most notes, but possibly use "Key Notes" for summaries
        content["note"].update({"type": noteType})
        content["note"].update({"subject": subject})

        return self._hydra(
            fn=requests.post,
            endpoint="accounts/{}/notes".format(account),
            payload=content,
        )

    def delete_account_notes(self, account, noteID):
        content = {"note": {"id": noteID}}
        return self._hydra(
            fn=requests.delete,
            endpoint="accounts/{}/notes".format(account),
            payload=content,
        )
