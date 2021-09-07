class RequestException(ValueError):
    "Helper for formatting requests errors"

    def __init__(self, response):
        super(RequestException, self).__init__(response)
        self.response = response

    def __str__(self):
        text = self.response.text
        if len(text) > 160:
            text = text[:157] + '...'
        return "failed {} -> {}\n{}".format(
            self.response.url, self.response.status_code, text,
        )
