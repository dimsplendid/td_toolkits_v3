from django.contrib import admin

from .models import (
    ProductModelType,
    Sub,
    Chip,
)

admin.site.register(ProductModelType)
admin.site.register(Sub)
admin.site.register(Chip)
