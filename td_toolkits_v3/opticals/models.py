from django.db import models

from model_utils.models import TimeStampedModel


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

class RDLCellGap(TimeStampedModel):
    chip = models.OneToOneField(
        'products.Chip', 
        on_delete=models.CASCADE,
        related_name='rdl_cell_gap'
    )
    cell_gap = models.FloatField()

class 