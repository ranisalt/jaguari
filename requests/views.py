from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import View
from .models import Order


class OrdersView(View):
    model = Order

    def get(self, request: HttpRequest) -> HttpResponse:
        """Index of user orders"""
        pass

    def post(self, request: HttpRequest) -> HttpResponse:
        """Create new order"""
        order = self.model.objects.get(id=request.session['order'])
        pass

    def get_queryset(self):
        return self.model.objects.filter(student=self.request.user)

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(OrdersView, self).dispatch(*args, **kwargs)


class OrderDetailView(View):
    model = Order
    queryset = Order.objects.all()

    def get(self, request: HttpRequest) -> HttpResponse:
        """Show a single order"""
        pass

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(OrderDetailView, self).dispatch(*args, **kwargs)


@login_required
def new(request):
    order = Order.objects.fetch(request.user)
    request.session['order'] = order.id
    return render(request, 'requests/new.html', {
        'order': order
    })
