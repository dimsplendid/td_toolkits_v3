from django.views.generic import (
    ListView, 
    DetailView,
    CreateView,
    TemplateView,
)


from .models import (
    Vender,
    LiquidCrystal
)

class VenderListView(ListView):
    model = Vender


class LiquidCrystalListView(ListView):
    model = LiquidCrystal

class LiquidCrystalDetailView(DetailView):
    model = LiquidCrystal

class LiquidCrystalCreateView(CreateView):
    model = LiquidCrystal
    fields = [
        'name',
        'vender',
        'designed_cell_gap',
        't_ni',
        't_cn',
        'flow_viscosity',
        'rotational_viscosity',
        'n_e',
        'n_o',
        'e_para',
        'e_perp',
        'k_11',
        'k_22',
        'k_33',
        'density'
    ]
