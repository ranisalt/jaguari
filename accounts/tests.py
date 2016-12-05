import os
import responses
import uuid
from django.conf import settings
from django.http import HttpRequest
from django.test import Client, TestCase


def resource(name: str, mode: str = 'r'):
    return open(os.path.join(settings.BASE_DIR, 'tests', name), mode)


class Accounts(TestCase):
    def setUp(self):
        self.client = Client()

    def test_cas_login(self):
        req = HttpRequest()
        req.session = {}
        with responses.RequestsMock() as r, resource('login.xml', 'rb') as body:
            r.add(responses.POST, 'https://sistemas.ufsc.br/samlValidate',
                  body=body.read())
            self.client.login(ticket='ST-{}'.format(uuid.uuid4()),
                              service=settings.CAS_SERVER_URL,
                              request=req)
