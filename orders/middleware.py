from django.shortcuts import render
from django.utils.deprecation import MiddlewareMixin
from .models import MissingFieldsError


class OrderMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        if isinstance(exception, MissingFieldsError):
            return render(request, 'errors/missing_fields.html', context={
                'fields': exception.fields
            }, status=400)
