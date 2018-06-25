import copy
import datetime
import os
from urllib.parse import urlunparse

import responses
from django.conf import settings
from django.test import SimpleTestCase, TransactionTestCase, override_settings
from django.urls import reverse
from pagseguro.admin import TransactionAdmin
from pagseguro.models import Transaction

from .admin import TransactionStatusFilter
from .factories import DegreeFactory, OrderFactory, TransactionFactory, UserFactory
from .models import Order


def resource(name: str, mode: str = 'r'):
    return open(os.path.join(settings.BASE_DIR, 'fixtures', name), mode)


def ws(*args):
    return urlunparse(('https', 'ws.ufsc.br', '/'.join(args), '', '', ''))


class Degrees(SimpleTestCase):
    def test_get_common_name(self):
        degree = DegreeFactory.build(name='Test Name')
        self.assertEqual('Test Name', degree.get_common_name())

        degree = DegreeFactory.build(name='Test Name', alias='Test Alias')
        self.assertEqual('Test Alias', degree.get_common_name())


@override_settings(MEDIA_ROOT='/tmp/upload', PAGSEGURO_SANDBOX=True)
class Orders(TransactionTestCase):
    links = [{
        'ativo': True,
        'id': '15100000',
        'idPessoa': '100000000400000',
        'codigoVinculo': 1,
        'codigoCurso': 123,
        'dataNascimento': '1996-01-01T00:00:00-03:00',
        'cpf': 12345678901,
        'identidade': '1234567',
        'codigoUfIdentidade': 'SC',
        'siglaOrgaoEmissorIdentidade': 'SSP',
        'codigoSituacao': 0,
    }]

    def assertDictContainsSubset(self, subset, dictionary, msg=None):
        for attr in subset:
            self.assertEqual(subset[attr], dictionary[attr], msg)

    def setUp(self):
        self.user = UserFactory()
        self.client.force_login(self.user)

    def test_list_orders(self):
        OrderFactory.create_batch(5)
        OrderFactory.create_batch(3, student=self.user)

        response = self.client.get(reverse('orders:index'))
        self.assertTemplateUsed(response, 'orders/order_list.html')

        orders = response.context['object_list']

        # users should see all anf only their orders
        self.assertEqual(3, orders.count())
        for order in orders:
            self.assertEqual(self.user, order.student)

    def test_detail_order(self):
        order = OrderFactory(student=self.user)

        response = self.client.get(reverse('orders:detail', kwargs={
            'pk': str(order.pk),
        }))
        self.assertTemplateUsed(response, 'orders/order_detail.svg')
        self.assertEqual(order, response.context['object'])

    @responses.activate
    def test_new_order(self):
        responses.add(
            method=responses.GET,
            url=ws('CAGRService', 'cursoGraduacaoAluno', '15100000'),
            json={
                'codigo': 123,
                'nomeCompleto': 'Science Engineering',
                'campus': {'id': 1},
            })

        responses.add(
            method=responses.GET,
            url=ws('CadastroPessoaService',
                   'vinculosPessoaById',
                   self.user.username),
            json=self.links)

        response = self.client.get(reverse('orders:create'))

        # ensure response is OK status
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'orders/order_form.html')

        initial = response.context['form'].initial
        self.assertDictContainsSubset({
            'student_id': self.user.pk,
            'degree_id': 123,
            'birthday': datetime.date(1996, 1, 1),
            'cpf': '12345678901',
            'identity_number': '1234567',
            'identity_issuer': 'SSP',
            'identity_state': 'SC',
            'enrollment_number': '15100000',
        }, initial)

    @responses.activate
    def test_new_order_missing_field(self):
        broken_links = copy.deepcopy(self.links)
        del broken_links[0]['siglaOrgaoEmissorIdentidade']

        responses.add(
            method=responses.GET,
            url=ws('CadastroPessoaService',
                   'vinculosPessoaById',
                   self.user.username),
            json=broken_links)

        response = self.client.get(reverse('orders:create'))

        # ensure response is OK status
        self.assertEqual(400, response.status_code)
        self.assertTemplateUsed(response, 'errors/missing_fields.html')

    @responses.activate
    def test_new_order_no_active_link(self):
        broken_links = copy.deepcopy(self.links)
        broken_links[0]['ativo'] = False

        responses.add(
            method=responses.GET,
            url=ws('CadastroPessoaService',
                   'vinculosPessoaById',
                   self.user.username),
            json=broken_links)

        response = self.client.get(reverse('orders:create'))

        # ensure response is OK status
        self.assertEqual(400, response.status_code)
        self.assertTemplateUsed(response, 'errors/no_valid_link.html')

    @responses.activate
    def test_new_order_no_regular_link(self):
        broken_links = copy.deepcopy(self.links)
        broken_links[0]['codigoSituacao'] += 1

        responses.add(
            method=responses.GET,
            url=ws('CadastroPessoaService',
                   'vinculosPessoaById',
                   self.user.username),
            json=broken_links)

        response = self.client.get(reverse('orders:create'))

        # ensure response is OK status
        self.assertEqual(400, response.status_code)
        self.assertTemplateUsed(response, 'errors/no_valid_link.html')

    @responses.activate
    def test_new_order_no_undergraduate_link(self):
        broken_links = copy.deepcopy(self.links)
        broken_links[0]['codigoVinculo'] += 1

        responses.add(
            method=responses.GET,
            url=ws('CadastroPessoaService',
                   'vinculosPessoaById',
                   self.user.username),
            json=broken_links)

        response = self.client.get(reverse('orders:create'))

        # ensure response is OK status
        self.assertEqual(400, response.status_code)
        self.assertTemplateUsed(response, 'errors/no_valid_link.html')

    @responses.activate
    def test_post_new_order(self):
        responses.add(
            method=responses.GET,
            url=ws('CAGRService', 'cursoGraduacaoAluno', '15100000'),
            json={
                'codigo': 123,
                'nomeCompleto': 'Science Engineering',
                'campus': {'id': 1},
            })

        responses.add(
            method=responses.GET,
            url=ws('CadastroPessoaService',
                   'vinculosPessoaById',
                   self.user.username),
            json=self.links)

        with resource('checkout.xml') as payload:
            responses.add(
                method=responses.POST,
                url='https://ws.sandbox.pagseguro.uol.com.br/v2/checkout',
                body=payload.read(),
                content_type='application/xml')

            with resource('image.jpg', 'rb') as picture:
                response = self.client.post(reverse('orders:create'), {
                    'picture': picture
                })

        # ensure response is redirect to payment gateway
        self.assertRedirects(response,
                             'https://sandbox.pagseguro.uol.com.br/v2/checkout/payment.html?code=00000000000000000000000000000000',
                             fetch_redirect_response=False)

    def test_order_transaction_status_filter_none(self):
        for order in OrderFactory.create_batch(5):
            TransactionFactory(reference=str(order.pk))

        order = OrderFactory()

        filter = TransactionStatusFilter(request=None,
                                         params={'status': 'none'},
                                         model=Transaction,
                                         model_admin=TransactionAdmin)
        result = filter.queryset(None, Order.objects.all())
        self.assertEqual(1, result.count())
        self.assertEqual(order, result.get())

    def test_order_transaction_status_filter_pending(self):
        OrderFactory.create_batch(5)

        filter = TransactionStatusFilter(request=None,
                                         params={'status': 'pending'},
                                         model=Transaction,
                                         model_admin=TransactionAdmin)

        order = OrderFactory()
        transaction = TransactionFactory(reference=str(order.pk),
                                         status='aguardando')

        result = filter.queryset(None, Order.objects.all())
        self.assertEqual(1, result.count())
        self.assertEqual(order, result.first())
        self.assertEqual(transaction,
                         Transaction.objects.get(reference=str(order.pk)))

        order = OrderFactory()
        transaction = TransactionFactory(reference=str(order.pk),
                                         status='em_analise')

        result = filter.queryset(None, Order.objects.all())
        self.assertEqual(2, result.count())
        self.assertEqual(order, result.first())
        self.assertEqual(transaction,
                         Transaction.objects.get(reference=str(order.pk)))

    def test_order_transaction_status_filter_available(self):
        OrderFactory.create_batch(5)

        filter = TransactionStatusFilter(request=None,
                                         params={'status': 'available'},
                                         model=Transaction,
                                         model_admin=TransactionAdmin)

        order = OrderFactory()
        transaction = TransactionFactory(reference=str(order.pk),
                                         status='pago')

        result = filter.queryset(None, Order.objects.all())
        self.assertEqual(1, result.count())
        self.assertEqual(order, result.first())
        self.assertEqual(transaction,
                         Transaction.objects.get(reference=str(order.pk)))

        order = OrderFactory()
        transaction = TransactionFactory(reference=str(order.pk),
                                         status='disponivel')

        result = filter.queryset(None, Order.objects.all())
        self.assertEqual(2, result.count())
        self.assertEqual(order, result.first())
        self.assertEqual(transaction,
                         Transaction.objects.get(reference=str(order.pk)))

    def test_order_transaction_status_filter_unavailable(self):
        OrderFactory.create_batch(5)

        filter = TransactionStatusFilter(request=None,
                                         params={'status': 'unavailable'},
                                         model=Transaction,
                                         model_admin=TransactionAdmin)

        order = OrderFactory()
        transaction = TransactionFactory(reference=str(order.pk),
                                         status='em_disputa')

        result = filter.queryset(None, Order.objects.all())
        self.assertEqual(1, result.count())
        self.assertEqual(order, result.first())
        self.assertEqual(transaction,
                         Transaction.objects.get(reference=str(order.pk)))

        order = OrderFactory()
        transaction = TransactionFactory(reference=str(order.pk),
                                         status='devolvido')

        result = filter.queryset(None, Order.objects.all())
        self.assertEqual(2, result.count())
        self.assertEqual(order, result.first())
        self.assertEqual(transaction,
                         Transaction.objects.get(reference=str(order.pk)))

        order = OrderFactory()
        transaction = TransactionFactory(reference=str(order.pk),
                                         status='cancelado')

        result = filter.queryset(None, Order.objects.all())
        self.assertEqual(3, result.count())
        self.assertEqual(order, result.first())
        self.assertEqual(transaction,
                         Transaction.objects.get(reference=str(order.pk)))

    def test_order_valid_qrcode_generate(self):
        OrderFactory(use_code='abcdefgh')

        response = self.client.get(reverse('orders:qr', kwargs={
            'slug': 'abcdefgh',
        }))

        self.assertEqual(200, response.status_code)
        self.assertEqual('image/svg+xml', response['Content-Type'])

    def test_order_invalid_qrcode_fail(self):
        Order.objects.filter(use_code='abcdefgh').delete()

        response = self.client.get(reverse('orders:qr', kwargs={
            'slug': 'abcdefgh',
        }))

        self.assertEqual(404, response.status_code)

    def test_order_full_name_search(self):
        from orders.models import Order

        OrderFactory.create_batch(5)
        user = UserFactory(
            name='Carolina Josefa Leopoldina de Habsburgo-Lorena')
        order = OrderFactory(student=user)

        result = Order.objects.filter(full_name__contains='josefa')
        self.assertEqual(1, result.count())
        self.assertEqual(order, result.get())

    def test_order_remove_picture_on_delete(self):
        from shutil import copy

        order = OrderFactory()

        dest = os.path.join(settings.MEDIA_ROOT, str(order.pk) + '.jpg')
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
        copy(os.path.join(settings.BASE_DIR, 'fixtures', 'image.jpg'), dest)

        order.picture = str(order.pk) + '.jpg'
        order.delete()

        self.assertFalse(os.path.isfile(dest))
