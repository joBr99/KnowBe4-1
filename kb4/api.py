import os
import time
import requests
from dataclasses import dataclass, field, asdict
from .exceptions import AuthorizationError

_GROUP_CACHE = {}
_PSTS_CACHE = {}
_USER_CACHE = {}


class API:

    def __init__(self):
        self._authToken = os.environ.get("kb4-api-key")
        self._domain = "https://us.api.knowbe4.com/v1"
        self._results_per_page = 500

    def _build_url(self, endpoint: str) -> str:
        return f'{self._domain}/{endpoint}'

    def _verify_auth_token(self):
        if not self._authToken:
            api_token = input('Please enter your KnowBe4 API Token: ')
            print("Note: You may be prompted for you API token everytime you call the KB4 class until you reboot your "
                  "system.")
            os.environ['kb4-api-key'] = api_token
            self._authToken = api_token

    def _set_headers(self):
        return {'Authorization': self._authToken}

    def _set_params(self, page: int = 1):
        return {'page': page, 'per_page': self._results_per_page}

    @staticmethod
    def _json(response):
        if not response:
            return None
        else:
            return response.json()

    def _request(self, method: str, url: str, params: dict = None, json: dict = None, headers: dict = None):

        parameters = self._set_params()

        if params:
            parameters.update(params)

        self._verify_auth_token()
        headers = self._set_headers()
        url = self._build_url(url)

        results = []

        def pagination_handler():

            has_next = True
            terminate = False

            while has_next and not terminate:

                try:
                    response = requests.request(method=method, url=url, params=parameters, json=json, headers=headers)
                    response.raise_for_status()

                except requests.exceptions.HTTPError as http_err:

                    response = http_err.response

                    if response.status_code == 401:
                        raise AuthorizationError(f'HTTP Error ({response.status_code}: Check your API token and try '
                                                 f'again. Run KB4.reset_auth_token to overwrite the current key.')

                    else:
                        response.raise_for_status()

                else:

                    # Extract JSON from response and append values to results
                    response = self._json(response)

                    if isinstance(response, list):
                        results.extend(response)
                    elif isinstance(response, dict):
                        results.append(response)

                    if len(response) != self._results_per_page:
                        has_next, terminate = False, True

                    else:
                        has_next = True
                        parameters['page'] += 1

        pagination_handler()

        return results


@dataclass()
class Datacls:
    pass

    @classmethod
    def from_dict(cls, obj):
        return cls(**obj)

    def to_dict(self):
        return asdict(self)


@dataclass()
class Group(Datacls):
    id: int
    name: str
    group_type: str
    adi_guid: str
    member_count: int
    current_risk_score: int = field(repr=False)
    risk_score_history: list = field(repr=False)
    status: str


@dataclass()
class TrainingEnrollment(Datacls):
    enrollment_id: int
    content_type: str
    module_name: str
    campaign_name: str
    enrollment_date: str
    start_date: str
    completion_date: str
    status: str = field(init=True)
    time_spent: int
    policy_acknowledged: bool
    email: str = field(init=False)
    firstname: str = field(init=False)
    lastname: str = field(init=False)
    location: str = field(init=False)
    division: str = field(init=False)
    user_status: str = field(init=False)
    user: dict = field(repr=False)

    def __post_init__(self):
        self.user = self.get_user()
        self.status = self.set_status()
        self.email = self.user.email
        self.firstname = self.user.first_name
        self.lastname = self.user.last_name
        self.location = self.user.location
        self.division = self.user.division
        self.user_status = self.user.status

    def set_status(self):
        if self.status == 'In Progress' and self.time_spent == 0:
            self.status = "Not Started"
        elif self.status == 'Passed':
            self.status = "Completed"
        elif self.status == 'Past Due' and self.time_spent > 0:
            self.status = "In Progress"
        elif self.status == 'Past Due' and self.time_spent == 0:
            self.status = "Not Started"
        return self.status

    def get_user(self):

        api = API()

        user_id = self.user.get("id")

        if not _USER_CACHE:
            users = api._request(method="GET", url=f'users')
            _USER_CACHE.update({user['id']: User.from_dict(user) for user in users})

        if user_id in _USER_CACHE.keys():
            return _USER_CACHE[user_id]
        else:
            user_obj = User.from_dict(api._request(method="GET", url=f'users/{user_id}')[0])
            _USER_CACHE[user_id] = user_obj
            return user_obj


@dataclass()
class StorePurchase(Datacls):
    store_purchase_id: int
    content_type: str
    name: str
    description: str
    type: str
    duration: int
    retired: bool
    retirement_date: str
    published_date: str
    publisher: str
    purchase_date: str
    policy_url: str


@dataclass()
class Policy(Datacls):
    id: int
    content_type: str
    name: str
    minimum_time: int
    default_language: str
    status: int


@dataclass()
class TrainingCampaign(Datacls):
    campaign_id: int
    name: str
    groups: list = field(repr=True)
    status: str
    modules: list
    content: list
    duration_type: str
    start_date: str
    end_date: str
    relative_duration: str
    auto_enroll: bool
    allow_multiple_enrollments: bool
    completion_percentage: int

    def __post_init__(self):
        self.groups = self.set_groups()

    def set_groups(self):

        api = API()

        group_objs = []

        for group in self.groups:

            if not _GROUP_CACHE:
                groups = api._request(method="GET", url=f'groups')
                _GROUP_CACHE.update({group['id']: Group.from_dict(group) for group in groups})

            if isinstance(group, int):
                pass
            elif isinstance(group, dict):
                group = group.get("group_id")

            if group in _GROUP_CACHE.keys():
                group_objs.append(_GROUP_CACHE[group])
            else:
                if group != 0:
                    group_obj = api._request(method="GET", url=f'groups/{group}')[0]
                    _GROUP_CACHE.update({group_obj.id: group_obj})
                    group_objs.append(group_obj)
                else:
                    pass

        return group_objs


@dataclass()
class User(Datacls):
    id: int
    employee_number: int
    first_name: str
    last_name: str
    job_title: str
    email: str
    phish_prone_percentage: int
    phone_number: str
    extension: str
    mobile_phone_number: str
    location: str
    division: str
    manager_name: str
    manager_email: str
    adi_manageable: bool
    adi_guid: str
    groups: list = field(init=True)
    current_risk_score: int
    risk_score_history: list
    aliases: list
    joined_on: str
    last_sign_in: str
    status: str
    organization: str
    department: str
    language: str
    comment: str
    employee_start_date: str
    archived_at: str
    custom_field_1: str
    custom_field_2: str
    custom_field_3: str
    custom_field_4: str
    custom_date_1: str
    custom_date_2: str

    def __post_init__(self):
        self.groups = self.set_groups()

    def set_groups(self):

        api = API()

        group_objs = []

        for group in self.groups:

            if not _GROUP_CACHE:
                groups = api._request(method="GET", url=f'groups')
                _GROUP_CACHE.update({group['id']: Group.from_dict(group) for group in groups})

            if isinstance(group, int):
                pass
            elif isinstance(group, dict):
                group = group.get("group_id")

            if group in _GROUP_CACHE.keys():
                group_objs.append(_GROUP_CACHE[group])
            else:
                if group != 0:
                    group_obj = api._request(method="GET", url=f'groups/{group}')[0]
                    _GROUP_CACHE.update({group_obj.id: group_obj})
                    group_objs.append(group_obj)
                else:
                    pass

        return group_objs


@dataclass()
class PhishingSecurityTest(Datacls):
    campaign_id: int
    pst_id: int
    status: str
    name: str
    groups: list = field(init=True)
    phish_prone_percentage: int
    started_at: str
    duration: int
    categories: list
    template: dict
    landing_page: dict
    scheduled_count: int
    delivered_count: int
    opened_count: int
    clicked_count: int
    replied_count: int
    attachment_open_count: int
    macro_enabled_count: int
    data_entered_count: int
    vulnerable_plugin_count: int
    exploited_count: int
    reported_count: int
    bounced_count: int

    def __post_init__(self):
        self.groups = self.set_groups()

    def set_groups(self):

        api = API()

        group_objs = []

        for group in self.groups:

            if not _GROUP_CACHE:
                groups = api._request(method="GET", url=f'groups')
                _GROUP_CACHE.update({group['id']: Group.from_dict(group) for group in groups})

            if isinstance(group, int):
                pass
            elif isinstance(group, dict):
                group = group.get("group_id")

            if group in _GROUP_CACHE.keys():
                group_objs.append(_GROUP_CACHE[group])
            else:
                if group != 0:
                    group_obj = api._request(method="GET", url=f'groups/{group}')[0]
                    _GROUP_CACHE.update({group_obj.id: group_obj})
                    group_objs.append(group_obj)
                else:
                    pass

        return group_objs


@dataclass()
class PhishingCampaign(Datacls):
    campaign_id: int
    name: str
    groups: list = field(init=True)
    last_phish_prone_percentage: int
    last_run: str
    status: str
    hidden: bool
    send_duration: str
    track_duration: str
    frequency: str
    difficulty_filter: list
    create_date: str
    psts_count: bool
    psts: list = field(init=True)

    def __post_init__(self):
        self.groups = self.set_groups()
        self.psts = self.set_phishing_security_tests()

    def set_groups(self):

        api = API()

        group_objs = []

        for group in self.groups:

            if not _GROUP_CACHE:
                groups = api._request(method="GET", url=f'groups')
                _GROUP_CACHE.update({group['id']: Group.from_dict(group) for group in groups})

            if isinstance(group, int):
                pass
            elif isinstance(group, dict):
                group = group.get("group_id")

            if group in _GROUP_CACHE.keys():
                group_objs.append(_GROUP_CACHE[group])
            else:
                if group != 0:
                    group_obj = api._request(method="GET", url=f'groups/{group}')[0]
                    _GROUP_CACHE.update({group_obj.id: group_obj})
                    group_objs.append(group_obj)
                else:
                    pass

        return group_objs

    def set_phishing_security_tests(self):

        api = API()

        psts = []

        for pst in self.psts:

            if isinstance(pst, int):
                pst_id = pst
                if pst in _PSTS_CACHE:
                    psts.append(_GROUP_CACHE[pst])
                else:
                    if pst != 0:
                        pst_obj = PhishingSecurityTest.from_dict(
                            api._request(method="GET", url=f'phishing/security_tests/{pst}')[0])
                        psts.append(pst_obj)
                        _PSTS_CACHE[pst_id] = pst_obj
                    else:
                        pass
            elif isinstance(pst, dict):
                pst_id = pst.get("pst_id")
                if pst_id in _PSTS_CACHE:
                    psts.append(_PSTS_CACHE[pst_id])
                else:
                    if pst_id != 0:
                        psts_obj = PhishingSecurityTest.from_dict(
                            api._request(method="GET", url=f'phishing/security_tests/{pst.get("pst_id")}')[0])
                        psts.append(psts_obj)
                        _PSTS_CACHE[pst_id] = psts_obj
                    else:
                        pass
        return psts


@dataclass()
class PhishingCampaignRecipient(Datacls):
    recipient_id: int
    pst_id: int
    user: dict = field(init=True)
    template: dict
    scheduled_at: str
    delivered_at: str
    opened_at: str
    clicked_at: str
    replied_at: str
    attachment_opened_at: str
    macro_enabled_at: str
    data_entered_at: str
    vulnerable_plugins_at: str
    exploited_at: str
    reported_at: str
    bounced_at: str
    ip: str
    ip_location: str
    browser: str
    browser_version: str
    os: str
