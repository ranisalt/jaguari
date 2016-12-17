import json
import os
import responses
from django.conf import settings
from django.contrib.auth.models import User
from django.test import Client, TransactionTestCase, override_settings
from .models import Degree, Order


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


@override_settings(MEDIA_ROOT='/tmp/upload', PAGSEGURO_SANDBOX=True)
class Orders(TransactionTestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='100000000400000',
                                             first_name='John',
                                             last_name='Edward Gammell')

    def test_new_order(self):
        self.client.force_login(self.user)

        with mock_cagr():
            response = self.client.get('/orders/new/')

        # ensure response is OK status
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'orders/new.html')

        # ensure degree is created with correct data
        self.assertEqual(1, Degree.objects.count())

        degree = Degree.objects.get()
        self.assertEqual(Degree.UNDERGRADUATE, degree.tier)
        self.assertEqual('Ciências da Computação', degree.name)
        self.assertEqual(Degree.FLO, degree.campus)

        # ensure order is created with correct data
        self.assertEqual(1, Order.objects.count())

        order = Order.objects.get()
        self.assertEqual('13100000', order.enrollment_number)
        self.assertEqual('John Edward Gammell', order.student.get_full_name())
        self.assertEqual('100000000400000', order.student.get_username())

    def test_new_order_without_login(self):
        response = self.client.get('/orders/new/')

        # ensure response is redirect to login page
        self.assertEqual(302, response.status_code)
        self.assertRegex(response.url, r'^/accounts/login/')

        # ensure order is not created
        self.assertEqual(0, Order.objects.count())

    def test_post_new_order(self):
        self.client.force_login(self.user)

        # force new order
        with mock_cagr():
            self.client.get('/orders/new/')

        with resource('image.jpg', 'rb') as picture:
            response = self.client.post('/orders/new/', {
                'picture': picture
            })

        # ensure response is redirect to payment gateway
        self.assertEqual(302, response.status_code)
        self.assertRegex(response.url,
                         r'^https://sandbox\.pagseguro\.uol\.com\.br/v2'
                         r'/checkout/payment\.html\?code=\w+$')
