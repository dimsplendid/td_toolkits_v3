from django.views.generic import (
    TemplateView,
)
from django.views.generic.edit import FormView


class IndexView(TemplateView):
    template_name = 'opticals/index.html'


class OpticalsUpload(FormView):
    template_name = 'opticals/upload.html'
    