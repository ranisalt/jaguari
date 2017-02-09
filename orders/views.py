import iso8601
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, DetailView, ListView
from pagseguro.api import PagSeguroApi, PagSeguroItem
from .forms import OrderForm
from .models import Order


class OrdersView(LoginRequiredMixin, ListView):
    model = Order

    def get_queryset(self):
        qs = super(OrdersView, self).get_queryset()
        return qs.filter(student=self.request.user)


class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order


class OrderCreateView(LoginRequiredMixin, CreateView):
    form_class = OrderForm
    model = Order

    def get_initial(self):
        userdata = self.request.session.get('userdata')
        if userdata is None:
            userdata = self.model.objects.fetch(self.request.user)
            self.request.session['userdata'] = userdata.copy()

        userdata['birthday'] = iso8601.parse_date(userdata['birthday']).date()
        return userdata

    def get_success_url(self):
        order = self.object

        item = PagSeguroItem(id=str(order.pk),
                             description='Carteira de Identificação Estudantil',
                             amount='20.00',
                             quantity=1)

        api = PagSeguroApi(reference=str(order.pk),
                           senderEmail=order.student.email,
                           senderName=order.student.get_full_name(),
                           shippingAddressPostalCode='88040000',
                           shippingAddressNumber='s/n',
                           shippingAddressComplement='',
                           shippingCost='0.00',
                           shippingType=3)

        api.add_item(item)
        checkout = api.checkout()
        return checkout['redirect_url']
