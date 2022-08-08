from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import (
    ListView,
    TemplateView
)
from django.views.generic.edit import FormView
from django.core.cache import cache

import pandas as pd

from .models import (
    Chip,
)
from .forms import ChipsUploadForm

class ChipListView(ListView):
    model = Chip
    paginate_by = 100

class ChipsBatchCreateView(LoginRequiredMixin, FormView):
    template_name = 'form_generic.html'
    form_class = ChipsUploadForm
    success_url = reverse_lazy('products:chip_upload_success')

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Chips Upload'
        context['file_path'] = reverse_lazy('materials:template') \
                             + '?download=optical_condition_upload_template'

        return context
    
class ChipBatchCreateSuccessView(TemplateView):
    template_name = 'success_generic.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Chips Upload Success'
        df: pd.DataFrame = cache.get('df')
        context['log'] = cache.get('save_log')
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
            "RDL Upload": reverse_lazy('opticals:rdl_cell_gap_upload'),
            "AXO Upload": reverse_lazy('opticals:axo_upload'),
        }
        return context