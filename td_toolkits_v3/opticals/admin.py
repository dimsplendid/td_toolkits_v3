from django.contrib import admin

from .models import (
    Instrument,
    AxometricsLog,
    RDLCellGap,
    OpticalLog,
)

admin.site.register(Instrument)
admin.site.register(AxometricsLog)
admin.site.register(RDLCellGap)
admin.site.register(OpticalLog)