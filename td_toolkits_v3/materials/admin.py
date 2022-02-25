from django.contrib import admin
from .models import (
    Vender,
    LiquidCrystal,
    Polyimide,
    Seal
)


admin.site.register(Vender)
admin.site.register(LiquidCrystal)
admin.site.register(Polyimide)
admin.site.register(Seal)
