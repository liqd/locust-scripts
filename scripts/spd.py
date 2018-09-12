from enum import Enum
from faker import Faker
from locust import HttpLocust, TaskSet, task
from pyquery import PyQuery
import random
import json

from credz import USER_CREDENTIALS

class SPDBrowser(TaskSet):

    def on_start(self):
        self.urls = []
        self.objectIds = []

    def login(self):
        r = self.client.get("django-admin/")
        csrf = self.client.cookies['csrftoken']

        if not USER_CREDENTIALS:
            self.interrupt()

        user, pwd = random.choice(USER_CREDENTIALS)
        print("logging in as {}".format(user))

        header = { "Referer": r.url }

        with self.client.post("django-admin/", data={
                "csrfmiddlewaretoken": csrf,
                "username": user,
                "password": pwd
                }, catch_response=True, headers=header) as r:

            pq = PyQuery(r.content)
            alertbox = pq("p").filter(".errornote")
            assert(not alertbox)

    def logout(self):
        self.client.get("admin/logout/")

    @task(50)
    def step_1(self):
        self.client.get("/")

    @task(49)
    def step_2(self):
        self.login()

    @task(48)
    def step_3(self):
        self.client.get("/")

    @task(47)
    def step_4(self):
        self.client.get("project-page-title-1/")

    @task(46)
    def step_5(self):
        self.client.get("questions/6/")

    @task(45)
    def step_6(self):
        self.client.get("project-page-title-1/")

    @task(44)
    def step_7(self):
        self.client.get("debattencamp/")

    @task(43)
    def step_8(self):
        self.client.get("statements/online-und-offline-der-parteiarbeit-besser-verbind/")

    @task(42)
    def step_9(self):
        self.logout()

class WebsiteUser(HttpLocust):
    # to call via
    #   $ locust -f locustfile.py --host <host>
    task_set = SPDBrowser
    min_wait = 10000
    max_wait = 60000
