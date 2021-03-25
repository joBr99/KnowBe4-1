import os
from training import Training
from account import Account
from users import Users
from groups import Groups
from phishing import Phishing


class KB4:

    training = Training()
    account = Account()
    users = Users()
    groups = Groups()
    phishing = Phishing()

    @staticmethod
    def reset_auth_token():
        os.environ.pop('kb4-api-key')
        api_token = input('Please enter your KnowBe4 API Token: ')
        os.environ['kb4-api-key'] = api_token
        print("Please reboot your system for the change to take effect.")
        return True
