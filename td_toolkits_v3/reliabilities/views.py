from django.urls import reverse_lazy
from django.views.generic import (
    TemplateView,
    ListView,
    DetailView,
)

class IndexView(TemplateView):
    template_name = 'reliabilities/index.html'