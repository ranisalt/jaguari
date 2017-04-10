from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.views.generic import DetailView, ListView
from formtools.wizard.views import SessionWizardView
from .forms import OrderPictureForm
from .models import Order


class OrdersView(LoginRequiredMixin, ListView):
    model = Order

    def get_queryset(self):
        qs = super(OrdersView, self).get_queryset()
        return qs.filter(student=self.request.user)


class OrderDetailView(LoginRequiredMixin, DetailView):
    content_type = 'image/svg+xml'
    model = Order
    template_name = 'orders/order_detail.svg'


class OrderQrView(LoginRequiredMixin, DetailView):
    model = Order
    slug_field = 'use_code'

    def render_to_response(self, context, **response_kwargs):
        import io
        import qrcode
        from qrcode.image.svg import SvgPathImage

        url = 'https://cie.dce.ufsc.br/atributos/ws/dceufsc/{}'
        image = qrcode.make(url.format(self.object.use_code),
                            error_correction=qrcode.constants.ERROR_CORRECT_L,
                            image_factory=SvgPathImage)

        stream = io.BytesIO()
        image.save(stream)
        return HttpResponse(content=stream.getvalue(),
                            content_type='image/svg+xml')


class OrderCreateView(SessionWizardView):
    form_list = [('review', forms.Form),
                 ('picture', OrderPictureForm)]
    template_name = 'orders/partials/{step}_form.html'

    def get_template_names(self):
        return [self.template_name.format(step=self.steps.current)]

    def get_form_initial(self, step):
        if step == 'review':
            userdata = Order.objects.fetch(self.request.user)

            userdata['cpf'] = Order.format_cpf(userdata['cpf'])
            userdata['degree'] = Order.format_degree(userdata['degree'])
            userdata['rg'] = Order.format_rg(userdata['identity_number'],
                                             userdata['identity_issuer'],
                                             userdata['identity_state'])
            return userdata

        return super().get_form_initial(step)

    def done(self, form_list, **kwargs) -> HttpResponse:
        from django.shortcuts import redirect
        from pagseguro.api import PagSeguroApi, PagSeguroItem

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

        return redirect(checkout['redirect_url'])
