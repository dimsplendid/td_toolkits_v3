from django.views.generic import (
    TemplateView,
    FormView,
)
from django.urls import reverse_lazy

from . import forms

class Index(TemplateView):
    template_name: str = 'base.html'
    
class RealiabilitySystemTest(FormView):
    template_name: str = 'form_generic.html'
    success_url = reverse_lazy('autofill:ras-test')
    form_class = forms.ReliabilityTestForm
    
    def form_valid(self, form):
        form.save()
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'RAS Autofill Test'
        return context