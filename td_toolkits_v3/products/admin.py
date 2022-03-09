from django.contrib import admin

from .models import (
    ProductModelType,
    Project,
    Factory,
    Experiment,
    Condition,
    Sub,
    Chip,
)

admin.site.register(ProductModelType)
admin.site.register(Project)
admin.site.register(Factory)
admin.site.register(Experiment)
admin.site.register(Condition)
admin.site.register(Sub)
admin.site.register(Chip)
