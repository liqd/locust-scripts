from enum import Enum
from faker import Faker
from locust import FastHttpUser, TaskSet, task
from locust.exception import InterruptTaskSet
from pyquery import PyQuery
import random
import json

from credz import USER_CREDENTIALS

fake = Faker()

# replace with url of a budgeting project
budgeting_url = "/budgeting/create/module/participatory-budgeting-3-phase-2/"


def get_csrf_token(cookiejar):
    csrf = ""
    for cookie in cookiejar:
        if cookie.name == "csrftoken":
            csrf = cookie.value
    return csrf


class MeinBerlinBudgetingIdeaCreator(TaskSet):
    def on_start(self):
        self.login()

    @task(1)
    def create_idea(self):
        self._submit_idea()

    def _submit(self, data):
        header = {"Referer": self.client.base_url}

        with self.client.post(
            budgeting_url, data=data, headers=header, catch_response=True
        ) as r:

            pq = PyQuery(r.text)
            errorlist = pq(".errorlist")
            if errorlist:
                r.failure("Idea creation failed")
                raise InterruptTaskSet(reschedule=False)

    def _submit_idea(self):
        data = {
            "csrfmiddlewaretoken": get_csrf_token(self.client.cookiejar),
            "name": fake.word(),
            "description": fake.paragraph(nb_sentences=5),
            "image": "",
            "__noname__": "",
            "budget": 0,
            "Address": "Hauptstrasse",
            "point": json.dumps(
                {
                    "type": "Feature",
                    "properties": {},
                    "geometry": {
                        "type": "Point",
                        "coordinates": [13.282471, 52.509375],
                    },
                }
            ),
            "point_label": "",
        }
        self._submit(data)

    def login(self):
        r = self.client.get("/accounts/login/")

        if not USER_CREDENTIALS:
            self.interrupt()

        user, pwd = random.choice(USER_CREDENTIALS)
        print("logging in as {}".format(user))

        header = {"Referer": r.url}

        with self.client.post(
            "/accounts/login/",
            data={
                "csrfmiddlewaretoken": get_csrf_token(self.client.cookiejar),
                "login": user,
                "password": pwd,
            },
            catch_response=True,
            headers=header,
        ) as r:

            pq = PyQuery(r.text)
            errorlist = pq(".errorlist")
            if errorlist:
                r.failure("Login failed")
                raise InterruptTaskSet(reschedule=False)


class MeinBerlinProjectBrowser(TaskSet):
    def on_start(self):
        self.active_projects = []
        self.past_projects = []
        self.future_projects = []
        self.load_active_projects()
        self.load_past_projects()
        self.load_future_projects()

    @task(30)
    def random_active_project(self):
        if len(self.active_projects) > 0:
            self.client.get(random.choice(self.active_projects))

    @task(20)
    def random_past_project(self):
        if len(self.past_projects) > 0:
            self.client.get(random.choice(self.past_projects))

    @task(10)
    def random_future_project(self):
        if len(self.future_projects) > 0:
            self.client.get(random.choice(self.future_projects))

    def load_active_projects(self):
        response = self.client.get("/api/projects/?status=activeParticipation")
        projects = json.loads(response.content)
        self.active_projects += [project["url"] for project in projects]

    def load_past_projects(self):
        response = self.client.get("/api/projects/?status=pastParticipation")
        projects = json.loads(response.content)
        self.past_projects += [project["url"] for project in projects]

    def load_future_projects(self):
        response = self.client.get("/api/projects/?status=futureParticipation")
        projects = json.loads(response.content)
        self.future_projects += [project["url"] for project in projects]


class MeinBerlinBrowser(TaskSet):
    @task(50)
    def index(self):
        self.client.get("/")

    @task(50)
    def projects(self):
        self.client.get("/projekte")

    @task(1)
    def terms(self):
        self.client.get("/impressum")

    @task(1)
    def terms(self):
        self.client.get("/datenschutzerklärung")

    @task(1)
    def terms(self):
        self.client.get("/nutzungsbedingungen")

    @task(1)
    def login(self):
        self.client.get("/accounts/login")

    @task(1)
    def register(self):
        self.client.get("/accounts/signup")

    @task(1)
    def error_page(self):
        self.client.get("/thisisvoid")


class WebsiteUser(FastHttpUser):
    # to call via
    #   $ locust -f locustfile.py --host <host>
    #    tasks = [MeinBerlinProjectBrowser]
    tasks = [MeinBerlinBudgetingIdeaCreator]
    # tasks = [MeinBerlinBudgetingIdeaCreator, MeinBerlinBrowser, MeinBerlinProjectBrowser]
    # tasks = [MeinBerlinBrowser, MeinBerlinProjectBrowser]
