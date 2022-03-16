from django.urls import reverse_lazy
from django.views.generic import (
    TemplateView,
    ListView
)
from django.views.generic.edit import FormView, CreateView, UpdateView

from .forms import (
    AxoUploadForm,
    RDLCellGapUploadForm,
    OptUploadForm,
    ResponseTimeUploadForm,
)
from .models import OpticalReference

class IndexView(TemplateView):
    template_name = 'opticals/index.html'


class OpticalsUploadView(TemplateView):
    template_name = 'opticals/upload.html'


class AxoUploadView(FormView):
    template_name = 'opticals/axo_upload.html'
    form_class = AxoUploadForm
    success_url = reverse_lazy('opticals:axo_upload')

    def form_valid(self, form):
        form.save(self.request)
        return super().form_valid(form)

class RDLCellGapUploadView(FormView):
    template_name = 'upload_generic.html'
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
    template_name = 'upload_generic.html'
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
    template_name = 'upload_generic.html'
    form_class = ResponseTimeUploadForm
    success_url = reverse_lazy('opticals:toc_rt_log_upload')

    def form_valid(self, form):
        form.save(self.request)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'TOC Response Time Upload'
        return context


class OpticalReferenceCreateView(CreateView):
    template_name = 'upload_generic.html'
    model = OpticalReference
    fields = [
        'product_model_type',
        'lc',
        'pi',
        'seal',
        'cell_gap',
        'ito_slit',
        'tft_tech',
    ]

class OpticalReferenceUpdateView(UpdateView):
    template_name = 'upload_generic.html'
    model = OpticalReference
    fields = [
        'product_model_type',
        'lc',
        'pi',
        'seal',
        'cell_gap',
        'ito_slit',
        'tft_tech',
    ]

class OpticalReferenceListView(ListView):
    model = OpticalReference