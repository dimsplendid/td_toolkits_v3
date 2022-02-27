from django.urls import reverse_lazy
from django.views.generic import (
    TemplateView,
)
from django.views.generic.edit import FormView

from .forms import OpticalsUploadForm


class IndexView(TemplateView):
    template_name = 'opticals/index.html'


class OpticalsUploadView(FormView):
    template_name = 'opticals/upload.html'
    form_class = OpticalsUploadForm
    success_url = reverse_lazy('opticals:upload')

    def form_valid(self, form):
        form.save(self.request)
        return super().form_valid(form)