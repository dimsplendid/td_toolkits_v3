from autoslug import AutoSlugField
from django.db import models
from django.db.models.fields.related import ForeignKey
from model_utils.models import TimeStampedModel


class File(TimeStampedModel):
    name = models.CharField(max_length=255, unique=True,
                            help_text='Input file name')

    def __str__(self):
        return self.name


class Configuration(models.Model):
    lc = ForeignKey(
        'materials.LiquidCrystal', 
        on_delete=models.CASCADE, null=True, blank=True)
    pi = ForeignKey(
        'materials.Polyimide', on_delete=models.CASCADE, null=True, blank=True)
    seal = ForeignKey(
        'materials.Seal', on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        abstract = True


class VoltageHoldingRatio(Configuration, TimeStampedModel):
    name = 'VHR(heat)'

    class UVAging(models.TextChoices):
        BEFORE_UV = 'Before UV'
        AFTER_UV = 'After UV'

    uv_aging = models.CharField(
        max_length=10,
        choices=UVAging.choices,
        default=UVAging.BEFORE_UV
    )

    measure_voltage = models.FloatField(default=1.)
    measure_freq = models.FloatField(default=0.6)
    measure_temperature = models.FloatField(default=60)
    value = models.FloatField(default=0.)

    unit = '%'
    vender = ForeignKey('materials.Vender', on_delete=models.CASCADE)
    file_source = ForeignKey(File, on_delete=models.CASCADE)

    @property
    def cond(self):
        return self.uv_aging + ', V: ' + str(self.measure_voltage) \
            + ' volt, freq: ' + str(self.measure_freq) + ' Hz, Temperature: '\
            + str(self.measure_temperature) + ' °C'

    @property
    def value_remark(self):
        return ''


class DeltaAngle(Configuration, TimeStampedModel):
    name = 'Δ angle'
    measure_voltage = models.FloatField(default=14.0)
    measure_freq = models.FloatField(default=60.0)
    measure_time = models.FloatField(default=72.0)
    measure_temperature = models.FloatField(default=60.0, null=True, blank=True)
    value = models.FloatField(default=0.)
    vender = ForeignKey('materials.Vender', on_delete=models.CASCADE, null=True)
    unit = '°'
    file_source = ForeignKey(File, on_delete=models.CASCADE)

    @property
    def cond(self):
        return str(self.measure_time) + ' hr, Vp-p: ' \
                + str(self.measure_voltage) + ' volt, freq: ' \
                + str(self.measure_freq) + ' Hz, Temperature: ' \
                + str(self.measure_temperature) + ' °C'
    
    @property
    def value_remark(self):
        return ''


class Adhesion(Configuration, TimeStampedModel):
    name = 'Adhesion test'
    
    adhesion_interface = models.CharField(
        max_length=255, help_text='enter condition')
    method = models.CharField(max_length=255)

    value = models.FloatField(default=0.)
    unit = 'kgw'

    peeling = models.CharField(
        max_length=40, help_text="Enter peeling interface.", blank=True, null=True)
    vender = ForeignKey('materials.Vender', on_delete=models.CASCADE)
    file_source = ForeignKey(File, on_delete=models.CASCADE)

    @property
    def cond(self):
        return 'Adhesion介面(T/C): ' + str(self.adhesion_interface) + '測試手法' + str(self.method)

    @property
    def value_remark(self):
        return 'Peeling surface: ' + str(self.peeling)


class LowTemperatureStorage(Configuration, TimeStampedModel):
    name = 'LTS'

    storage_condition = models.CharField(
        max_length=10,
        choices=(
            ('Bulk', 'Bulk'),
            ('Test Cell', 'Test Cell')
        )
    )

    slv_condition = models.FloatField(default=1.)
    jar_test_seal = ForeignKey(
        'materials.Seal', 
        on_delete=models.SET_NULL, 
        null=True, blank=True, related_name='lts_jar_test_seals')
    measure_temperature = models.FloatField(default=-30.)

    value = models.FloatField(default=0.)
    unit = 'days'
    vender = ForeignKey('materials.Vender', on_delete=models.CASCADE)

    file_source = ForeignKey(File, on_delete=models.CASCADE)

    @property
    def cond(self):
        return str(self.measure_temperature) + ' °C, Storage: ' \
            + self.storage_condition + ', SLV%: ' \
            + str(self.slv_condition * 100.) + '% , Jar test seal: ' \
            + str(self.jar_test_seal)

    @property
    def value_remark(self):
        return ''


class LowTemperatureOperation(Configuration, TimeStampedModel):
    name = 'LTO'
    
    storage_condition = models.CharField(
        max_length=10,
        default='Test Cell',
    )

    slv_condition = models.FloatField(default=1.)
    jar_test_seal = ForeignKey(
        'materials.Seal', 
        on_delete=models.SET_NULL, 
        null=True, blank=True, related_name='lto_jar_test_seals')
    measure_temperature = models.FloatField(default=-30.)

    class Value(models.IntegerChoices):
        NA = -1, "N.A."
        NG = 0, "NG"
        PASS = 1, "Pass"

    value_mapping = {i.label: i.value for i in Value}
    value = models.IntegerField(
        choices=Value.choices,
        default=Value.PASS
    )
    unit = ''
    vender = ForeignKey(
        'materials.Vender', on_delete=models.CASCADE, null=True)

    file_source = ForeignKey(File, on_delete=models.CASCADE)

    @property
    def cond(self):
        return str(self.measure_temperature) + ' °C, Storage: ' \
            + str(self.storage_condition) + ', SLV%: ' \
            + str(self.slv_condition * 100) + '% , Jar test seal: ' \
            + self.jar_test_seal.name

    @property
    def value_remark(self):
        return ''


class PressureCookingTest(Configuration, TimeStampedModel):
    name = 'PCT'
    value = models.FloatField(default=0.)
    unit = 'hours'
    measure_condition = models.CharField(
        max_length=255,
        help_text="measure condition"
    )
    test_vehical = models.CharField(
        max_length=255,
        help_text='test vehicle'
    )
    vender = ForeignKey('materials.Vender', on_delete=models.CASCADE, null=True)
    file_source = ForeignKey(File, on_delete=models.CASCADE)

    @property
    def cond(self):
        return "measure conditions: " + str(self.measure_condition) \
            + ", test vehicle: " + str(self.test_vehical)

    @property
    def value_remark(self):
        return ''


class SealWVTR(Configuration, TimeStampedModel):
    name = 'Seal WVTR'
    value = models.FloatField(default=0.)
    unit = ''
    temperature = models.FloatField(default=0)
    humidity = models.FloatField(default=0)
    thickness = models.FloatField(default=0)

    vender = ForeignKey(
        'materials.Vender', on_delete=models.CASCADE, null=True)
    file_source = ForeignKey(File, on_delete=models.CASCADE)

    @property
    def cond(self):
        return "temperature: " + str(self.temperature) \
             + "°C, humidity: " + str(self.humidity) \
             + "%, thickness: " + str(self.thickness) + " um."

    @property
    def value_remark(self):
        return ''

class UShapeAC(Configuration, TimeStampedModel):
    name = 'U-shape AC%'
    unit = ''
    value = models.FloatField()
    time = models.FloatField()
    temperature = models.FloatField()
    vender = ForeignKey(
        'materials.Vender', on_delete=models.CASCADE, null=True)
    file_source = ForeignKey(File, on_delete=models.CASCADE)

    @property
    def cond(self):
        return f'time: {self.time}, temp: {self.temperature}'

    @property
    def value_remark(self):
        return ''


class ReliabilitySearchProfile(TimeStampedModel):
    name = models.CharField('Profile Name', max_length=255, default='Default')
    slug = AutoSlugField(
        'Reliability Search Profile Address', unique=True, always_update=False,
        populate_from='name'
    )

    voltage_holding_ratio = models.FloatField(default=0.)
    voltage_holding_ratio_venders = models.ManyToManyField(
        'materials.vender', 
        verbose_name='VHR Venders',
        related_name='voltage_holding_ratio_venders'
    )
    voltage_holding_ratio_weight = models.FloatField('VHR Weight', default=1.)

    delta_angle = models.FloatField('Δ angle', default=90.)
    delta_angle_venders = models.ManyToManyField(
        'materials.vender', 
        verbose_name='Δ angle Venders',
        related_name='delta_angle_venders'
    )
    delta_angle_weight = models.FloatField('Δ angle Weight', default=1.)

    adhesion = models.FloatField('Adhesion', default=0.)
    adhesion_venders = models.ManyToManyField(
        'materials.vender', 
        verbose_name='Adhesion Venders',
        related_name='adhesion_venders'
    )
    adhesion_weight = models.FloatField('Adhesion Weight', default=1.)

    low_temperature_storage = models.FloatField('LTS', default=0.)
    low_temperature_storage_venders = models.ManyToManyField(
        'materials.vender', 
        verbose_name='LTS Venders',
        related_name='low_temperature_storage_venders'
    )
    low_temperature_storage_weight = models.FloatField('LTS Weight', default=1.)

    
    pressure_cooking_test = models.FloatField('PCT', default=0.)
    pressure_cooking_test_venders = models.ManyToManyField(
        'materials.vender', 
        verbose_name='PCT Venders',
        related_name='pressure_cooking_test_venders'
    )
    pressure_cooking_test_weight = models.FloatField('PCT Weight', default=0.)

    seal_wvtr = models.FloatField('Seal WVTR', default=0.)
    seal_wvtr_venders = models.ManyToManyField(
        'materials.vender', 
        verbose_name='Seal WVTR Venders',
        related_name='seal_wvtr_venders'
    )
    seal_wvtr_weight = models.FloatField('Seal WVTR Weight', default=0.)

    u_shape_ac = models.FloatField('U-Shape AC%', default=0.)
    u_shape_ac_venders = models.ManyToManyField(
        'materials.vender', 
        verbose_name='U-Shape AC% Venders',
        related_name='u_shape_ac_venders'
    )
    u_shape_ac_weight = models.FloatField('U-Shape AC% Weight', default=0.)

    def __str__(self):
        return self.name