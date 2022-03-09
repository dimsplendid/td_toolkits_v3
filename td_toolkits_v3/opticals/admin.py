from django.contrib import admin

from .models import (
    Instrument,
    AxometricsLog,
    RDLCellGap
)

admin.site.register(Instrument)
admin.site.register(AxometricsLog)
admin.site.register(RDLCellGap)