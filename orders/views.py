import requests
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views.generic import View
from lxml import etree
from .models import Order

MOIP_XML = """
<EnviarInstrucao>
    <InstrucaoUnica>
        <Razao>Carteira de Identificação Estudantil</Razao>
        <Valores>
            <Valor moeda='BRL'>15.00</Valor>
        </Valores>
        <IdProprio>{order_id}</IdProprio>
    </InstrucaoUnica>
</EnviarInstrucao>
"""


class OrdersView(View):
    model = Order

    def get(self, request: HttpRequest) -> HttpResponse:
        """Index of user orders"""
        pass

    def get_queryset(self):
        return self.model.objects.filter(student=self.request.user)

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(OrdersView, self).dispatch(*args, **kwargs)


class OrderDetailView(View):
    model = Order

    def get(self, request: HttpRequest) -> HttpResponse:
        """Show a single order"""
        pass

    def get_queryset(self):
        return self.model.objects.filter(pk=self.request.session['order'])

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(OrderDetailView, self).dispatch(*args, **kwargs)


class OrderCreateView(View):
    model = Order

    def get(self, request: HttpRequest) -> HttpResponse:
        order = self.model.objects.fetch(request.user)
        request.session['order'] = order.id
        return render(request, 'requests/new.html', {
            'order': order
        })

    def post(self, request: HttpRequest) -> HttpResponse:
        """Create new order"""
        order = get_object_or_404(self.model, pk=request.session['order'])

        payload = MOIP_XML.format(order_id=order.pk)

        res = requests.post(settings.MOIP_ORDER_URL,
                            auth=settings.MOIP_CREDENTIALS,
                            data=payload,
                            headers={'content-type': 'application/xml'})
        root = etree.fromstring(res.text)
        token = root.xpath('//Token/text()')[0]
        return redirect(settings.MOIP_CHECKOUT_URL.format(token))
