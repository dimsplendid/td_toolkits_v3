from django.contrib import admin

from .models import (
    Adhesion,
    DeltaAngle,
    File,
    LowTemperatureOperation,
    LowTemperatureStorage,
    PressureCookingTest,
    SealWVTR,
    UShapeAC,
    VoltageHoldingRatio,
)

admin.site.register(Adhesion)
admin.site.register(DeltaAngle)
admin.site.register(File)
admin.site.register(LowTemperatureOperation)
admin.site.register(LowTemperatureStorage)
admin.site.register(PressureCookingTest)
admin.site.register(SealWVTR)
admin.site.register(UShapeAC)
admin.site.register(VoltageHoldingRatio)

