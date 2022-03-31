from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import (
    TemplateView,
    ListView,
    DetailView,
)
from django.views.generic.edit import (
    CreateView,
    FormView,
    UpdateView,
)

from td_toolkits_v3.materials.models import (
    LiquidCrystal,
    Polyimide,
    Seal,
)

from .forms import (
    ReliabilitiesUploadForm
)
from .models import ReliabilitySearchProfile


class IndexView(TemplateView):
    template_name = 'reliabilities/index.html'

class ReliabilitySearchProfileListView(ListView):
    model = ReliabilitySearchProfile

class ReliabilitySearchProfileDetailView(DetailView):
    model = ReliabilitySearchProfile

class ReliabilitySearchProfileCreateView(CreateView):
    template_name = 'upload_generic.html'
    model = ReliabilitySearchProfile
    fields = [
        'name',
        'voltage_holding_ratio',
        'voltage_holding_ratio_venders',
        'voltage_holding_ratio_weight',
        'delta_angle',
        'delta_angle_venders',
        'delta_angle_weight',
        'adhesion',
        'adhesion_venders',
        'adhesion_weight',
        'low_temperature_storage',
        'low_temperature_storage_venders',
        'low_temperature_storage_weight',
        'pressure_cooking_test',
        'pressure_cooking_test_venders',
        'pressure_cooking_test_weight',
        'seal_wvtr',
        'seal_wvtr_venders',
        'seal_wvtr_weight',
        'u_shape_ac',
        'u_shape_ac_venders',
        'u_shape_ac_weight',
    ]

class ReliabilitySearchProfileUpdateView(UpdateView):
    template_name = 'upload_generic.html'
    model = ReliabilitySearchProfile
    fields = [
        'name',
        'voltage_holding_ratio',
        'voltage_holding_ratio_venders',
        'voltage_holding_ratio_weight',
        'delta_angle',
        'delta_angle_venders',
        'delta_angle_weight',
        'adhesion',
        'adhesion_venders',
        'adhesion_weight',
        'low_temperature_storage',
        'low_temperature_storage_venders',
        'low_temperature_storage_weight',
        'pressure_cooking_test',
        'pressure_cooking_test_venders',
        'pressure_cooking_test_weight',
        'seal_wvtr',
        'seal_wvtr_venders',
        'seal_wvtr_weight',
        'u_shape_ac',
        'u_shape_ac_venders',
        'u_shape_ac_weight',
    ]

class ReliabilitiesUploadView(FormView):
    template_name = 'upload_generic.html'
    form_class = ReliabilitiesUploadForm
    success_url = reverse_lazy('reliabilities:index')

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

class ReliabilitySearchView(TemplateView):
    template_name = 'reliabilities/search.html'

    def get_context_data(self, **kwargs) :
        context = super().get_context_data(**kwargs)
        profile = self.request.GET.get('profile')
        if profile is None:
            profile = 'default'

        if self.request.GET.get('pure'):
            self.request.session['opt_lc_list'] = None
        
        # opt result part
        if self.request.session['opt_lc_list']:
            pass
        
        # ra part
        context['lc_list'] = LiquidCrystal.objects.all()
        context['pi_list'] = Polyimide.objects.all()
        context['seal_list'] = Seal.objects.all()

        context['profile_list'] = ReliabilitySearchProfile.objects.all()
        context['profile'] = get_object_or_404(
            ReliabilitySearchProfile,
            slug=profile
        )
        query = self.configuration_query()
        if query is not None:
            context['q'] = True
            q_lc, q_pi, q_seal = query
            context['q_lc_list'] = q_lc
            context['q_pi_list'] = q_pi
            context['q_seal_list'] = q_seal

        return context

    def configuration_query(self):
        lc_list = self.request.GET.getlist('lc_list')
        pi_list = self.request.GET.getlist('pi_list')
        seal_list = self.request.GET.getlist('seal_list')
        if (not lc_list) and (not pi_list) and (not seal_list):
            return None

        def qeury(model, qlist):
            print(qlist)
            if (not qlist) or ('ALL' in qlist):
                return model.objects.all()
            else:
                return model.objects.filter(name__in=qlist)

        q_lc = qeury(LiquidCrystal, lc_list)
        q_pi = qeury(Polyimide, pi_list)
        q_seal = qeury(Seal, seal_list)

        return (q_lc, q_pi, q_seal)
    