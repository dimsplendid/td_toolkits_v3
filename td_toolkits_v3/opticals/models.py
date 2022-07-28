from django.db import models
from django.urls import reverse

from autoslug import AutoSlugField
from model_utils.models import TimeStampedModel
from picklefield.fields import PickledObjectField


class Instrument(TimeStampedModel):
    name = models.CharField("Instrument Name", max_length=255)
    slug = AutoSlugField(
        "Instrument Address", unique=True, always_update=False, populate_from="name"
    )
    desc = models.TextField("description", blank=True)
    factory = models.ForeignKey(
        "products.Factory",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )

    @classmethod
    def default(cls, name, factory):
        return cls.objects.get_or_create(
            name=name,
            factory=factory,
        )[0]

    def __str__(self):
        return f"{self.name} (@{self.factory.name})"


class AxometricsLog(TimeStampedModel):
    chip = models.ForeignKey("products.Chip", on_delete=models.CASCADE)
    measure_point = models.SmallIntegerField()
    x_coord = models.FloatField()
    y_coord = models.FloatField()
    cell_gap = models.FloatField()
    top_rubbing_direct = models.FloatField()
    twist = models.FloatField()
    top_pretilt = models.FloatField()
    bottom_pretilt = models.FloatField()
    rms = models.FloatField()
    iteration = models.FloatField()
    instrument = models.ForeignKey(
        Instrument, on_delete=models.CASCADE, null=True, blank=True
    )

    def __str__(self):
        return (
            f"{self.chip.name}, p {self.measure_point}" + f", cell gap: {self.cell_gap}"
        )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["chip", "measure_point"], name="axo_chip_measure_point"
            )
        ]


class RDLCellGap(TimeStampedModel):
    # One to One relation can not duplicate.
    chip = models.OneToOneField(
        "products.Chip", on_delete=models.CASCADE, related_name="rdl_cell_gap"
    )
    cell_gap = models.FloatField()
    instrument = models.ForeignKey(
        Instrument, on_delete=models.CASCADE, null=True, blank=True
    )

    def __str__(self):
        return self.chip.name


class OpticalLog(TimeStampedModel):
    chip = models.ForeignKey("products.Chip", on_delete=models.CASCADE)
    measure_point = models.SmallIntegerField()
    measure_time = models.DateTimeField()
    instrument = models.ForeignKey(
        Instrument, on_delete=models.CASCADE, null=True, blank=True
    )
    operator = models.CharField(max_length=255)
    voltage = models.FloatField("Vop")
    lc_percent = models.FloatField()
    w_x = models.FloatField()
    w_y = models.FloatField()
    w_capital_y = models.FloatField("WY")

    @property
    def t_percent(self):
        max_lc_percent = max(
            self.objects.filter(
                chip=self.chip, measure_point=self.measure_point
            ).values_list("lc_percent")
        )[0]
        return self.lc_percent / max_lc_percent * 100

    def __str__(self):
        return (
            f"{self.chip.name}, p {self.measure_point} "
            + f"v: {self.voltage}, ({self.lc_percent},"
            + f"{self.w_x}, {self.w_y}, {self.w_capital_y})"
        )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["chip", "measure_point", "voltage"], name="opt_unique"
            )
        ]


class ResponseTimeLog(TimeStampedModel):
    chip = models.ForeignKey("products.Chip", on_delete=models.CASCADE)
    measure_point = models.SmallIntegerField("Point")
    measure_time = models.DateTimeField()
    instrument = models.ForeignKey(
        Instrument, on_delete=models.CASCADE, null=True, blank=True
    )
    operator = models.CharField(max_length=255)
    voltage = models.FloatField("Vop")
    time_rise = models.FloatField("Tr")
    time_fall = models.FloatField("Tf")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["chip", "measure_point", "voltage"], name="rt_unique"
            )
        ]


class OpticalReference(TimeStampedModel):
    """
    Cause **Reference** should be mass product.
    There would be only one optical reference for each product model type.
    """

    product_model_type = models.OneToOneField(
        "products.ProductModelType",
        on_delete=models.CASCADE,
        verbose_name="Product Name",
    )

    def slug_gen(obj):
        product = obj.product_model_type.name
        factory = obj.product_model_type.factory.name
        return f"{product}-{factory}"

    slug = AutoSlugField(
        "opt ref addr", unique=True, always_update=False, 
        # # This is the django-extension parameters 
        # populate_from=[
        #     'product_model_type__name',
        #     'product_model_type__factory__name'
        # ]
        populate_from=slug_gen
    )

    lc = models.ForeignKey(
        "materials.LiquidCrystal",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="LC",
    )
    pi = models.ForeignKey(
        "materials.Polyimide",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="PI",
    )
    seal = models.ForeignKey(
        "materials.Seal",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Seal",
    )

    cell_gap = models.FloatField("Cell Gap(um)")
    voltage = models.FloatField(default=5.0)
    ito_slit = models.FloatField("ITO Slit(°)", null=True, blank=True)

    class TFTTech(models.TextChoices):
        AMORPHOUS = "a_Si", "a-Si"
        LTPS = "LTPS", "LTPS"

        __empty__ = "Unknown"

    tft_tech = models.CharField(
        "TFT Tech", choices=TFTTech.choices, max_length=20)
    transmittance = models.FloatField("T%")
    time_rise = models.FloatField("Tr(ms)")
    time_fall = models.FloatField("Tf(ms)")
    gray_to_gray = models.FloatField("G2G(ms)")
    w_x = models.FloatField("Wx")
    w_y = models.FloatField("Wy")
    contrast_ratio = models.FloatField("CR")

    @property
    def response_time(self):
        return self.time_fall + self.time_rise

    def __str__(self):
        return (
            self.product_model_type.name 
            + "@" + self.product_model_type.factory.name
            # + " Vop:" + self.voltage
        )

    def get_absolute_url(self):
        return reverse("opticals:ref_detail", kwargs={"slug": self.slug})


class ValidManager(models.Manager):
    def valided(self, **kwargs):
        return self.filter(is_valid=True, **kwargs)


class OpticalsFittingModel(TimeStampedModel):
    # TODO: to be deprecated
    experiment = models.ForeignKey(
        "products.Experiment", on_delete=models.CASCADE)
    lc = models.ForeignKey("materials.LiquidCrystal", on_delete=models.CASCADE)
    # Origin data ranges
    cell_gap_upper = models.FloatField()
    cell_gap_lower = models.FloatField()
    
    # Fitting models
    # RTs
    voltage = PickledObjectField()
    response_time = PickledObjectField()
    time_rise = PickledObjectField()
    time_fall = PickledObjectField()
    # OPTs
    w_x = PickledObjectField()
    w_y = PickledObjectField()
    w_capital_y = PickledObjectField()
    lc_percent = PickledObjectField()
    transmittance = PickledObjectField()
    v_percent = PickledObjectField()
    # collect all r2
    r2 = models.JSONField()

    # Custom model manager
    objects = ValidManager()

    # valid system
    is_valid = models.BooleanField(default=False)

    def valid(self):
        self.is_valid = True
        self.save()

    def invalid(self):
        self.is_valid = False
        self.save()

    def __str__(self):
        return f"fitting model of {self.lc.name} @ {self.experiment.name}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["experiment", "lc"], name="opticals_scipy_model"
            )
        ]

class OptFittingModel(TimeStampedModel):
    experiment = models.ForeignKey(
        'products.Experiment',
        on_delete=models.CASCADE,
    )
    # Configurations
    lc = models.ForeignKey(
        'materials.LiquidCrystal', 
        on_delete=models.CASCADE
    )
    pi = models.ForeignKey(
        'materials.Polyimide',
        on_delete=models.CASCADE
    )
    seal = models.ForeignKey(
        'materials.Seal',
        on_delete=models.CASCADE
    )
    
    def slug_gen(obj):
        exp = obj.experiment.name
        lc = obj.lc.name.replace('-','')
        pi = obj.pi.name.replace('-','')
        seal = obj.seal.name.replace('-','')
        return f'{lc}-{pi}-{seal}-{exp}'    
    
    slug = AutoSlugField(
        unique=True, always_update=False,
        populate_from=slug_gen
    )
    
    # Origin data ranges
    cell_gap_upper = models.FloatField()
    cell_gap_lower = models.FloatField()
    
    # Fitting models
    # OPTs
    w_x = PickledObjectField()
    w_y = PickledObjectField()
    w_capital_y = PickledObjectField()
    lc_percent = PickledObjectField()
    transmittance = PickledObjectField()
    v_percent = PickledObjectField()
    # collect all r2
    r2 = models.JSONField()
    
    def __str__(self):
        return f"opt fitting model of {self.slug}"

class RTFittingModel(TimeStampedModel):
    experiment = models.ForeignKey(
        'products.Experiment',
        on_delete=models.CASCADE,
    )
    # Configurations
    lc = models.ForeignKey(
        'materials.LiquidCrystal', 
        on_delete=models.CASCADE
    )
    pi = models.ForeignKey(
        'materials.Polyimide',
        on_delete=models.CASCADE
    )
    seal = models.ForeignKey(
        'materials.Seal',
        on_delete=models.CASCADE
    )
    
    def slug_gen(obj):
        exp = obj.experiment.name
        lc = obj.lc.name.replace('-','')
        pi = obj.pi.name.replace('-','')
        seal = obj.seal.name.replace('-','')
        return f'{lc}-{pi}-{seal}-{exp}'    
    
    slug = AutoSlugField(
        unique=True, always_update=False,
        populate_from=slug_gen
    )
    
    # Origin data ranges
    cell_gap_upper = models.FloatField()
    cell_gap_lower = models.FloatField()
    
    # Fitting models
    # RTs
    voltage = PickledObjectField()
    response_time = PickledObjectField()
    time_rise = PickledObjectField()
    time_fall = PickledObjectField()
    # collect all r2
    r2 = models.JSONField()
    
    def __str__(self):
        return f"rt fitting model of {self.slug}" 

class OpticalSearchProfile(TimeStampedModel):
    name = models.CharField('Profile Name', max_length=255, default='Default')
    slug = AutoSlugField(
        'Optical Search Profile Address', unique=True, always_update=False,
        populate_from='name'
    )
    ref_product = models.ForeignKey(
        OpticalReference, 
        verbose_name='Ref Product',
        on_delete=models.CASCADE
    )

    lc_percent = models.FloatField('LC% minimum', default=0.)
    lc_percent_weight = models.FloatField('LC% Weight', default=1.)
    response_time = models.FloatField('RT maximum', default=100.)
    response_time_weight = models.FloatField('RT Weight', default=1.)
    delta_e_ab = models.FloatField('ΔEab* minimum', default=100.)
    delta_e_ab_weight = models.FloatField('ΔEab* Weight', default=1.)
    contrast_ratio = models.FloatField('CR minimum', default=0.)
    contrast_ratio_weight = models.FloatField('CR Weight', default=1.)
    class RemarkChoice(models.TextChoices):
        ALL = 'All', 'All'
        INTER = 'Interpolation', 'Interpolation'
        EXTRA = 'Extrapolation', 'Extrapolation'

    remark = models.TextField(
        choices=RemarkChoice.choices, max_length=20, default=RemarkChoice.INTER)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(
            "opticals:search_profile_detail", kwargs={"slug": self.slug})
        
class BackLightUnit(TimeStampedModel):
    name = models.CharField('Name', max_length=255, default='Default')
    slug = AutoSlugField(
        'Back Light Unit Address', unique=True, always_update=False,
        populate_from='name'
    )
    
    def __str__(self):
        return self.name
    
class OpticalWaveBase(TimeStampedModel):
    wavelength = models.FloatField('Wavelength(nm)')
    value = models.FloatField('Value')
    
    class Meta:
        abstract = True
        
class BackLightIntensity(OpticalWaveBase):
    blu = models.ForeignKey(
        BackLightUnit,
        on_delete=models.CASCADE,
        related_name='back_light_intensity'
    )
    
    