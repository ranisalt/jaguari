from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views.generic import View
from pagseguro.api import PagSeguroApi, PagSeguroItem
from .models import Order


class OrdersView(View):
    model = Order

    def get(self, request):
        """Index of user orders"""
        pass

    def get_queryset(self):
        return self.model.objects.filter(student=self.request.user)

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(OrdersView, self).dispatch(*args, **kwargs)


class OrderDetailView(View):
    model = Order

    def get(self, request):
        """Show a single order"""
        pass

    def get_queryset(self):
        return self.model.objects.filter(pk=self.request.session['order'])

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(OrderDetailView, self).dispatch(*args, **kwargs)


class OrderCreateView(View):
    model = Order

    def get(self, request):
        order = self.model.objects.fetch(request.user)
        request.session['order'] = str(order.pk)
        return render(request, 'requests/new.html', {
            'order': order
        })

    def post(self, request):
        """Create new order"""
        order = get_object_or_404(Order, pk=request.session['order'])
        order.picture = request.FILES['picture']
        order.save()

        item = PagSeguroItem(id=str(order.pk),
                             description='Carteira de Identificação Estudantil',
                             amount='15.00',
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

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(OrderCreateView, self).dispatch(*args, **kwargs)
