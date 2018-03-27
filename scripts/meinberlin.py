from enum import Enum
from faker import Faker
from locust import HttpLocust, TaskSet, task
from pyquery import PyQuery
import random
import json

from credz import USER_CREDENTIALS


fake = Faker()


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


class MeinBerlinBrowser(TaskSet):

    def on_start(self):
        self.index()
        self.urls = []
        self.objectIds = []

    @task(50)
    def index(self):
        self.client.get("/")

    @task(1)
    def terms(self):
        self.client.get("/impressum")

    @task(1)
    def terms(self):
        self.client.get("/datenschutz")

    @task(1)
    def terms(self):
        self.client.get("/terms-of-use")

    @task(1)
    def login(self):
        self.client.get("/accounts/login")

    @task(1)
    def register(self):
        self.client.get("/accounts/signup")


class WebsiteUser(HttpLocust):
    # to call via
    #   $ locust -f locustfile.py --host <host>
    task_set = MeinBerlinBrowser
