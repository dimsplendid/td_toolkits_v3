from io import BytesIO
import pandas as pd

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpRequest
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import (
    TemplateView,
    ListView,
    DetailView,
)
from django.views.generic.edit import (
    CreateView,
    FormView,
    UpdateView,
)

from td_toolkits_v3.materials.models import (
    LiquidCrystal,
    Polyimide,
    Seal,
)
from td_toolkits_v3.products.models import Experiment

from .forms import (
    ReliabilitiesUploadForm
)
from .models import ReliabilitySearchProfile
from .tools.utils import ReliabilityScore, UShape

class IndexView(TemplateView):
    template_name = 'reliabilities/index.html'

class ReliabilitySearchProfileListView(ListView):
    model = ReliabilitySearchProfile

class ReliabilitySearchProfileDetailView(DetailView):
    model = ReliabilitySearchProfile

class ReliabilitySearchProfileCreateView(LoginRequiredMixin, CreateView):
    template_name = 'form_generic.html'
    model = ReliabilitySearchProfile
    fields = [
        'name',
        'material_type',
        'voltage_holding_ratio',
        'voltage_holding_ratio_venders',
        'voltage_holding_ratio_weight',
        'delta_angle',
        'delta_angle_venders',
        'delta_angle_weight',
        'adhesion',
        'adhesion_venders',
        'adhesion_weight',
        'low_temperature_storage',
        'low_temperature_storage_venders',
        'low_temperature_storage_weight',
        'pressure_cooking_test',
        'pressure_cooking_test_venders',
        'pressure_cooking_test_weight',
        'seal_wvtr',
        'seal_wvtr_venders',
        'seal_wvtr_weight',
        'u_shape_ac',
        'u_shape_ac_venders',
        'u_shape_ac_weight',
    ]

class ReliabilitySearchProfileUpdateView(LoginRequiredMixin, UpdateView):
    template_name = 'form_generic.html'
    model = ReliabilitySearchProfile
    fields = [
        'name',
        'material_type',
        'voltage_holding_ratio',
        'voltage_holding_ratio_venders',
        'voltage_holding_ratio_weight',
        'delta_angle',
        'delta_angle_venders',
        'delta_angle_weight',
        'adhesion',
        'adhesion_venders',
        'adhesion_weight',
        'low_temperature_storage',
        'low_temperature_storage_venders',
        'low_temperature_storage_weight',
        'pressure_cooking_test',
        'pressure_cooking_test_venders',
        'pressure_cooking_test_weight',
        'seal_wvtr',
        'seal_wvtr_venders',
        'seal_wvtr_weight',
        'u_shape_ac',
        'u_shape_ac_venders',
        'u_shape_ac_weight',
    ]
    def get(self, request, *args, **kwargs):
        request.session['next'] = request.GET.get('next')

        return super().get(request, *args, **kwargs)

    def get_success_url(self) -> str:
        if self.request.session['next']:
            return self.request.session['next']
        return super().get_success_url()

class ReliabilitySearchProfileCopyView(ReliabilitySearchProfileUpdateView):
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        self.origin = super().get_object(queryset)
        obj.pk = None
        obj.name = obj.name + '-copy'
        obj.slug = None
        # TODO:
        # The many-to-many fields need add after pk is generate
        # Still don't know how to copy the values in this kind of 
        # situation
        
        return obj

class ReliabilitiesUploadView(LoginRequiredMixin, FormView):
    template_name = 'form_generic.html'
    form_class = ReliabilitiesUploadForm
    success_url = reverse_lazy('reliabilities:index')

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'RA Upload'
        context['file_path'] = reverse_lazy('materials:template') \
                             + '?download=reliability_upload_template'

        return context

class ReliabilitySearchView(TemplateView):
    template_name = 'reliabilities/search.html'

    def get_context_data(self, **kwargs) :
        context = super().get_context_data(**kwargs)
        profile = self.request.GET.get('profile')
        if profile is None:
            profile = 'default'

        context['profile_list'] = ReliabilitySearchProfile.objects.all()
        self.profile = get_object_or_404(
            ReliabilitySearchProfile,
            slug=profile
        )
        context['profile'] = self.profile

        if self.request.GET.get('pure'):
            self.request.session['opt_lc_list'] = None
        
        # opt result part
        if opt_lc_list:= self.request.session.get('opt_lc_list'):
            context['lc_list'] = LiquidCrystal.objects.filter(
                name__in=opt_lc_list
            )
            context['q_opt'] = True
        else:
            context['lc_list'] = LiquidCrystal.objects.filter(
                material_type=context['profile'].material_type
            )

        
        # ra part
        context['pi_list'] = Polyimide.objects.filter(
            material_type=context['profile'].material_type
        )
        context['seal_list'] = Seal.objects.filter(
            material_type=context['profile'].material_type
        )

        
        query = self.configuration_query()
        if query is not None:
            context['q'] = True
            ra_score = ReliabilityScore(query, context['profile'])
            context['ra_plot'] = ra_score.plot

            # TODO: maybe this style should move to other place, and I can
            #       use the for all my pandas render
            table_style = {
                'float_format': lambda x: f'{x:.2f}',
                'classes': [
                    'table', 
                    'table-hover', 
                    'text-center', 
                    'table-striped'
                ],
                'justify': 'center',
                'index': False,
                'escape': False,
            }

            # Only render first 10 result
            context['ra_score'] = ra_score.result['normalized'][:10].to_html(
                **table_style
            )
            context['ra_score_raw'] = ra_score.result['raw'][:10].to_html(
                **table_style
            )
            # save data to cookies for downloading later
            self.request.session['ra_all'] = ra_score.result['all'].to_json()
            self.request.session['ra_score'] = ra_score.result['normalized'].\
                to_json()
            self.request.session['ra_score_raw'] = ra_score.result['raw'].\
                to_json()
            # The calculate raws
            for attr in dir(ra_score):
                if attr.startswith('table'):
                    if (table := getattr(ra_score, attr)['raw']) is None:
                        # TODO: There should be more eligant methods...
                        if attr[6:] == 'u_shape_ac':
                            self.request.session[attr] = pd.DataFrame({
                                'msg': ['no value'],
                                'Time(h)': [1],
                                'Temperature(°C)': [25]
                            }).to_json()
                        elif attr[6:] == 'voltage_holding_ratio':
                            self.request.session[attr] = pd.DataFrame({
                                'msg': ['no value'],
                                'Measure Voltage': [1],
                                'Measure Frequency': [0.6]
                            }).to_json()
                        elif attr[6:] == 'low_temperature_storage':
                            self.request.session[attr] = pd.DataFrame({
                                'msg': ['no value'],
                                'Storage Cond.': 'Bulk',
                                'Measure Temp.(°C)': [-30]
                            }).to_json()
                        else:
                            self.request.session[attr] = None
                    else:
                        self.request.session[attr] = table.to_json()

        return context

    def configuration_query(self):
        """
        Deal with the ra qeury, transfer 'ALL' and None to Model.objects.all(),
        otherwise just search using name__in()
        """
        lc_list = self.request.GET.getlist('lc_list')
        pi_list = self.request.GET.getlist('pi_list')
        seal_list = self.request.GET.getlist('seal_list')
        if (not lc_list) and (not pi_list) and (not seal_list):
            return None

        def qeury(model, qlist):
            # print(qlist)
            if (not qlist) or ('ALL' in qlist):
                return model.objects.filter(
                    material_type=self.profile.material_type
                )
            else:
                return model.objects.filter(name__in=qlist)

        q_lc = qeury(LiquidCrystal, lc_list)
        q_pi = qeury(Polyimide, pi_list)
        q_seal = qeury(Seal, seal_list)

        return (q_lc, q_pi, q_seal)
    

class ReliabilitySearchResultDownload(View):
    def get(self, request: HttpRequest, *args, **kwargs):
        if 'ra_all' in request.session:
            ra_result = pd.read_json(request.session['ra_all'])
            ra_score_raw = pd.read_json(request.session['ra_score_raw'])
            ra_score = pd.read_json(request.session['ra_score'])

            buffer = BytesIO()
            with pd.ExcelWriter(buffer) as writer:
                ra_result.to_excel(writer, sheet_name='RA Result', index=False)
                ra_score_raw.to_excel(
                    writer, sheet_name='RA Score Raw', index=False)
                ra_score.to_excel(writer, sheet_name='RA Score', index=False)
                # raw data
                for k, v in request.session.items():
                    if k.startswith('table'):
                        if v is None:
                            pd.DataFrame({
                                'msg': ['no value']
                            }).to_excel(
                                writer, 
                                sheet_name=k[6:].title().replace("_", " ")
                            )
                        else:
                            pd.read_json(v).to_excel(
                                writer, 
                                sheet_name=k[6:].title().replace("_", " ")
                            )

            file_name = 'RA Result.xlsx'
            response = HttpResponse(
                buffer.getvalue(),
                content_type=(
                    'application/'
                    'vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            )
            response['Content-Disposition'] = f'attachment; filename={file_name}'
            return response
        return redirect(reverse_lazy('reliabilities:search'))

class UShapeView(TemplateView):
    template_name = 'reliabilities/ushape.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['experiments'] = Experiment.objects.all()
        if experiment_name := self.request.GET.get('experiment'):
            ushape = UShape(experiment_name)
            context['q'] = True
            context['plot'] = ushape.vt_curve['plot']
            self.request.session['vt_curve'] = ushape.vt_curve['data'].to_json()
            self.request.session['voltage_setting'] = (
                ushape.voltage_setting.to_json()
            )

        return context

    def get(self, request, *args, **kwargs):
        if request.GET.get('download'):
            buffer = BytesIO()
            with pd.ExcelWriter(buffer) as writer:
                pd.read_json(
                    request.session['voltage_setting']
                ).to_excel(writer, sheet_name='Voltage Setting', index=False)
                pd.read_json(
                    request.session['vt_curve']
                ).to_excel(writer, sheet_name='VT curve', index=False)

            response = HttpResponse(
                    buffer.getvalue(),
                    content_type=(
                        'application/'
                        'vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    )
                )
            filename = 'ushape_volgate_setting.xlsx'
            response['Content-Disposition'] = (
                f'attachment; filename={filename}'
            )
            return response

        return super().get(request, *args, **kwargs)
