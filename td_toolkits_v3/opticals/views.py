from io import BytesIO
from typing import List, Dict, Tuple, Union, Optional, Any

import pandas as pd
import plotly.express as px
from plotly.offline import plot

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import (
    TemplateView,
    ListView,
    DetailView,
    View,
)
from django.views.generic.edit import FormView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache

from td_toolkits_v3.materials.models import LiquidCrystal
from td_toolkits_v3.products.models import Experiment

from td_toolkits_v3.opticals.tools.utils import (
    # OptResultGenerator, 
    OptTableGenerator,
    OptictalsScore,
    OptLoader,
)

from .forms import (
    AxoUploadForm,
    RDLCellGapUploadForm,
    OptUploadForm,
    ResponseTimeUploadForm,
    CalculateOpticalForm,
    ProductModelTypeForm,
    OpticalReferenceFormset,
    OptFittingForm,
    RTFittingForm,
    OpticalPhaseTwoForm,
    AdvancedContrastRatioForm,
    BackLightUnitUploadForm,
)
from .models import (
    OpticalReference, 
    OpticalsFittingModel,
    OpticalSearchProfile,
    OptFittingModel,
    RTFittingModel,
    BackLightUnit,
)


class IndexView(TemplateView):
    template_name = 'opticals/index.html'


class AxoUploadView(LoginRequiredMixin, FormView):
    template_name = 'opticals/axo_upload.html'
    form_class = AxoUploadForm
    success_url = reverse_lazy('opticals:axo_upload_success')

    def form_valid(self, form):
        form.save(self.request)
        return super().form_valid(form)
    
class AxoUploadSuccessView(TemplateView):
    template_name = 'success_generic.html'
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['title'] = 'Axo Upload Success'
        df: pd.DataFrame = cache.get('df')
        context['log']: dict[str, list] = cache.get('save_log')
        try:
            context['table'] = df.to_html(
                float_format=lambda x: f'{x:.4f}',
                classes='table table-striped table-bordered table-hover',
                justify='center',
                index=False,
                escape=False,
            )
        except:
            context['table'] = None
        context['nexts'] = {
            "OPT Upload": reverse_lazy('opticals:toc_opt_log_upload'),
        }
        return context

class RDLCellGapUploadView(LoginRequiredMixin, FormView):
    template_name = 'form_generic.html'
    form_class = RDLCellGapUploadForm
    success_url = reverse_lazy('opticals:rdl_cell_gap_upload_success')

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "RDL Cell Gap Upload"
        context['file_path'] = reverse_lazy('materials:template') \
                             + '?download=optical_rdl_cellgap_upload_template'
        return context

class RDLCellGapUploadSuccessView(TemplateView):
    template_name = 'success_generic.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "RDL Cell Gap Upload Success"
        context['log'] = cache.get('save_log')
        try:
            context['table'] = cache.get('df').to_html(
                float_format=lambda x: f'{x:.4f}',
                classes='table table-striped table-bordered table-hover',
                justify='center',
                index=False,
                escape=False,
            )
        except:
            context['table'] = None
            
        context["nexts"] = {
            "AXO Upload": reverse_lazy('opticals:axo_upload'),
            "OPT Upload": reverse_lazy('opticals:toc_opt_log_upload'),
        }
        return context

class OptUploadView(LoginRequiredMixin, FormView):
    template_name = 'form_generic.html'
    form_class = OptUploadForm
    success_url = reverse_lazy('opticals:toc_opt_log_upload_success')

    def form_valid(self, form):
        form.save(self.request)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "TOC OPT Upload"
        return context

class OptUploadSuccessView(TemplateView):
    template_name: str = 'success_generic.html'
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['title'] = 'TOC OPT Upload Success'
        context['log'] = cache.get('save_log')
        context['nexts'] = {
            "RT Upload": reverse_lazy('opticals:toc_rt_log_upload'),
            "OPT Fitting": reverse_lazy('opticals:opt_fitting'),
        }
        return context
                
class ResponseTimeUploadView(LoginRequiredMixin, FormView):
    template_name = 'form_generic.html'
    form_class = ResponseTimeUploadForm
    success_url = reverse_lazy('opticals:toc_rt_log_upload_success')

    def form_valid(self, form):
        form.save(self.request)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'TOC Response Time Upload'
        return context

class ResponseTimeUploadSuccessView(TemplateView):
    template_name = 'success_generic.html'
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['title'] = 'TOC Response Time Upload Success'
        context['log'] = cache.get('save_log')
        context['nexts'] = {
            "OPT Upload": reverse_lazy('opticals:toc_opt_log_upload'),
            "RT Fitting": reverse_lazy('opticals:rt_fitting'),
        }
        return context

class OpticalReferenceCreateView(LoginRequiredMixin, CreateView):
    template_name = 'form_generic.html'
    model = OpticalReference
    fields = [
        'product_model_type',
        'lc',
        'pi',
        'seal',
        'cell_gap',
        'ito_slit',
        'tft_tech',
        'transmittance',
        'time_rise',
        'time_fall',
        'gray_to_gray',
        'w_x',
        'w_y',
        'contrast_ratio',
    ]

class OpticalReferenceUpdateView(LoginRequiredMixin, UpdateView):
    template_name = 'form_generic.html'
    model = OpticalReference
    fields = [
        'lc',
        'pi',
        'seal',
        'cell_gap',
        'ito_slit',
        'tft_tech',
        'transmittance',
        'time_rise',
        'time_fall',
        'gray_to_gray',
        'w_x',
        'w_y',
        'contrast_ratio',
    ]
    

class OpticalReferenceListView(ListView):
    model = OpticalReference

class OpticalReferenceDetailView(DetailView):
    model = OpticalReference

class OptFittingView(LoginRequiredMixin, FormView):
    form_class = OptFittingForm
    template_name = 'form_generic.html'

    def form_valid(self, form):
        form.calculate(self.request)
        return super().form_valid(form)
    success_url = reverse_lazy('opticals:opt_fitting_check')

class RTFittingView(LoginRequiredMixin, FormView):
    form_class = RTFittingForm
    template_name = 'form_generic.html'

    def form_valid(self, form):
        form.calculate(self.request)
        return super().form_valid(form)
    success_url = reverse_lazy('opticals:rt_fitting_check')
    
class FittingCheckBaseView(TemplateView):
    template_name = 'opticals/calculate_check.html'
    
    def get(self, request, *args, **kwargs):
        if request.GET.get('experiment'):
            request.session['exp_id'] = request.GET.get('experiment')

        return super().get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['message'] = self.request.session.get('message')
        # render r2 score table
        all_r2 = []
        models = kwargs['model'].objects.filter(
            experiment__name = self.request.session['exp_id']
        ).values('lc__name', 'pi__name', 'seal__name','r2')
        for record in models:
            df = pd.DataFrame(record['r2'], index=[0])
            df.insert(0, 'LC', record['lc__name'])
            df.insert(1, 'PI', record['pi__name'])
            df.insert(2, 'Seal', record['seal__name'])
            all_r2.append(df)
        df = pd.concat(all_r2, ignore_index=True)
        # changing some notation to make it easier see on website
        df.columns = [column.replace('|->', '=') for column in df.columns]
        df.columns = [column.replace('Cell Gap', 'd') for column in df.columns]
        # add link to LC
        # def url(x):
        #     url = reverse_lazy("materials:lc_detail", kwargs={'slug': x.lower()})
        #     return f'<a href="{url}">{x}</a>'
        # df['LC'] = df['LC'].apply(url)
        
        context['table'] = df.to_html(
            float_format=lambda x: f'{x:.3f}',
            classes=['table', 'table-hover', 'text-center', 'table-striped'],
            justify='center',
            index=False,
            escape=False,
        )
        context['id'] = self.request.session['exp_id']
        return context

class OptFittingCheckView(FittingCheckBaseView):
    def get_context_data(self, **kwargs):
        return super().get_context_data(model=OptFittingModel,**kwargs)

class RTFittingCheckView(FittingCheckBaseView):
    def get_context_data(self, **kwargs):
        return super().get_context_data(model=RTFittingModel,**kwargs)

class CalculateOpticalView(LoginRequiredMixin, FormView):
    form_class = CalculateOpticalForm
    template_name = 'form_generic.html'

    def form_valid(self, form):
        form.calculate(self.request)
        return super().form_valid(form)
    success_url = reverse_lazy('opticals:calculate_check')

class CalculateCheckView(TemplateView):
    # Todo: check and update to data base
    # form_class = None
    template_name = 'opticals/calculate_check.html'

    def get(self, request, *args, **kwargs):
        if request.GET.get('experiment'):
            request.session['exp_id'] = request.GET.get('experiment')

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['message'] = self.request.session.get('message')
        # render r2 score table
        all_r2 = []
        models = OpticalsFittingModel.objects.filter(
            experiment__name = self.request.session['exp_id']
        ).values('lc__name','r2')
        for record in models:
            df = pd.DataFrame(record['r2'], index=[0])
            df.insert(0, 'LC', record['lc__name'])
            all_r2.append(df)
        df = pd.concat(all_r2, ignore_index=True)
        # changing some notation to make it easier see on website
        df.columns = [column.replace('|->', '=') for column in df.columns]
        df.columns = [column.replace('Cell Gap', 'd') for column in df.columns]
        # add link to LC
        def url(x):
            url = reverse_lazy("materials:lc_detail", kwargs={'slug': x.lower()})
            return f'<a href="{url}">{x}</a>'
        df['LC'] = df['LC'].apply(url)
        context['table'] = df.to_html(
            float_format=lambda x: f'{x:.3f}',
            classes=['table', 'table-hover', 'text-center', 'table-striped'],
            justify='center',
            index=False,
            escape=False,
        )
        context['id'] = self.request.session['exp_id']
        return context

class OpticalSearchProfileListView(ListView):
    model = OpticalSearchProfile

class OpticalSearchProfileDetailView(DetailView):
    model = OpticalSearchProfile

class OpticalSearchProfileCreateView(LoginRequiredMixin, CreateView):
    template_name = 'form_generic.html'
    model = OpticalSearchProfile
    fields = [
        'name',
        'ref_product',
        'lc_percent',
        'lc_percent_weight',
        'response_time',
        'response_time_weight',
        'delta_e_ab',
        'delta_e_ab_weight',
        'contrast_ratio',
        'contrast_ratio_weight',
        'remark',
    ]

class OpticalSearchProfileUpdateView(LoginRequiredMixin, UpdateView):
    template_name = 'form_generic.html'
    model = OpticalSearchProfile
    fields = [
        'name',
        'ref_product',
        'lc_percent',
        'lc_percent_weight',
        'response_time',
        'response_time_weight',
        'delta_e_ab',
        'delta_e_ab_weight',
        'contrast_ratio',
        'contrast_ratio_weight',
        'remark',
    ]
    def get(self, request, *args, **kwargs):
        request.session['next'] = request.GET.get('next')

        return super().get(request, *args, **kwargs)

    def get_success_url(self) -> str:
        if self.request.session['next']:
            return self.request.session['next']
        return super().get_success_url()

class OpticalSearchProfileCopyView(OpticalSearchProfileUpdateView):
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        obj.pk = None
        obj.name = obj.name + '-copy'
        obj.slug = None
        
        return obj

class OpticalSearchView(TemplateView):
    template_name = 'opticals/search.html'
    def get(self, request, *args, **kwargs):
        # setting the profile through get method
        if request.GET.get('profile'):
            request.session['profile'] = request.GET.get('profile')
        else:
            request.session['profile'] = 'Default'
        
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lc_list'] = [
            i[0] for i in 
            OptFittingModel.objects.all()
            .values_list('lc__name')
            # Seems distinct is not compatible to order_by
            # .order_by('modified') 
            .distinct()
        ]
        context['profile_list'] = OpticalSearchProfile.objects.all()
            
        context['profile'] = get_object_or_404(
            OpticalSearchProfile,
            slug=self.request.session['profile']
        )

        header = {
            "ref_product__product_model_type__name": "Product",
            "ref_product__product_model_type__factory__name": "Factory",
            "ref_product__lc__name": "LC",
            "ref_product__cell_gap": "Cell Gap",
            'ref_product__voltage': 'Voltage',
            'response_time': 'RT',
            'response_time_weight': 'w(RT)',
            "lc_percent": "LC%",
            "lc_percent_weight": "w(LC%)",
            'delta_e_ab':  'ΔEab*',
            'delta_e_ab_weight':  'w(ΔEab*)',
            'contrast_ratio': 'CR',
            'contrast_ratio_weight': 'w(CR)',
            'remark': 'Remark'
        }
        profile_df = pd.DataFrame.from_records(
            OpticalSearchProfile.objects
            .filter(slug=self.request.session['profile'])
            .values(*header)
        ).rename(
            columns=header
        )
        context['profile_table'] = profile_df.to_html(
            float_format=lambda x: f'{x:.2f}',
            classes=['table', 'table-hover', 'text-center', 'table-striped'],
            justify='center',
            index=False,
            escape=False,
        )
        lc_list = self.request.GET.getlist('q')
        context['q'] = lc_list
        context['q_lc_list'] = None
        if lc_list:
            context['q_lc_list'] = LiquidCrystal.objects.filter(
                name__in=lc_list)
            # store lc list cookies to for the ra searching
            ref = OpticalReference.objects.get(
                product_model_type__name=profile_df['Product'][0],
                product_model_type__factory__name=profile_df['Factory'][0],
            )
            # concat all results into one table
            opt_result_generator = OptTableGenerator(
                lc_list=lc_list,
                reference=ref, 
                mode='search',
            )
            opt_result_generator.calc()
            results = opt_result_generator.tables
            result = results['Vref'].dropna()
            self.request.session['result'] = {
                k: v.to_json() for
                k, v in results.items()
            }
            opt_score = OptictalsScore(result, profile_df)
            self.request.session['opt_result'] = result.to_json()
            self.request.session['opt_plot'] = opt_score.plot
            self.request.session['opt_score_raw'] = opt_score.data.to_json()
            self.request.session['opt_score'] = opt_score.score.to_json()
            # Only transfer success result to next level
            self.request.session['opt_lc_list'] = list(
                opt_score.score['LC'].unique())

            context['opt_plot'] = opt_score.plot
            context['opt_score'] = opt_score.score.to_html(
                float_format=lambda x: f'{x:.2f}',
                classes=['table', 'table-hover', 'text-center', 'table-striped'],
                justify='center',
                index=False,
                escape=False,
            )
            context['opt_score_raw'] = opt_score.data.to_html(
                float_format=lambda x: f'{x:.2f}',
                classes=['table', 'table-hover', 'text-center', 'table-striped'],
                justify='center',
                index=False,
                escape=False,
            )
        return context

class OpticalSearchResultDownload(View):
    def get(self, request, *args, **kwargs):
        if 'opt_result' in request.session:
            opt_result = pd.read_json(request.session['opt_result'])
            opt_score_raw = pd.read_json(request.session['opt_score_raw'])
            opt_score = pd.read_json(request.session['opt_score'])
            # print(request.session['opt_result'])
            with BytesIO() as b:
                writer = pd.ExcelWriter(b, engine='openpyxl')
                opt_result.to_excel(
                    writer, sheet_name='OPT Result', index=False)
                opt_score_raw.to_excel(
                    writer, sheet_name='OPT Score Raw', index=False)
                opt_score.to_excel(
                    writer, sheet_name='OPT Score', index=False)
                writer.save()
                file_name = 'OPT Result.xlsx'
                response = HttpResponse(
                    b.getvalue(),
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                response['Content-Disposition'] = f'attachment; filename={file_name}'
                return response
        return redirect(reverse_lazy('opticals:search'))

class ProductModelTypeCreateView(CreateView):
    form_class = ProductModelTypeForm
    template_name = 'formset_generic.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Ref Product Create'

        context['formset'] = OpticalReferenceFormset()
        return context

    def post(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        optical_reference_formset = OpticalReferenceFormset(self.request.POST)

        if form.is_valid() and optical_reference_formset.is_valid():
            return self.form_valid(form, optical_reference_formset)
        else:
            return self.form_invalid(form, optical_reference_formset)

    def form_valid(self, form, formset):
        self.object = form.save(commit=False)
        self.object.save()
        # saving OpticalReference Instances
        optical_references = formset.save(commit=False)
        for ref in optical_references:
            ref.product_model_type = self.object
            ref.save()
        return redirect(reverse_lazy('opticals:ref_list'))

    def form_invalid(self, form, formset):
        return self.render_to_response(
            self.get_context_data(
                form=form,
                formset=formset,
            )
        )

class OpticalDataDumpView(TemplateView):
    template_name = 'opticals/data_dump.html'

    def get(self, request, *args, **kwargs):
        if exp_name := request.GET.get('exp'):
            cell_gap = request.GET.get('cell_gap')
            if cell_gap == 'None':
                cell_gap = None

            data_loader = OptLoader(exp_name, cell_gap)
            opt_df = data_loader.opt
            # if there is rt data, export either
            try:
                rt_df = data_loader.rt
            except:
                rt_df = None

            file_name = exp_name + '.xlsx'

            buffer = BytesIO()
            with pd.ExcelWriter(buffer) as writter:
                opt_df.to_excel(writter,sheet_name='OPT', index=False)
                if rt_df is not None:
                    rt_df.to_excel(writter,sheet_name='RT', index=False)
            
            response = HttpResponse(
                buffer.getvalue(),
                content_type=(
                    'application/'
                    'vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
            )
            response['Content-Disposition'] = f'attachment; filename={file_name}'
            return response

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['exps'] = Experiment.objects.all()
        return context
    
class OpticalPhaseTwoView(LoginRequiredMixin, FormView):
    template_name: str = 'form_generic.html'
    form_class = OpticalPhaseTwoForm
    success_url = reverse_lazy('opticals:tr2_success')
    
    def form_valid(self, form):
        form.calc(self.request)
        return super().form_valid(form)
    
class OpticalPhaseTwoSuccessView(View):
    def get(self, request, *args, **kwargs):
        if 'result' in  request.session:            
            with BytesIO() as b:
                writer = pd.ExcelWriter(b, engine='openpyxl')
                for k, v in request.session['result'].items():
                    pd.read_json(v).to_excel(writer, sheet_name=k, index=False)
                writer.save()
                file_name = 'OPT Result.xlsx'
                response = HttpResponse(
                    b.getvalue(),
                    content_type=(
                        'application/'
                        'vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    )
                )
                response['Content-Disposition'] = f'attachment; filename={file_name}'
                return response
            
class AdvancedContrastRatioIndexView(TemplateView):
    template_name = 'opticals/advanced_contrast_index.html'
            
class AdvancedContrastRatioView(FormView):
    template_name: str = 'form_generic.html'
    form_class = AdvancedContrastRatioForm
    success_url: Optional[str] = reverse_lazy(
        'opticals:advanced_contrast_ratio_success'
    )
    
    def form_valid(self, form):
        form.calc(self.request)
        return super().form_valid(form)
    

class AdvancedContrastRatioSuccessView(TemplateView):
    template_name: str = 'opticals/advanced_contrast_ratio_success.html'
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['title'] = 'Advanced Contrast Ratio'
        result: pd.DataFrame = (cache.get('result'))
        context['result'] = result.to_html(
            float_format=lambda x: f'{x:.2f}',
            classes=['table', 'table-hover', 'text-center', 'table-striped'],
            justify='center',
            index=False,
            escape=False,
        )
        return context
    
class BackLightUnitUploadView(FormView):
    template_name: str = 'form_generic.html'
    form_class = BackLightUnitUploadForm
    success_url: Optional[str] = reverse_lazy(
        'opticals:blu_upload_success'
    )
    
    def form_valid(self, form):
        form.save()
        return super().form_valid(form)
    
class BackLightUnitUploadSuccessView(TemplateView):
    template_name: str = 'opticals/back_light_unit_upload_success.html'
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['title'] = 'Back Light Unit Upload Success'
        
        # Draw the uploaded data
        blu: BackLightUnit = cache.get('blu')
        blu_df = pd.DataFrame(
            blu.back_light_intensity.values('wavelength', 'value')
        )
        blu_df.columns = ['wavelength(nm)', 'intensity(a.u.)']
        fig = px.line(blu_df, x='wavelength(nm)', y='intensity(a.u.)')
        context['plot'] = plot(fig, output_type='div')
        return context