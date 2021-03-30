from .api import API, PhishingCampaign, PhishingSecurityTest, PhishingCampaignRecipient


class Phishing(API):

    def __init__(self):
        super().__init__()
        self._domain = f'{self._domain}/phishing'

    def get_campaigns(self, campaign_id: int = None) -> list:

        """Retrieves all phishing campaigns (or a specific phishing campaign if a campaign_id is
        provided) in your KnowBe4 account.

        :parameter campaign_id: an int, a phishing campaign ID to filter on
        :return: a list, API response(s)
        :rtype: list
        """

        # Get a Specific Phishing Campaign:
        # https://developer.knowbe4.com/reporting/#tag/Phishing/paths/~1v1~1phishing~1campaigns~1{campaign_id}/get
        if campaign_id:
            return [PhishingCampaign.from_dict(phishing_campaign)
                    for phishing_campaign in self._request(method="GET", url=f'campaigns/{campaign_id}')]

        # Get All Phishing Campaigns:
        # https://developer.knowbe4.com/reporting/#tag/Phishing/paths/~1v1~1phishing~1campaigns/get
        else:
            return [PhishingCampaign.from_dict(phishing_campaign)
                    for phishing_campaign in self._request(method="GET", url=f'campaigns')]

    def get_security_tests(self, campaign_id: int = None, phishing_security_test_id: int = None) -> list:

        """Retrieves all phishing security tests (or a phishing security test from a specific campaign if a
        campaign_id is provided) in your KnowBe4 account.

        :parameter campaign_id: an int, a security test campaign ID to filter on
        :parameter phishing_security_test_id: an int, a phishing security test ID to filter on
        :return: a list, API response(s)
        :rtype: list
        """

        if campaign_id and phishing_security_test_id:
            raise ValueError('Please provide either a value for campaign_id or phishing_security_test_id, not both.')

        # Get a Phishing Security Test From a Specific Campaign:
        # https://developer.knowbe4.com/reporting/#tag/Phishing/paths/~1v1~1phishing~1campaigns~1{campaign_id}~1security_tests/get
        if campaign_id:
            return [PhishingSecurityTest.from_dict(pst)
                    for pst in self._request(method="GET", url=f'campaigns/{campaign_id}/security_tests')]

        # Get a Specific PST
        # https://developer.knowbe4.com/reporting/#tag/Phishing/paths/~1v1~1phishing~1security_tests~1{pst_id}/get
        elif phishing_security_test_id:
            return [PhishingSecurityTest.from_dict(pst)
                    for pst in self._request(method="GET", url=f'security_tests/{phishing_security_test_id}')]

        # Get All Phishing Security Tests:
        # https://developer.knowbe4.com/reporting/#tag/Phishing/paths/~1v1~1phishing~1security_tests/get
        else:
            return [PhishingSecurityTest.from_dict(pst)
                    for pst in self._request(method="GET", url=f'security_tests')]

    def get_security_test_results(self, phishing_security_test_id: int = None, recipient_id: int = None) -> list:

        """Retrieves all recipients (or a specific recipient if a user_id is provided) from a phishing security test in
        your KnowBe4 account.

        :parameter phishing_security_test_id: an int, a phishing security test ID to filter on
        :parameter recipient_id: an int, a recipient ID to filter on
        :return: a list, API response(s)
        :rtype: list
        """

        if not phishing_security_test_id:
            raise ValueError("A value must be provided for phishing_security_test_id.")

        # Get a Specific Recipient's Results
        # https://developer.knowbe4.com/reporting/#tag/Phishing/paths/~1v1~1phishing~1security_tests~1{pst_id}~1recipients~1{recipient_id}/get
        if recipient_id:
            return [PhishingCampaignRecipient.from_dict(pcr)
                    for pcr in self._request(method="GET", url=f'security_tests/{phishing_security_test_id}/recipients/{recipient_id}')]

        # Get All Recipient Results
        # https://developer.knowbe4.com/reporting/#tag/Phishing/paths/~1v1~1phishing~1security_tests~1{pst_id}~1recipients/get
        else:
            return [PhishingCampaignRecipient.from_dict(pcr) for pcr
                    in self._request(method="GET", url=f'security_tests/{phishing_security_test_id}/recipients')]
