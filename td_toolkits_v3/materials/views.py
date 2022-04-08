from io import BytesIO
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
import pandas as pd
from config.settings.base import APPS_DIR
from config.settings.base import UPLOAD_TEMPLATE_DIR

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

class LiquidCrystalUpdateView(UpdateView):
    model = LiquidCrystal
    fields = ['designed_cell_gap']
    template_name = 'form_generic.html'

    def get(self, request, *args, **kwargs):
        request.session['next'] = request.GET.get('next')

        return super().get(request, *args, **kwargs)

    def get_success_url(self) -> str:
        if self.request.session['next']:
            return self.request.session['next']
        return super().get_success_url()

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
            for item in df_map:
                df_map[item].to_excel(writer, sheet_name=item, index=False)

            # add additional regested data for reference
            # TODO: testing now
            pd.DataFrame({
                'item': ['LC'],
                'value': ['LCT-15-1098']
            }).to_excel(writer, sheet_name='regested', index=False)
        
        response = HttpResponse(
            buffer.getvalue(),
            content_type=(
                'application/'
                'vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        )
        response['Content-Disposition'] = f'attachment; filename={file_name}'
        return response
