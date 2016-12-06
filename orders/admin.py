from django.conf import settings
from django.contrib import admin
from .models import Degree, Order


@admin.register(Degree)
class DegreeAdmin(admin.ModelAdmin):
    pass


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    def picture_tag(self, obj):
        import os
        from django.utils.safestring import mark_safe
        if obj.picture:
            return mark_safe('<img src="{}" />'.format(
                os.path.join('/', settings.MEDIA_URL, obj.picture.url)
            ))
        return '(no picture)'

    list_display = ['student', 'picture_tag']
