from enum import Enum
from locust import HttpLocust, TaskSet, task
from pyquery import PyQuery
import random
import json

from credz import USER_CREDENTIALS


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

    except IndexError:
        pass


class AeContributor(TaskSet):

    def on_start(self):
        self.login()

    def login(self):
        self.client.get("/accounts/login")
        csrf = self.client.cookies['csrftoken']

        if not USER_CREDENTIALS:
            self.interrupt()

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

    def submit_idea(self):
        # TODO
        pass


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
        AeFeedbacker: 10,
        surf_ideaspace: 30,
        load_page: 5
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
    task_set = AeBrowser
