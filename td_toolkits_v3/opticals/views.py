from io import BytesIO
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
import pandas as pd

from django.urls import reverse_lazy
from django.views.generic import (
    TemplateView,
    ListView,
    DetailView,
    View,
)
from django.views.generic.edit import FormView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from td_toolkits_v3.materials.models import LiquidCrystal

from td_toolkits_v3.opticals.tools.utils import (
    OptResultGenerator, 
    OptictalsScore,
)

from .forms import (
    AxoUploadForm,
    RDLCellGapUploadForm,
    OptUploadForm,
    ResponseTimeUploadForm,
    CalculateOpticalForm,
)
from .models import (
    OpticalReference, 
    OpticalsFittingModel,
    OpticalSearchProfile
)


class IndexView(TemplateView):
    template_name = 'opticals/index.html'


class AxoUploadView(FormView):
    template_name = 'opticals/axo_upload.html'
    form_class = AxoUploadForm
    success_url = reverse_lazy('opticals:axo_upload')

    def form_valid(self, form):
        form.save(self.request)
        return super().form_valid(form)

class RDLCellGapUploadView(FormView):
    template_name = 'form_generic.html'
    form_class = RDLCellGapUploadForm
    success_url = reverse_lazy('opticals:rdl_cell_gap_upload')

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "RDL Cell Gap Upload"
        return context

class OptUploadView(FormView):
    template_name = 'form_generic.html'
    form_class = OptUploadForm
    success_url = reverse_lazy('opticals:toc_opt_log_upload')

    def form_valid(self, form):
        form.save(self.request)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "TOC OPT Upload"
        return context

class ResponseTimeUploadView(FormView):
    template_name = 'form_generic.html'
    form_class = ResponseTimeUploadForm
    success_url = reverse_lazy('opticals:toc_rt_log_upload')

    def form_valid(self, form):
        form.save(self.request)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'TOC Response Time Upload'
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

class CalculateOpticalView(FormView):
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

class OpticalSearchProfileCreateView(CreateView):
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

class OpticalSearchProfileUpdateView(UpdateView):
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
            OpticalsFittingModel.objects.all()
            .values_list('lc__name')
            .order_by('modified')
            .distinct()
        ]
        context['profile_list'] = [
            i[0] for i in
            OpticalSearchProfile.objects.all()
            .values_list('name')
            .order_by('modified')
        ]
        context['profile'] = get_object_or_404(
            OpticalSearchProfile,
            name=self.request.session['profile']
        )

        header = {
            "ref_product__product_model_type__name": "Product",
            "ref_product__product_model_type__factory__name": "Factory",
            "ref_product__lc__name": "LC",
            "ref_product__cell_gap": "Cell Gap",
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
            .filter(name=self.request.session['profile'])
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
            ref = (profile_df['Factory'][0], profile_df['Product'][0])
            results = []
            for lc in lc_list:
                result_generator = OptResultGenerator(lc, ref)
                results += [result_generator.table]

            # concat all results into one table
            result = pd.concat(results, ignore_index=True)
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
