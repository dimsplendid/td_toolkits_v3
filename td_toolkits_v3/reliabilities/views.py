from django.urls import reverse_lazy
from django.views.generic import (
    TemplateView,
    ListView,
    DetailView,
)
from django.views.generic.edit import FormView

from .forms import (
    ReliabilitiesUploadForm
)

class IndexView(TemplateView):
    template_name = 'reliabilities/index.html'

class ReliabilitiesUploadView(FormView):
    template_name = 'upload_generic.html'
    form_class = ReliabilitiesUploadForm
    success_url = reverse_lazy('reliabilities:index')

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)