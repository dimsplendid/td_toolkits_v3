from django.urls import reverse_lazy
from django.views.generic import (
    ListView, 
    DetailView,
    CreateView,
    TemplateView,
)
from django.views.generic.edit import FormView


from .models import (
    Vender,
    LiquidCrystal
)
from .forms import MaterialsUploadForm

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

class MaterialsBatchCreateView(FormView):
    template_name = 'materials/materials_upload.html'
    form_class = MaterialsUploadForm
    success_url = reverse_lazy('materials:lc_list')

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)