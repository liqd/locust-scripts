from enum import Enum
from faker import Faker
from locust import HttpLocust, TaskSet, task
from pyquery import PyQuery
import random
import json

from credz import USER_CREDENTIALS


fake = Faker()


class PageType(Enum):
    IDEA = 1
    IDEASPACE = 2


def _process_ideaspace(l, pagecontent):
    pq = PyQuery(pagecontent)
    links = []

    # get idea links
    link_elements = pq("a").filter(".idealist-image")
    links.extend([
        (PageType.IDEA, a.attrib["href"]) for a in link_elements
    ])

    # get pagination links
    next_pages = pq("ul").filter(".pagination").eq(0).find('a')
    links.extend([
        (PageType.IDEASPACE, "/ideas/" + a.attrib["href"]) for a in next_pages
    ])

    l.urls = links


def _process_idea(l, pagecontent):
    pq = PyQuery(pagecontent)
    # TODO for now we only fetch object ids of ideas, so
    # commenting/rating comments not possible for now
    objectIds = pq('a[data-ae-widget="supports"]')[:1]

    l.objectIds += [
        get_objectId(o) for o in objectIds
    ]


def surf_ideaspace(l, status="", ordering="", page=1):
    url = "/ideas/?ordering={ordering}&status={status}&page={page}".format(
            status=status,
            ordering=ordering,
            page=page
        )
    r = l.client.get(url)
    _process_ideaspace(l, r.content)


def get_objectId(elem):
    data_str = elem.attrib["data-attributes"]
    data_json = json.loads(data_str)
    return (data_json["objectId"], data_json["contentType"])


def load_page(l):
    r = None

    try:
        pagetype, url = random.choice(l.urls)
        r = l.client.get(url)

        if pagetype == PageType.IDEASPACE:
            _process_ideaspace(l, r.content)
        elif pagetype == PageType.IDEA:
            _process_idea(l, r.content)

    except (IndexError, ValueError):
        pass


class AeContributor(TaskSet):

    def on_start(self):
        self.login()

    def login(self):
        r = self.client.get("/accounts/login/")
        csrf = self.client.cookies['csrftoken']

        if not USER_CREDENTIALS:
            self.interrupt()

        user, pwd = random.choice(USER_CREDENTIALS)
        print("logging in as {}".format(user))

        header = { "Referer": r.url }

        with self.client.post("/accounts/login/", data={
                "csrfmiddlewaretoken": csrf,
                "login": user,
                "password": pwd
                }, catch_response=True, headers=header) as r:

            pq = PyQuery(r.content)
            alertbox = pq("p").filter(".alert-danger")
            assert(not alertbox)

    def _submit(self, data):
        header = { "Referer": self.client.base_url }

        with self.client.post(
            "/ideas/create/module/ideas2017/",
            data=data,
            headers=header,
            catch_response=True) as r:

            pq = PyQuery(r.content)
            errorblock = pq("span").filter(".error-block")
            assert(not errorblock)

    def _submit_step_zero(self):
        data = {
            "idea_sketch_create_wizard-current_step": "0",
            "0-first_name": fake.first_name(),
            "0-last_name": fake.last_name(),
            "0-organisation_status": "other",
            "0-organisation_status_extra": fake.word(),
            "0-organisation_name": "",
            "0-organisation_website": "",
            "0-organisation_country": "",
            "0-organisation_city": "",
            "0-contact_email": "",
            "0-year_of_registration": "",
            "csrfmiddlewaretoken": self.client.cookies['csrftoken']
        }
        self._submit(data)

    def _submit_step_one(self):
        data = {
            "idea_sketch_create_wizard-current_step": "1",
            "csrfmiddlewaretoken": self.client.cookies['csrftoken'],
            "1-partner_organisation_1_name": "",
            "1-partner_organisation_1_website": "",
            "1-partner_organisation_1_country": "",
            "1-partner_organisation_2_name": "",
            "1-partner_organisation_2_website": "",
            "1-partner_organisation_2_country": "",
            "1-partner_organisation_3_name": "",
            "1-partner_organisation_3_website": "",
            "1-partner_organisation_3_country": "",
            "1-partners_more_info": "",
        }
        self._submit(data)

    def _submit_step_two(self):
        data = {
            "idea_sketch_create_wizard-current_step": "2",
            "csrfmiddlewaretoken": self.client.cookies['csrftoken'],
            "2-idea_title": fake.sentence(nb_words=4),
            "2-idea_subtitle": fake.sentence(nb_words=6),
            "2-idea_pitch": fake.text(max_nb_chars=200),
            "2-idea_topics": random.choice([
                    "migration",
                    "education",
                    "communities",
                    "environment"
            ]),
            "2-idea_topics_other": "",
            "2-idea_location": "online",
            "2-idea_location_specify": "",
            "2-idea_location_ruhr": ""
        }
        self._submit(data)

    def _submit_step_three(self):
        data = {
            "idea_sketch_create_wizard-current_step": "3",
            "csrfmiddlewaretoken": self.client.cookies['csrftoken'],
            "3-challenge": fake.sentence(nb_words=10),
            "3-outcome": fake.sentence(nb_words=10),
            "3-plan": fake.sentence(nb_words=10),
            "3-importance": fake.sentence(nb_words=10),
            "3-target_group": fake.sentence(nb_words=10),
            "3-members": fake.word()
        }
        self._submit(data)

    def _submit_step_four(self):
        data = {
            "idea_sketch_create_wizard-current_step": "4",
            "csrfmiddlewaretoken": self.client.cookies['csrftoken'],
            "4-collaboration_camp_represent": fake.name(),
            "4-collaboration_camp_benefit": fake.sentence(nb_words=10)
        }
        self._submit(data)

    def _submit_step_five(self):
        data = {
            "idea_sketch_create_wizard-current_step": "5",
            "csrfmiddlewaretoken": self.client.cookies['csrftoken'],
            "5-co_workers_emails": "",
            "5-reach_out": "",
            "5-how_did_you_hear": "personal_contact",
            "5-confirm_publicity": "on",
            "5-confirm_collaboration_camp": "on",
            "5-accept_conditions": "on"
        }
        self._submit(data)

    def _submit_step_six(self):
        data = {
            "idea_sketch_create_wizard-current_step": "6",
            "csrfmiddlewaretoken": self.client.cookies['csrftoken'],
        }
        self._submit(data)

    @task(100)
    def submit_idea(self):
        self._submit_step_zero()
        self._submit_step_one()
        self._submit_step_two()
        self._submit_step_three()
        self._submit_step_four()
        self._submit_step_five()
        self._submit_step_six()


class AeFeedbacker(TaskSet):
    tasks = {
        surf_ideaspace: 20,
        load_page: 5
    }

    def on_start(self):
        self.urls = []
        self.objectIds = []
        self.alreadyrated = dict()
        self.login()

    def login(self):
        r = self.client.get("/accounts/login")
        csrf = self.client.cookies['csrftoken']

        if not USER_CREDENTIALS:
            self.interrupt()

#       user, pwd = random.choice(USER_CREDENTIALS)
        user, pwd = USER_CREDENTIALS.pop()
        print("logging in as {}".format(user))

        with self.client.post("/accounts/login/", data={
                "csrfmiddlewaretoken": csrf,
                "login": user,
                "password": pwd
                }, catch_response=True) as r:

            pq = PyQuery(r.content)
            alertbox = pq("p").filter(".alert-danger")
            assert(not alertbox)

    @task(10)
    def comment(self):
        try:
            objectId, contentType = random.choice(self.objectIds)
            csrf = self.client.cookies['csrftoken']

            data = {"comment": "a locust was here"}
            header = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-CSRFToken": csrf
            }

            self.client.post(
                "/api/contenttypes/{type}/objects/{id}/comments/"
                .format(id=objectId, type=contentType),
                data=json.dumps(data),
                headers=header
            )

        except IndexError:
            pass

    @task(5)
    def support(self):
        try:
            objectId, contentType = random.choice(self.objectIds)
            csrf = self.client.cookies['csrftoken']

            header = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-CSRFToken": csrf
            }

            if str(objectId) in self.alreadyrated:
                data = {"value": random.choice([-1, 0])}
                comment = self.alreadyrated[str(objectId)]

                r = self.client.patch(
                        "/api/contenttypes/{type}/objects/{iid}/ratings/{cid}/"
                        .format(iid=objectId, cid=comment, type=contentType),
                        data=json.dumps(data),
                        headers=header
                )

            else:
                data = {"value": random.choice([-1, 1])}

                r = self.client.post(
                        "/api/contenttypes/{type}/objects/{iid}/ratings/"
                        .format(iid=objectId, type=contentType),
                        data=json.dumps(data),
                        headers=header
                )
                if r.status_code == 201:
                    jsondata = json.loads(r.content)
                    self.alreadyrated[str(objectId)] = jsondata["id"]

        except IndexError:
            pass

    @task(2)
    def stop(self):
        self.interrupt()


class AeBrowser(TaskSet):
    tasks = {
        AeContributor: 2,
        AeFeedbacker: 5,
        surf_ideaspace: 30,
        load_page: 20
    }

    def on_start(self):
        self.index()
        self.urls = []
        self.objectIds = []

    @task(50)
    def index(self):
        self.client.get("/")

    @task(20)
    def idea_filter(self):
        status = random.choice([
            "winner", "proposal", "idea_sketch", "shortlist"
        ])
        ordering = random.choice([
            "newest", "comments", "support", "title"
        ])
        surf_ideaspace(self, status=status, ordering=ordering)

    @task(5)
    def stories(self):
        r = self.client.get("/blog")
        pq = PyQuery(r.content)
        link_elements = pq("a").filter(".hover-child-img")
        self.urls = [
            a.attrib["href"] for a in link_elements
        ]

    @task(1)
    def about(self):
        self.client.get("/about")

    @task(1)
    def terms(self):
        self.client.get("/terms-use")

    @task(1)
    def login(self):
        self.client.get("/accounts/login")

    @task(1)
    def register(self):
        self.client.get("/accounts/signup")


class WebsiteUser(HttpLocust):
    # to call via
    #   $ locust -f locustfile.py --host <host>
    task_set = AeContributor
