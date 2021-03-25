from api import API


class Training(API):

    def __init__(self):
        super().__init__()
        self.domain = f'{self.domain}/training'

    def get_store_purchases(self, store_purchase_id: int = None) -> (list, dict):

        """Retrieves all store purchases (or a specific purchase if a store_purchase_id is provided) in your KnowBe4
        account.

        :parameter store_purchase_id: an int, a store purchase ID to filter on
        :return: a list or a dict, API response(s)
        :rtype: (list, dict)
        """

        # Get a Specific Store Purchase:
        # https://developer.knowbe4.com/reporting/#tag/Training/paths/~1v1~1training~1store_purchases~1{store_purchase_id}/get
        if store_purchase_id:
            return self.request(method="GET", url=f'store_purchases/{store_purchase_id}')

        # Get All Store Purchases:
        # https://developer.knowbe4.com/reporting/#tag/Training/paths/~1v1~1training~1store_purchases/get
        else:
            return self.request(method="GET", url=f'store_purchases')

    def get_policies(self, policy_id: int = None) -> (list, dict):

        """Retrieves all policies (or a specific policy if a policy_id is provided) in your KnowBe4 account.

        :parameter policy_id: an int, a policy ID to filter on
        :return: a list or a dict, API response(s)
        :rtype: (list, dict)
        """

        # Get a Specific Policy:
        # https://developer.knowbe4.com/reporting/#tag/Training/paths/~1v1~1training~1policies~1{policy_id}/get
        if policy_id:
            return self.request(method="GET", url=f'policies/{policy_id}')

        # Get All Policies:
        # https://developer.knowbe4.com/reporting/#tag/Training/paths/~1v1~1training~1policies/get
        else:
            return self.request(method="GET", url=f'policies')

    def get_campaigns(self, campaign_id: int = None) -> (list, dict):

        """Retrieves all training campaigns (or a specific training campaign if a campaign_id is provided) in your
        KnowBe4 account.

        :parameter campaign_id: an int, a training campaign ID to filter on
        :return: a list or a dict, API response(s)
        :rtype: (list, dict)
        """

        # Get a Specific Training Campaign:
        # https://developer.knowbe4.com/reporting/#tag/Training/paths/~1v1~1training~1campaigns~1{campaign_id}/get
        if campaign_id:
            return self.request(method="GET", url=f'campaigns/{campaign_id}')

        # Get All Training Campaigns:
        # https://developer.knowbe4.com/reporting/#tag/Training/paths/~1v1~1training~1campaigns/get
        else:
            return self.request(method="GET", url=f'campaigns')

    def get_enrollments(self, enrollment_id: int = None, store_purchase_id: int = None,
                        campaign_id: int = None, user_id: int = None) -> (list, dict):

        """Retrieves all training enrollments (or a specific training enrollment if a enrollment_id is provided) in
        your KnowBe4 account.

        :parameter enrollment_id: an int, a training enrollment ID to filter on
        :parameter store_purchase_id: an int, a store purchase ID to filter on
        :parameter campaign_id: an int, a training campaign ID to filter on
        :parameter user_id: an int, a user ID to filter on
        :return: a list or a dict, API response(s)
        :rtype: (list, dict)
        """

        params = {}

        if store_purchase_id:
            params.update({'store_purchase_id': store_purchase_id})
        if campaign_id:
            params.update({'campaign_id': campaign_id})
        if user_id:
            params.update({'user_id': user_id})

        # Get a Specific Training Enrollment
        # https://developer.knowbe4.com/reporting/#tag/Training/paths/~1v1~1training~1enrollments~1{enrollment_id}/get
        if enrollment_id:
            return self.request(method="GET", url=f'enrollments/{enrollment_id}')

        # Get All Training Enrollments
        # https://developer.knowbe4.com/reporting/#tag/Training/paths/~1v1~1training~1enrollments/get
        else:
            return self.request(method="GET", url=f'enrollments', params=params)
