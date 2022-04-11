import imp
from re import template
from django.urls import reverse_lazy

from django.views.generic import (
    ListView,
    CreateView,
)
from django.views.generic.edit import FormView

from .models import (
    Chip,
)
from .forms import ChipsUploadForm

class ChipListView(ListView):
    model = Chip
    paginate_by = 100

class ChipsBatchCreateView(FormView):
    template_name = 'form_generic.html'
    form_class = ChipsUploadForm
    success_url = reverse_lazy('products:chip_list')

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Chips Upload'
        context['file_path'] = reverse_lazy('materials:template') \
                             + '?download=optical_condition_upload_template'

        return context