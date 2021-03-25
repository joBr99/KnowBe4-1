class KnowBe4Exception(Exception):
    pass


class AuthorizationError(KnowBe4Exception):

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg