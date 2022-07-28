from __future__ import annotations
from typing import List, Tuple, Dict, Union, Optional

from io import BytesIO
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpRequest
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import (
    ListView, 
    DetailView,
    CreateView,
    TemplateView,
)
from django.views.generic.edit import FormView, UpdateView
from django.http.response import HttpResponse
from django.core.cache import cache

import pandas as pd
from config.settings.base import APPS_DIR
from config.settings.base import UPLOAD_TEMPLATE_DIR

from .models import (
    Vender,
    LiquidCrystal,
    Polyimide,
    Seal
)
from .forms import (
    MaterialsUploadForm,
    MaterialsUpdateForm,
    RefractionIndexUploadForm,
)
from td_toolkits_v3.materials.tools import utils

class VenderListView(ListView):
    model = Vender


class LiquidCrystalListView(ListView):
    model = LiquidCrystal

class LiquidCrystalDetailView(DetailView):
    model = LiquidCrystal

class LiquidCrystalCreateView(LoginRequiredMixin, CreateView):
    model = LiquidCrystal
    fields = [
        'name',
        'vender',
        'material_type',
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

class LiquidCrystalUpdateView(LoginRequiredMixin, UpdateView):
    model = LiquidCrystal
    fields = ['material_type', 'designed_cell_gap']
    template_name = 'form_generic.html'

    def get(self, request, *args, **kwargs):
        request.session['next'] = request.GET.get('next')

        return super().get(request, *args, **kwargs)

    def get_success_url(self) -> str:
        if self.request.session['next']:
            return self.request.session['next']
        return super().get_success_url()

class MaterialsUploadView(LoginRequiredMixin, FormView):
    # template_name = 'materials/materials_upload.html'
    template_name = 'form_generic.html'
    form_class = MaterialsUploadForm
    success_url = reverse_lazy('materials:lc_list')

    def get_context_data(self, **kwargs) -> dict[str, ]:
        context = super().get_context_data(**kwargs)
        context['title'] = 'Materials Upload'
        context['file_path'] = reverse_lazy('materials:template') \
                             + '?download=material_upload_template'

        return context

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

class MaterialsUpdateView(LoginRequiredMixin, FormView):
    template_name = 'form_generic.html'
    form_class = MaterialsUpdateForm
    success_url = reverse_lazy('materials:lc_list')

    def get_context_data(self, **kwargs) -> dict[str, ]:
        context = super().get_context_data(**kwargs)
        context['title'] = 'Materials Update'
        context['file_path'] = reverse_lazy('materials:template') \
                             + '?download=material_upload_template'
        return context

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

class IndexView(TemplateView):
    template_name = 'materials/index.html'

class PolyimideListView(ListView):
    template_name = 'list_generic.html'
    model = Polyimide
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object_name'] = 'PI'
        # context['add_url'] = reverse_lazy('materials:pi_add')
        return context

class PolyimideDetailView(DetailView):
    model = Polyimide

class PolyimideCreateView(LoginRequiredMixin, CreateView):
    template_name = 'form_generic.html'
    model = Polyimide
    fields = [
        'name',
        'material_type',
        'vender',
    ]

class PolyimideUpdateView(LoginRequiredMixin, UpdateView):
    template_name = 'form_generic.html'
    model = Polyimide
    fields = [
        'name',
        'material_type',
        'vender',
    ]

class SealListView(ListView):
    template_name = 'list_generic.html'
    model = Seal
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object_name'] = 'Seal'
        # context['add_url'] = reverse_lazy('materials:seal_add')
        return context

class SealDetailView(DetailView):
    model = Seal

class SealCreateView(LoginRequiredMixin, CreateView):
    template_name = 'form_generic.html'
    model = Seal
    fields = [
        'name',
        'material_type',
        'vender',
    ]

class SealUpdateView(LoginRequiredMixin, UpdateView):
    template_name = 'form_generic.html'
    model = Seal
    fields = [
        'name',
        'material_type',
        'vender',
    ]

class TemplateDownloadView(View):
    def get(self, request:HttpRequest, *args, **kwargs) -> HttpResponse:
        # make sure there is download keywords
        if not (file_name := request.GET.get('download')):
            raise Http404

        file_name += '.xlsx'
        file_path = UPLOAD_TEMPLATE_DIR / file_name

        # read all file from static template file
        try:
            df_map = pd.read_excel(file_path, sheet_name=None)
        except:
            print(f'File not found: {file_path}')
            print('Or somethin wrong in pandas read_excel')
            raise Http404

        buffer = BytesIO()
        with pd.ExcelWriter(buffer) as writer:
            # add additional registered data for reference
            df = utils.get_registered_name()
            df.to_excel(writer, sheet_name='registerted', index=False)
            
            for item in df_map:
                df_map[item].to_excel(writer, sheet_name=item, index=False)

            
        
        response = HttpResponse(
            buffer.getvalue(),
            content_type=(
                'application/'
                'vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        )
        response['Content-Disposition'] = f'attachment; filename={file_name}'
        return response

class RefractionIndexUploadView(FormView):
    template_name: str = 'form_generic.html'
    form_class = RefractionIndexUploadForm
    # success_url: str = reverse_lazy(
    #     'materials:refraction_index_upload_success'
    # )
    success_url: Optional[str] = reverse_lazy(
        'materials:refraction_index_upload_success'
    )
    
    def form_valid(self, form):
        form.save()
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Refraction Index Upload'
        context['file_path'] = reverse_lazy(
            'materials:template'
        ) + '?download=lc_datasheet_refraction_template'
        
        return context
    
class RefractionIndexUploadSuccessView(TemplateView):
    template_name = 'materials/refraction_index_upload_success.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Refraction Index Upload Success'
        lcs = cache.get('lcs')
        table = {
            'LC': [],
            'ne_450': [],
            'no_450': [],
            'ne_509': [],
            'no_509': [],
            'ne_546': [],
            'no_546': [],
            'ne_589': [],
            'no_589': [],
            'ne_633': [],
            'no_633': [],
        }
        for lc in lcs:
            table['LC'].append(lc)
            table['ne_450'].append(lc.ne_exps.get(wavelength=450).value)
            table['no_450'].append(lc.no_exps.get(wavelength=450).value)
            table['ne_509'].append(lc.ne_exps.get(wavelength=509).value)
            table['no_509'].append(lc.no_exps.get(wavelength=509).value)
            table['ne_546'].append(lc.ne_exps.get(wavelength=546).value)
            table['no_546'].append(lc.no_exps.get(wavelength=546).value)
            table['ne_589'].append(lc.ne_exps.get(wavelength=589).value)
            table['no_589'].append(lc.no_exps.get(wavelength=589).value)
            table['ne_633'].append(lc.ne_exps.get(wavelength=633).value)
            table['no_633'].append(lc.no_exps.get(wavelength=633).value)
            
        table_df = pd.DataFrame(table)
        table_html = table_df.to_html(
            float_format=lambda x: f'{x:.4f}',
            classes='table table-striped table-bordered table-hover',
            justify='center',
            index=False,
            escape=False,
        )
        context['table'] = table_html
        return context
        