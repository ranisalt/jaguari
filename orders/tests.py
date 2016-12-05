import json
import os
import responses
import uuid
from django.conf import settings
from django.http import HttpRequest
from django.test import Client, TestCase
from .models import Order


def resource(name: str, mode: str = 'r'):
    return open(os.path.join(settings.BASE_DIR, 'tests', name), mode)


def mock_cagr() -> responses.RequestsMock:
    r = responses.RequestsMock()

    with resource('cursoGraduacaoAluno.json') as payload:
        r.add(responses.GET,
              'https://ws.ufsc.br/CAGRService/cursoGraduacaoAluno/13100000',
              json=json.load(payload))

    with resource('vinculosPessoaById.json') as payload:
        r.add(responses.GET,
              'https://ws.ufsc.br/CadastroPessoaService/vinculosPessoaById'
              '/100000000400000',
              json=json.load(payload))

    return r


class Orders(TestCase):
    def setUp(self):
        self.client = Client()

        req = HttpRequest()
        req.session = {}
        with responses.RequestsMock() as r, resource('login.xml', 'rb') as body:
            r.add(responses.POST, 'https://sistemas.ufsc.br/samlValidate',
                  body=body.read())
            self.client.login(ticket='ST-{}'.format(uuid.uuid4()),
                              service=settings.CAS_SERVER_URL,
                              request=req)

    def test_new_order(self):
        self.assertEqual(Order.objects.count(), 0)

        with mock_cagr():
            self.client.get('/orders/new/', follow=True)

        self.assertEqual(Order.objects.count(), 1)

        order = Order.objects.get()
        self.assertEqual('13100000', order.enrollment_number)
        self.assertEqual('John Edward Gammell', order.student.get_full_name())

        order = Order.objects.get()
        self.assertEqual(order.student.get_username(), '100000000400000')

    def test_post_order(self):
        self.assertEqual(Order.objects.count(), 0)

        with mock_cagr():
            self.client.get('/orders/new/', follow=True)

        self.assertEqual(Order.objects.count(), 1)

        with resource('image.jpg', 'rb') as picture:
            res = self.client.post('/orders/new/', {
                'picture': picture
            })
        self.assertEqual(res.status_code, 302)
