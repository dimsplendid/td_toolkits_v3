from urllib import response
from django.urls import reverse_lazy
from django.views.generic import (
    ListView, 
    DetailView,
    CreateView,
    TemplateView,
)
from django.views.generic.edit import FormView
from django.http.response import HttpResponse
from config.settings.base import APPS_DIR

from .models import (
    Vender,
    LiquidCrystal,
    Polyimide,
    Seal
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

class MaterialsUploadView(FormView):
    template_name = 'materials/materials_upload.html'
    form_class = MaterialsUploadForm
    success_url = reverse_lazy('materials:lc_list')

    def get(self, request, *args, **kwargs):
        if request.GET.get('download'):
            filename = APPS_DIR / "materials/tests/test_files/batch_upload_test_null.xlsx"
            with open(filename, 'rb') as fp:
                response = HttpResponse(
                    fp,
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                response['content-Disposition'] = f'attachment; filename=materials_upload.xlsx'
                return response
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

class IndexView(TemplateView):
    template_name = 'materials/index.html'

class PolyimideListView(ListView):
    model = Polyimide

class SealListView(ListView):
    model = Seal