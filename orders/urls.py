from django.conf.urls import include, url
from .views import OrderCreateView, OrderDetailView, OrdersView

urlpatterns = [
    url(r'^$', OrdersView.as_view(), name='orders'),
    url(r'^(?P<pk>[\w-]{36})/$', OrderDetailView.as_view(), name='order-detail'),
    url(r'^new/$', OrderCreateView.as_view(), name='order-new'),
    url(r'^callback/', include('pagseguro.urls')),
]
