import os
import uuid

import responses
from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpRequest
from django.test import Client, TransactionTestCase


def resource(name: str, mode: str = 'r'):
    return open(os.path.join(settings.BASE_DIR, 'fixtures', name), mode)


class Accounts(TransactionTestCase):
    def setUp(self):
        self.client = Client()

    def test_cas_login(self):
        req = HttpRequest()
        req.session = {}
        with responses.RequestsMock() as r, resource('login.xml', 'rb') as body:
            r.add(responses.POST, 'https://sistemas.ufsc.br/samlValidate',
                  body=body.read())
            self.client.login(ticket=f'ST-{uuid.uuid4()}',
                              service=settings.CAS_SERVER_URL,
                              request=req)

        # ensure user is created with correct data
        self.assertEqual(1, User.objects.count())

        user = User.objects.get()
        self.assertEqual('100000000400000', user.get_username())
        self.assertEqual('John Edward', user.first_name)
        self.assertEqual('Gammell', user.last_name)
        self.assertEqual('john@gmail.com', user.email)

    def test_cas_login_long_name(self):
        req = HttpRequest()
        req.session = {}
        with responses.RequestsMock() as r, resource('login-longname.xml',
                                                     'rb') as body:
            r.add(responses.POST, 'https://sistemas.ufsc.br/samlValidate',
                  body=body.read())
            self.client.login(ticket=f'ST-{uuid.uuid4()}',
                              service=settings.CAS_SERVER_URL,
                              request=req)

        user = User.objects.get()
        self.assertEqual('Carolina Josefa Leopoldina de', user.first_name)
        self.assertEqual('Habsburgo-Lorena', user.last_name)
