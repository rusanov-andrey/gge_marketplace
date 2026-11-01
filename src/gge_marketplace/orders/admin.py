from django.contrib import admin

from .infrastructure.models import Order, OrderItem

admin.site.register(Order)
admin.site.register(OrderItem)
