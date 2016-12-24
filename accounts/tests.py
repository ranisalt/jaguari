import os
import responses
import uuid
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
            self.client.login(ticket='ST-{}'.format(uuid.uuid4()),
                              service=settings.CAS_SERVER_URL,
                              request=req)

        # ensure user is created with correct data
        self.assertEqual(1, User.objects.count())

        user = User.objects.get()
        self.assertEqual('100000000400000', user.get_username())
        self.assertEqual('John', user.first_name)
        self.assertEqual('Edward Gammell', user.last_name)
        self.assertEqual('john@gmail.com', user.email)
