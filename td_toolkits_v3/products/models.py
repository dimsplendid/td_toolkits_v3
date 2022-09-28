from django.db import models

from autoslug import AutoSlugField
from model_utils.models import TimeStampedModel


class ProductModelType(TimeStampedModel):
    name = models.CharField("short name", max_length=255)
    slug = AutoSlugField(
        "Product Address", unique=True, always_update=False, populate_from="name"
    )
    model_name = models.CharField(max_length=255, null=True, blank=True)
    factory = models.ForeignKey(
        "Factory",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    @classmethod
    def default(cls, name, factory):
        return cls.objects.get_or_create(name=name, factory=factory)[0]

    def __str__(self):
        return self.name

class ProductID(TimeStampedModel):
    name = models.CharField(max_length=255)
    model = models.ForeignKey(
        to=ProductModelType, 
        on_delete=models.CASCADE,
    )

class Project(TimeStampedModel):
    name = models.CharField(
        "Project name",
        max_length=255,
    )
    code = models.CharField("project code", max_length=255, blank=True)

    def __str__(self):
        return self.name


class Factory(TimeStampedModel):
    name = models.CharField(
        "Factory Name",
        max_length=255,
    )
    slug = AutoSlugField(
        "Factory Address", unique=True, always_update=False, populate_from="name"
    )
    addr = models.CharField(
        "Factory Address(Physics)",
        max_length=255,
        blank=True,
    )
    desc = models.TextField("description", blank=True)
    ra_name = models.CharField(
        verbose_name='RAS Fab Name',
        blank=True,
        null=True,
    )

    @classmethod
    def default(cls, name):
        return cls.objects.get_or_create(name=name)[0]

    def __str__(self):
        return self.name


class Experiment(TimeStampedModel):
    name = models.CharField(
        "Experiment ID",
        max_length=255,
        unique=True,
    )
    slug = AutoSlugField(
        "Experiment Address", unique=True, always_update=False, populate_from="name"
    )
    desc = models.TextField("description", blank=True)
    product_type = models.ForeignKey(
        "ProductModelType", on_delete=models.CASCADE, null=True, blank=True
    )
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.name


class Condition(TimeStampedModel):
    name = models.CharField(
        "Conditions",
        max_length=255,
    )
    slug = AutoSlugField(
        "Condtions Address", unique=True, always_update=False, populate_from="name"
    )
    desc = models.TextField("description", blank=True)
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE)

    # TODO: experiment conditions

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["name", "experiment"], name="unique_condition"
            )
        ]

    def __str__(self):
        return self.name


class Sub(TimeStampedModel):
    name = models.CharField(
        "sub id",
        max_length=255,
        help_text="If you don't have ID like some simple test cell, using \
            project_name",
    )
    slug = AutoSlugField(
        "Sub Address", unique=True, always_update=False, populate_from="name"
    )

    condition = models.ForeignKey(
        "Condition", on_delete=models.CASCADE, null=True, blank=True
    )

    def __str__(self):
        return self.name


class Chip(TimeStampedModel):
    name = models.CharField(
        "chip id",
        max_length=255,
        help_text="If you don't have ID like some simple test cell, using \
            project_name + your spcific id",
    )
    slug = AutoSlugField(
        "Sub Address", unique=True, always_update=False, populate_from="name"
    )
    short_name = models.CharField("short id", max_length=255, blank=True)
    sub = models.ForeignKey("Sub", on_delete=models.CASCADE, null=True, blank=True)
    condition = models.ForeignKey(
        'Condition', on_delete=models.CASCADE, null=True, blank=True)

    lc = models.ForeignKey(
        "materials.LiquidCrystal", on_delete=models.CASCADE, null=True, blank=True
    )
    pi = models.ForeignKey(
        "materials.Polyimide", on_delete=models.CASCADE, null=True, blank=True
    )
    seal = models.ForeignKey(
        "materials.Seal", on_delete=models.CASCADE, null=True, blank=True
    )

    def __str__(self):
        return self.name
