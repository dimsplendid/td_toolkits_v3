from django.db import models
from django.urls import reverse

from autoslug import AutoSlugField
from model_utils.models import TimeStampedModel


class Vender(TimeStampedModel):
    name = models.CharField(
        "Name of Vender", max_length=255, unique=True)
    slug = AutoSlugField(
        "Vender Address",
        unique=True, always_update=False, populate_from="name")

    def __str__(self):
        return self.name


def get_default_vender():
    return Vender.objects.get_or_create(name="INX")[0]


class LiquidCrystal(TimeStampedModel):
    name = models.CharField(
        "Name of Liquid Crystal", 
        max_length=255, unique=True)
    slug = AutoSlugField(
        "LC Address",
        unique=True, always_update=False, populate_from="name")
    vender = models.ForeignKey(
        Vender,
        default=get_default_vender, on_delete=models.CASCADE)
    designed_cell_gap = models.FloatField(null=True, blank=True)
    t_ni = models.FloatField('Tni(°C)', null=True, blank=True)
    t_cn = models.FloatField('Tcn(°C)', null=True, blank=True)
    flow_viscosity = models.FloatField(
        'ν(mm^2/s)', 
        null=True, blank=True)
    rotational_viscosity = models.FloatField(
        'γ1(mPa*s)', 
        null=True, blank=True)
    n_e = models.FloatField(null=True, blank=True)
    n_o = models.FloatField(null=True, blank=True)
    e_para = models.FloatField('ε_∥', null=True, blank=True)
    e_perp = models.FloatField('ε_⟂', null=True, blank=True)
    k_11 = models.FloatField('K11(pN)', null=True, blank=True)
    k_22 = models.FloatField('K22(pN)', null=True, blank=True)
    k_33 = models.FloatField('K33(pN)', null=True, blank=True)
    density = models.FloatField('d(g/cm^3)', null=True, blank=True)

    # Some property extend from others.
    @property
    def delta_n(self):
        if (self.n_e is None) or (self.n_o is None):
            return None
        else:
            return self.n_e - self.n_o

    @property
    def retardation(self): 
        if (self.designed_cell_gap is None) or (self.delta_n is None):
            return None
        else:
            return self.designed_cell_gap * self.delta_n * 1000

    @property
    def delta_e(self):
        if (self.e_para is None) or (self.e_perp is None):
            return None
        else:
            return self.e_para - self.e_perp
    
    @property
    def scatter_index(self):
        """The higher, the brighter at dark state.(lower CR)"""
        if (self.delta_n is None) \
            or (self.k_11 is None) or (self.k_33 is None):
            return None
        
        n_e = self.n_e
        n_o = self.n_o
        k_11 = self.k_11
        k_22 = self.k_22 if self.k_22 is not None else (k_11/2)
        k_33 = self.k_33
        return (n_e**2 - n_o**2)**2 * 3 / (k_11 + k_22 + k_33)
        
        

    @property
    def response_index(self):
        """The higher, the slower.(no cell gap)"""
        if (self.rotational_viscosity is None) \
            or (self.k_11 is None):
            return None

        k_22 = self.k_22 if self.k_22 is not None else (self.k_11/2)
        return self.rotational_viscosity / k_22
    
    @property
    def vt_index(self):
        """The higher, the higher LC%"""
        if (self.delta_e is None) or (self.k_11 is None):
            return None
        return abs(self.delta_e / self.k_11)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        """Return absolute URL to the LC Detail page."""
        return reverse(
            'materials:lc_detail', kwargs={"slug": self.slug}
        )

class Polyimide(TimeStampedModel):
    name = models.CharField(
        "Name of Polyimide", 
        max_length=255, unique=True)
    slug = AutoSlugField(
        "LC Address",
        unique=True, always_update=False, populate_from="name")
    vender = models.ForeignKey(
        Vender,
        default=get_default_vender, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    # def get_absolute_url(self):
    #     """Return absolute URL to the LC Detail page."""
    #     return reverse(
    #         'materials:pi_detail', kwargs={"slug": self.slug}
    #     )


class Seal(TimeStampedModel):
    name = models.CharField(
        "Name of Seal", 
        max_length=255, unique=True)
    slug = AutoSlugField(
        "LC Address",
        unique=True, always_update=False, populate_from="name")
    vender = models.ForeignKey(
        Vender,
        default=get_default_vender, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    # def get_absolute_url(self):
    #     """Return absolute URL to the LC Detail page."""
    #     return reverse(
    #         'materials:pi_detail', kwargs={"slug": self.slug}
    #     )