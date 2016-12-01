from django.conf.urls import include, url
from .views import OrderCreateView, OrdersView

urlpatterns = [
    url(r'^$', OrdersView.as_view(), name='orders'),
    url(r'^new/$', OrderCreateView.as_view(), name='order-new'),
    url(r'^callback/', include('pagseguro.urls')),
]
