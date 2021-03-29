import os
import time
import requests
from dataclasses import dataclass, field
from .exceptions import AuthorizationError


class API:

    GROUP_CACHE = {}
    PSTS_CACHE = {}

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

        return results


@dataclass()
class Group:
    id: int
    name: str
    group_type: str
    adi_guid: str
    member_count: int
    current_risk_score: int
    risk_score_history: list
    status: str

    @classmethod
    def from_json(cls, obj):
        return cls(
            id=obj.get('id'),
            name=obj.get('name'),
            group_type=obj.get('group_type'),
            adi_guid=obj.get('adi_guid'),
            member_count=obj.get('member_count'),
            current_risk_score=obj.get('current_risk_score'),
            risk_score_history=obj.get('risk_score_history'),
            status=obj.get('status')
            )


@dataclass()
class TrainingEnrollment:
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

    @classmethod
    def from_json(cls, obj):
        return cls(
            campaign_name=obj.get('campaign_name'),
            completion_date=obj.get('completion_date'),
            content_type=obj.get('content_type'),
            enrollment_date=obj.get('enrollment_date'),
            enrollment_id=obj.get('enrollment_id'),
            module_name=obj.get('module_name'),
            policy_acknowledged=obj.get('policy_acknowledged'),
            start_date=obj.get('start_date'),
            status=obj.get('status'),
            time_spent=obj.get('time_spent'),
            employee_upn=obj.get('user').get('email'),
            employee_id=obj.get('user').get('id')
            )


@dataclass()
class StorePurchase:
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

    @classmethod
    def from_json(cls, obj):
        return cls(
            store_purchase_id=obj.get('store_purchase_id'),
            content_type=obj.get('content_type'),
            name=obj.get('name'),
            description=obj.get('description'),
            type=obj.get('type'),
            duration=obj.get('duration'),
            retired=obj.get('retired'),
            retirement_date=obj.get('retirement_date'),
            published_date=obj.get('published_date'),
            publisher=obj.get('publisher'),
            purchase_date=obj.get('purchase_date'),
            policy_url=obj.get('policy_url')
            )


@dataclass()
class Policy:
    id: int
    content_type: str
    name: str
    minimum_time: int
    default_language: str
    status: int

    @classmethod
    def from_json(cls, obj):
        return cls(
            id=obj.get('id'),
            content_type=obj.get('content_type'),
            name=obj.get('name'),
            minimum_time=obj.get('minimum_time'),
            default_language=obj.get('default_language'),
            status=obj.get('status')
            )


@dataclass()
class TrainingCampaign:
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
                if group in API.GROUP_CACHE:
                    groups.append(API.GROUP_CACHE[group])
                else:
                    if group != 0:
                        group_obj = Group.from_json(api.request(method="GET", url=f'groups/{group_id}')[0])
                        groups.append(group_obj)
                        API.GROUP_CACHE[group_id] = group_obj
                    else:
                        pass
            elif isinstance(group, dict):
                group_id = group.get("group_id")
                if group_id in API.GROUP_CACHE:
                    groups.append(API.GROUP_CACHE[group_id])
                else:
                    if group_id != 0:
                        group_obj = Group.from_json(api.request(method="GET", url=f'groups/{group_id}')[0])
                        groups.append(group_obj)
                        API.GROUP_CACHE[group_id] = group_obj
                    else:
                        pass
        return groups

    @classmethod
    def from_json(cls, obj):
        return cls(
            campaign_id=obj.get('campaign_id'),
            name=obj.get('name'),
            groups=obj.get('groups'),
            status=obj.get('status'),
            modules=obj.get('modules'),
            content=obj.get('content'),
            duration_type=obj.get('duration_type'),
            start_date=obj.get('start_date'),
            end_date=obj.get('end_date'),
            relative_duration=obj.get('relative_duration'),
            auto_enroll=obj.get('auto_enroll'),
            allow_multiple_enrollments=obj.get('allow_multiple_enrollments'),
            completion_percentage=obj.get('completion_percentage')
            )


@dataclass()
class User:
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
                if group in API.GROUP_CACHE:
                    groups.append(API.GROUP_CACHE[group])
                else:
                    if group != 0:
                        group_obj = Group.from_json(api.request(method="GET", url=f'groups/{group_id}')[0])
                        groups.append(group_obj)
                        API.GROUP_CACHE[group_id] = group_obj
                    else:
                        pass
            elif isinstance(group, dict):
                group_id = group.get("group_id")
                if group_id in API.GROUP_CACHE:
                    groups.append(API.GROUP_CACHE[group_id])
                else:
                    if group_id != 0:
                        group_obj = Group.from_json(api.request(method="GET", url=f'groups/{group_id}')[0])
                        groups.append(group_obj)
                        API.GROUP_CACHE[group_id] = group_obj
                    else:
                        pass
        return groups

    @classmethod
    def from_json(cls, obj):
        return cls(
            id=obj.get('id'),
            employee_number=obj.get('employee_number'),
            first_name=obj.get('first_name'),
            last_name=obj.get('last_name'),
            job_title=obj.get('job_title'),
            email=obj.get('email'),
            phish_prone_percentage=obj.get('phish_prone_percentage'),
            phone_number=obj.get('phone_number'),
            extension=obj.get('extension'),
            mobile_phone_number=obj.get('mobile_phone_number'),
            location=obj.get('location'),
            division=obj.get('division'),
            manager_name=obj.get('manager_name'),
            manager_email=obj.get('manager_email'),
            adi_manageable=obj.get('adi_manageable'),
            adi_guid=obj.get('adi_guid'),
            groups=obj.get('groups'),
            current_risk_score=obj.get('current_risk_score'),
            risk_score_history=obj.get('risk_score_history'),
            aliases=obj.get('aliases'),
            joined_on=obj.get('joined_on'),
            last_sign_in=obj.get('last_sign_in'),
            status=obj.get('status'),
            organization=obj.get('organization'),
            department=obj.get('department'),
            language=obj.get('language'),
            comment=obj.get('comment'),
            employee_start_date=obj.get('employee_start_date'),
            archived_at=obj.get('archived_at'),
            custom_field_1=obj.get('custom_field_1'),
            custom_field_2=obj.get('custom_field_2'),
            custom_field_3=obj.get('custom_field_3'),
            custom_field_4=obj.get('custom_field_4'),
            custom_date_1=obj.get('custom_date_1'),
            custom_date_2=obj.get('custom_date_2'),
            )


@dataclass()
class PhishingSecurityTest:
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
    landing: dict
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
                if group in API.GROUP_CACHE:
                    groups.append(API.GROUP_CACHE[group])
                else:
                    if group != 0:
                        group_obj = Group.from_json(api.request(method="GET", url=f'groups/{group_id}')[0])
                        groups.append(group_obj)
                        API.GROUP_CACHE[group_id] = group_obj
                    else:
                        pass
            elif isinstance(group, dict):
                group_id = group.get("group_id")
                if group_id in API.GROUP_CACHE:
                    groups.append(API.GROUP_CACHE[group_id])
                else:
                    if group_id != 0:
                        group_obj = Group.from_json(api.request(method="GET", url=f'groups/{group_id}')[0])
                        groups.append(group_obj)
                        API.GROUP_CACHE[group_id] = group_obj
                    else:
                        pass
        return groups

    @classmethod
    def from_json(cls, obj):
        return cls(
            campaign_id=obj.get('campaign_id'),
            pst_id=obj.get('pst_id'),
            status=obj.get('status'),
            name=obj.get('name'),
            groups=obj.get('groups'),
            phish_prone_percentage=obj.get('phish_prone_percentage'),
            started_at=obj.get('started_at'),
            duration=obj.get('duration'),
            categories=obj.get('categories'),
            template=obj.get('template'),
            landing=obj.get('landing'),
            scheduled_count=obj.get('scheduled_count'),
            delivered_count=obj.get('delivered_count'),
            opened_count=obj.get('opened_count'),
            clicked_count=obj.get('clicked_count'),
            replied_count=obj.get('replied_count'),
            attachment_open_count=obj.get('attachment_open_count'),
            macro_enabled_count=obj.get('macro_enabled_count'),
            data_entered_count=obj.get('data_entered_count'),
            vulnerable_plugin_count=obj.get('vulnerable_plugin_count'),
            exploited_count=obj.get('exploited_count'),
            reported_count=obj.get('reported_count'),
            bounced_count=obj.get('bounced_count'),
            )


@dataclass()
class PhishingCampaign:
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
                if group in API.GROUP_CACHE:
                    groups.append(API.GROUP_CACHE[group])
                else:
                    if group != 0:
                        group_obj = Group.from_json(api.request(method="GET", url=f'groups/{group_id}')[0])
                        groups.append(group_obj)
                        API.GROUP_CACHE[group_id] = group_obj
                    else:
                        pass
            elif isinstance(group, dict):
                group_id = group.get("group_id")
                if group_id in API.GROUP_CACHE:
                    groups.append(API.GROUP_CACHE[group_id])
                else:
                    if group_id != 0:
                        group_obj = Group.from_json(api.request(method="GET", url=f'groups/{group_id}')[0])
                        groups.append(group_obj)
                        API.GROUP_CACHE[group_id] = group_obj
                    else:
                        pass
        return groups

    def set_phishing_security_tests(self):

        api = API()

        psts = []

        for pst in self.psts:

            if isinstance(pst, int):
                pst_id = pst
                if pst in API.PSTS_CACHE:
                    print("PST found in CACHE")
                    psts.append(API.GROUP_CACHE[pst])
                else:
                    if pst != 0:
                        pst_obj = PhishingSecurityTest.from_json(
                            api.request(method="GET", url=f'phishing/security_tests/{pst}')[0])
                        psts.append(pst_obj)
                        API.PSTS_CACHE[pst_id] = pst_obj
                    else:
                        pass
            elif isinstance(pst, dict):
                pst_id = pst.get("pst_id")
                if pst_id in API.PSTS_CACHE:
                    print("PST found in CACHE")
                    psts.append(API.PSTS_CACHE[pst_id])
                else:
                    if pst_id != 0:
                        psts_obj = PhishingSecurityTest.from_json(
                            api.request(method="GET", url=f'phishing/security_tests/{pst.get("pst_id")}')[0])
                        psts.append(psts_obj)
                        API.PSTS_CACHE[pst_id] = psts_obj
                    else:
                        pass
        return psts

    @classmethod
    def from_json(cls, obj):
        return cls(
            campaign_id=obj.get('campaign_id'),
            name=obj.get('name'),
            groups=obj.get('groups'),
            last_phish_prone_percentage=obj.get('last_phish_prone_percentage'),
            last_run=obj.get('last_run'),
            status=obj.get('status'),
            hidden=obj.get('hidden'),
            send_duration=obj.get('send_duration'),
            track_duration=obj.get('track_duration'),
            frequency=obj.get('frequency'),
            difficulty_filter=obj.get('difficulty_filter'),
            create_date=obj.get('create_date'),
            psts=obj.get('psts'),
            psts_count=obj.get('psts_count')
            )


@dataclass()
class PhishingCampaignRecipient:
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

    def __post_init__(self):
        self.groups = self.set_groups()

    def set_groups(self):

        api = API()

        groups = []

        for group in self.groups:

            if isinstance(group, int):
                group_id = group
                if group in API.GROUP_CACHE:
                    groups.append(API.GROUP_CACHE[group])
                else:
                    if group != 0:
                        group_obj = Group.from_json(api.request(method="GET", url=f'groups/{group_id}')[0])
                        groups.append(group_obj)
                        API.GROUP_CACHE[group_id] = group_obj
                    else:
                        pass
            elif isinstance(group, dict):
                group_id = group.get("group_id")
                if group_id in API.GROUP_CACHE:
                    groups.append(API.GROUP_CACHE[group_id])
                else:
                    if group_id != 0:
                        group_obj = Group.from_json(api.request(method="GET", url=f'groups/{group_id}')[0])
                        groups.append(group_obj)
                        API.GROUP_CACHE[group_id] = group_obj
                    else:
                        pass
        return groups

    @classmethod
    def from_json(cls, obj):
        return cls(
            recipient_id=obj.get('recipient_id'),
            user=obj.get('user'),
            pst_id=obj.get('pst_id'),
            template=obj.get('template'),
            scheduled_at=obj.get('scheduled_at'),
            delivered_at=obj.get('delivered_at'),
            opened_at=obj.get('opened_at'),
            clicked_at=obj.get('clicked_at'),
            replied_at=obj.get('replied_at'),
            attachment_opened_at=obj.get('attachment_opened_at'),
            macro_enabled_at=obj.get('macro_enabled_at'),
            data_entered_at=obj.get('data_entered_at'),
            vulnerable_plugins_at=obj.get('vulnerable_plugins_at'),
            exploited_at=obj.get('exploited_at'),
            reported_at=obj.get('reported_at'),
            bounced_at=obj.get('bounced_at'),
            ip=obj.get('ip'),
            ip_location=obj.get('ip_location'),
            browser=obj.get('browser'),
            browser_version=obj.get('browser_version'),
            os=obj.get('os')
            )