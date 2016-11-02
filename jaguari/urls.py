from django.conf.urls import include, url
from django.contrib import admin

urlpatterns = [
    # Examples:
    # url(r'^$', 'jaguari.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^login$', 'sessions.views.login', name='cas_ng_login'),
    url(r'^logout$', 'sessions.views.logout', name='cas_ng_logout'),
]
