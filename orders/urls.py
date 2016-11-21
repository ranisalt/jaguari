from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^new/$', views.new, name='order-new'),
    url(r'^$', views.OrdersView.as_view(), name='orders')
]
