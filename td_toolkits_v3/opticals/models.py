from django.db import models

from autoslug import AutoSlugField
from model_utils.models import TimeStampedModel


class Instrument(TimeStampedModel):
    name = models.CharField(
        'Instrument Name',
        max_length=255)
    slug = AutoSlugField(
        'Instrument Address',
        unique=True, always_update=False, populate_from='name')
    desc = models.TextField(
        'description', blank=True)
    factory = models.ForeignKey(
        'products.Factory',
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
        return f'{self.name} (@{self.factory.name})'


class AxometricsLog(TimeStampedModel):
    chip = models.ForeignKey('products.Chip', on_delete=models.CASCADE)
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
        Instrument, 
        on_delete=models.CASCADE,
        null=True, blank=True
    )

    def __str__(self):
        return f'{self.chip.name}, p {self.measure_point}' \
            + f', cell gap: {self.cell_gap}'

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['chip', 'measure_point'], name='axo_chip_measure_point'
            )
        ]



class RDLCellGap(TimeStampedModel):
    # One to One relation can not duplicate.
    chip = models.OneToOneField(
        'products.Chip', 
        on_delete=models.CASCADE,
        related_name='rdl_cell_gap'
    )
    cell_gap = models.FloatField()
    instrument = models.ForeignKey(
        Instrument, 
        on_delete=models.CASCADE,
        null=True, blank=True
    )
    
    def __str__(self):
        return self.chip.name


class OpticalLog(TimeStampedModel):
    chip = models.ForeignKey('products.Chip', on_delete=models.CASCADE)
    measure_point = models.SmallIntegerField()
    measure_time = models.DateTimeField()
    instrument = models.ForeignKey(
        Instrument,
        on_delete=models.CASCADE,
        null=True, blank=True
    )
    operator = models.CharField(max_length=255)
    voltage = models.FloatField('Vop')
    lc_percent = models.FloatField()
    w_x = models.FloatField()
    w_y = models.FloatField()

    @property
    def t_percent(self):
        max_lc_percent = max(self.objects.filter(
            chip=self.chip,
            measure_point=self.measure_point
        ).values_list('lc_percent'))[0]
        return self.lc_percent / max_lc_percent * 100

    def __str__(self):
        return f'{self.chip.name}, p {self.measure_point} ' \
            + f'v: {self.voltage}, ({self.lc_percent}, {self.w_x}, {self.w_y})'


    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['chip', 'measure_point', 'voltage'], 
                name='opt_unique'
            )
        ]

class ResponseTimeLog(TimeStampedModel):
    chip = models.ForeignKey('products.Chip', on_delete=models.CASCADE)
    measure_point = models.SmallIntegerField()
    measure_time = models.DateTimeField()
    instrument = models.ForeignKey(
        Instrument,
        on_delete=models.CASCADE,
        null=True, blank=True
    )
    operator = models.CharField(max_length=255)
    voltage = models.FloatField('Vop')
    time_rise = models.FloatField()
    time_fall = models.FloatField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['chip', 'measure_point', 'voltage'], 
                name='rt_unique'
            )
        ]

class OpticalReference(TimeStampedModel):
    """
    Cause **Reference** should be mass product.
    There would be only one optical reference for each product model type.
    """
    product_model_type = models.OneToOneField(
        'products.ProductModelType', on_delete=models.CASCADE,
        verbose_name='Product Name',
        )
    
    lc = models.ForeignKey(
        "materials.LiquidCrystal", 
        on_delete=models.CASCADE, null=True, blank=True,
        verbose_name='LC'
    )
    pi = models.ForeignKey(
        "materials.Polyimide", 
        on_delete=models.CASCADE, null=True, blank=True,
        verbose_name='PI'
    )
    seal = models.ForeignKey(
        "materials.Seal", 
        on_delete=models.CASCADE, null=True, blank=True,
        verbose_name='Seal'
    )

    cell_gap = models.FloatField('Cell Gap')
    ito_slit = models.FloatField(
        'ITO Slit', null=True, blank=True)

    class TFTTech(models.TextChoices):
        AMORPHOUS = 'a_Si', 'a-Si'
        LTPS = 'LTPS', 'LTPS'

        __empty__ = 'Unknown'

    tft_tech = models.CharField(
        'TFT Tech', choices=TFTTech.choices, max_length=20)

    def __str__(self):
        return self.product_model_type.name + '@'\
                + self.product_model_type.factory.name
    
    def get_absolute_url(self):
        return 