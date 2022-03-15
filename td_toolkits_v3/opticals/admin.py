from django.contrib import admin

from .models import (
    Instrument,
    AxometricsLog,
    RDLCellGap,
    OpticalLog,
    ResponseTimeLog
)

admin.site.register(Instrument)
admin.site.register(AxometricsLog)
admin.site.register(RDLCellGap)
admin.site.register(OpticalLog)
admin.site.register(ResponseTimeLog)