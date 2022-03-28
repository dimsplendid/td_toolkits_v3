from django.contrib import admin

from .models import (
    Instrument,
    AxometricsLog,
    RDLCellGap,
    OpticalLog,
    ResponseTimeLog,
    OpticalReference,
    OpticalsFittingModel,
    OpticalSearchProfile,
)

admin.site.register(Instrument)
admin.site.register(AxometricsLog)
admin.site.register(RDLCellGap)
admin.site.register(OpticalLog)
admin.site.register(ResponseTimeLog)
admin.site.register(OpticalReference)
admin.site.register(OpticalsFittingModel)
admin.site.register(OpticalSearchProfile)