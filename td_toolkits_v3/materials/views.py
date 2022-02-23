from django.views.generic import ListView, DetailView


from .models import (
    Vender,
    LiquidCrystal
)

class VenderListView(ListView):
    model = Vender


class LiquidCrystalListView(ListView):
    model = LiquidCrystal
