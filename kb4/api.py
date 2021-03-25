import os
import time
import requests
from exceptions import AuthorizationError


class API:

    def __init__(self):
        self.authToken = os.environ.get("kb4-api-key")
        self.domain = "https://us.api.knowbe4.com/v1"
        self.results_per_page = 500

    def build_url(self, endpoint: str) -> str:
        return f'{self.domain}/{endpoint}'

    def verify_auth_token(self):
        if not self.authToken:
            api_token = input('Please enter your KnowBe4 API Token: ')
            print("Note: You may be prompted for you API token everytime you call the KB4 class until you reboot your "
                  "system.")
            os.environ['kb4-api-key'] = api_token
            self.authToken = api_token

    def set_headers(self):
        return {'Authorization': self.authToken}

    def set_params(self, page: int = 1):
        return {'page': page, 'per_page': self.results_per_page}

    @staticmethod
    def json(response):
        if not response:
            return None
        else:
            return response.json()

    def request(self, method: str, url: str, params: dict = None, json: dict = None, headers: dict = None):

        parameters = self.set_params()

        if params:
            parameters.update(params)

        self.verify_auth_token()
        headers = self.set_headers()
        url = self.build_url(url)

        results = []

        def pagination_handler():

            has_next = True
            terminate = False

            api_requests = 0
            retries = 0

            while has_next and not terminate:

                if retries > 5:
                    raise requests.exceptions.RetryError('Too many consecutive 429 responses were received. Please try '
                                                         'again later.')

                try:
                    response = requests.request(method=method, url=url, params=parameters, json=json, headers=headers)
                    response.raise_for_status()

                except requests.exceptions.HTTPError as http_err:

                    response = http_err.response

                    if response.status_code == 401:
                        raise AuthorizationError(f'HTTP Error ({response.status_code}: Check your API token and try '
                                                 f'again. Run KB4.reset_auth_token to overwrite the current key.')

                    elif response.status_code == 429:
                        retries += 1
                        wait_time = int(response.headers['Retry-After'])
                        time.sleep(wait_time + 1)

                    else:
                        response.raise_for_status()

                else:
                    # Reset retries incrementer
                    retries = 0

                    # Add 1 to # of API request made
                    api_requests += 1

                    # Extract JSON from response and append values to results
                    response = self.json(response)

                    if isinstance(response, list):
                        results.extend(response)
                    elif isinstance(response, dict):
                        results.append(response)

                    if len(response) != self.results_per_page:
                        has_next, terminate = False, True
                    else:
                        has_next = True
                        parameters['page'] += 1

        pagination_handler()

        return results[0] if len(results) == 1 else results
