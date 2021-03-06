from django.conf.urls import include, url

from .views import OrderCreateView, OrderDetailView, OrderQrView, OrdersView

app_name = 'orders'
urlpatterns = [
    url(r'^$', OrdersView.as_view(), name='index'),
    url(r'^(?P<pk>[\w-]{36}).svg$', OrderDetailView.as_view(), name='detail'),
    url(r'^qr/(?P<slug>[\w-]{8}).svg$', OrderQrView.as_view(), name='qr'),
    url(r'^new/$', OrderCreateView.as_view(), name='create'),
    url(r'^callback/', include('pagseguro.urls')),
]
