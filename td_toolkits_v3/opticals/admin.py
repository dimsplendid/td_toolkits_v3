from django.contrib import admin

from .models import (
    AxometricsLog,
    RDLCellGap
)

admin.site.register(AxometricsLog)
admin.site.register(RDLCellGap)