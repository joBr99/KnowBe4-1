import os
import time
import requests
from dataclasses import dataclass, field, asdict
from .exceptions import AuthorizationError

_GROUP_CACHE = {}
_PSTS_CACHE = {}


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
    current_risk_score: int
    risk_score_history: list
    status: str


@dataclass()
class TrainingEnrollment(Datacls):
    campaign_name: str
    completion_date: str
    content_type: str
    enrollment_date: str
    enrollment_id: int
    module_name: str
    policy_acknowledged: bool
    start_date: str
    status: str = field(init=True)
    time_spent: int
    employee_upn: str
    employee_id: int

    def __post_init__(self):
        self.status = self.set_status()

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
    groups: list = field(init=True)
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

        groups = []

        for group in self.groups:

            if isinstance(group, int):
                group_id = group
                if group in _GROUP_CACHE:
                    groups.append(_GROUP_CACHE[group])
                else:
                    if group != 0:
                        group_obj = Group.from_dict(api._request(method="GET", url=f'groups/{group_id}')[0])
                        groups.append(group_obj)
                        _GROUP_CACHE[group_id] = group_obj
                    else:
                        pass
            elif isinstance(group, dict):
                group_id = group.get("group_id")
                if group_id in _GROUP_CACHE:
                    groups.append(_GROUP_CACHE[group_id])
                else:
                    if group_id != 0:
                        group_obj = Group.from_dict(api._request(method="GET", url=f'groups/{group_id}')[0])
                        groups.append(group_obj)
                        _GROUP_CACHE[group_id] = group_obj
                    else:
                        pass
        return groups


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

        groups = []

        for group in self.groups:

            if isinstance(group, int):
                group_id = group
                if group in _GROUP_CACHE:
                    groups.append(_GROUP_CACHE[group])
                else:
                    if group != 0:
                        group_obj = Group.from_dict(api._request(method="GET", url=f'groups/{group_id}')[0])
                        groups.append(group_obj)
                        _GROUP_CACHE[group_id] = group_obj
                    else:
                        pass
            elif isinstance(group, dict):
                group_id = group.get("group_id")
                if group_id in _GROUP_CACHE:
                    groups.append(_GROUP_CACHE[group_id])
                else:
                    if group_id != 0:
                        group_obj = Group.from_dict(api._request(method="GET", url=f'groups/{group_id}')[0])
                        groups.append(group_obj)
                        _GROUP_CACHE[group_id] = group_obj
                    else:
                        pass
        return groups


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

        groups = []

        for group in self.groups:

            if isinstance(group, int):
                group_id = group
                if group in _GROUP_CACHE:
                    groups.append(_GROUP_CACHE[group])
                else:
                    if group != 0:
                        group_obj = Group.from_dict(api._request(method="GET", url=f'groups/{group_id}')[0])
                        groups.append(group_obj)
                        _GROUP_CACHE[group_id] = group_obj
                    else:
                        pass
            elif isinstance(group, dict):
                group_id = group.get("group_id")
                if group_id in _GROUP_CACHE:
                    groups.append(_GROUP_CACHE[group_id])
                else:
                    if group_id != 0:
                        group_obj = Group.from_dict(api._request(method="GET", url=f'groups/{group_id}')[0])
                        groups.append(group_obj)
                        _GROUP_CACHE[group_id] = group_obj
                    else:
                        pass
        return groups


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

        groups = []

        for group in self.groups:

            if isinstance(group, int):
                group_id = group
                if group in _GROUP_CACHE:
                    groups.append(_GROUP_CACHE[group])
                else:
                    if group != 0:
                        group_obj = Group.from_dict(api._request(method="GET", url=f'groups/{group_id}')[0])
                        groups.append(group_obj)
                        _GROUP_CACHE[group_id] = group_obj
                    else:
                        pass
            elif isinstance(group, dict):
                group_id = group.get("group_id")
                if group_id in _GROUP_CACHE:
                    groups.append(_GROUP_CACHE[group_id])
                else:
                    if group_id != 0:
                        group_obj = Group.from_dict(api._request(method="GET", url=f'groups/{group_id}')[0])
                        groups.append(group_obj)
                        _GROUP_CACHE[group_id] = group_obj
                    else:
                        pass
        return groups

    def set_phishing_security_tests(self):

        api = API()

        psts = []

        for pst in self.psts:

            if isinstance(pst, int):
                pst_id = pst
                if pst in _PSTS_CACHE:
                    print("PST found in CACHE")
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
                    print("PST found in CACHE")
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
