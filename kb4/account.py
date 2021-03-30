from .api import API


class Account(API):

    def __init__(self):
        super().__init__()
        self._domain = f'{self._domain}/account'

    def get_information(self, full: bool = False) -> dict:

        """Retrieves account data from you KnowBe4 account, including your subscription level, number of seats,
        risk score history, and more.

        :parameter full: a bool, If set to True the entire organization risk score history will be returned. Otherwise,
        only the last 6 months will be returned.
        :return: a dict, API response(s)
        :rtype: dict
        """

        params = {}

        if full:
            params.update({'full': 'true'})

        return self._request(method="GET", url="")

    def admins(self) -> list:

        """Retrieves a list of the Organization's KnowBe4 admins.

        :return: a list, API response(s)
        :rtype: list
        """

        response = self._request(method="GET", url="")[0]

        return response.get('admins')
