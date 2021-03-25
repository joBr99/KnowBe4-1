from .api import API


class Users(API):

    def __init__(self):
        super().__init__()
        self.domain = f'{self.domain}/users'

    def get(self, status: str = 'active', group_id: int = None, user_id: int = None, expand: bool = False) -> (list,
                                                                                                               dict):

        """Retrieves all users (or a specific user if a user_id is provided) in your KnowBe4 account

        :parameter status: a str, Filter results based on status (active / archived) [Default = active]
        :parameter group_id: a str, A group ID to filter on
        :parameter user_id: an int, A user ID to filter on
        :parameter expand: a bool, If true, expands groups to provide additional details [Default = False]
        :return: a list or a dict, API response(s)
        :rtype: (list, dict)
        """

        params = {}

        # Get a Specific User
        # https://developer.knowbe4.com/reporting/#tag/Users/paths/~1v1~1users~1{user_id}/get
        if user_id:
            return self.request(method="GET", url=f'{user_id}')

        # Get All Users:
        # https://developer.knowbe4.com/reporting/#tag/Users/paths/~1v1~1users/get
        else:
            if group_id:
                params.update({'group_id': group_id})
            if status.lower() not in ['archived', 'active']:
                raise ValueError(f'{status} is an invalid value for status. Possible values: '
                                 f'["active", "archived"]')
            else:
                if status.lower() == 'archived':
                    params.update({'status': 'archived'})
                elif status.lower() == 'active':
                    params.update({'status': 'active'})
            if expand:
                params.update({'expand': 'group'})

            return self.request(method="GET", url="", params=params)
