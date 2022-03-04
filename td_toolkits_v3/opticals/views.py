from django.urls import reverse_lazy
from django.views.generic import (
    TemplateView,
)
from django.views.generic.edit import FormView

from td_toolkits_v3.materials.forms import MaterialsUploadForm


class IndexView(TemplateView):
    template_name = 'opticals/index.html'


class OpticalsUploadView(TemplateView):
    template_name = 'opticals/upload.html'
    success_url = reverse_lazy('opticals:upload')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['materials_form'] = MaterialsUploadForm(**kwargs)
        # context['chips_form'] = ChipsUploadForm()
        
        return context
