from typing import List, Dict, Optional

from django.db import models

from autoslug import AutoSlugField
from model_utils.models import TimeStampedModel
from enum import Enum

class ProductModelType(TimeStampedModel):
    name = models.CharField("short name", max_length=255)
    slug = AutoSlugField(
        "Product Address", unique=True, always_update=False, populate_from="name"
    ) # type: ignore
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


class Project(TimeStampedModel):
    name = models.CharField(
        "Project name",
        max_length=255,
    )
    code = models.CharField("project code", max_length=255, blank=True)
    # executor = models.ForeignKey(
    #     'users.User', 
    #     on_delete=models.CASCADE, 
    #     null=True, blank=True
    # )


    def __str__(self):
        return self.name
    
# class KanbanBase(TimeStampedModel):
#     title = models.CharField(max_length=255)
#     slug = AutoSlugField(
#         unique=True, always_update=False, populate_from="title"
#     )
    
#     def __str__(self):
#         return self.title
    
#     class Meta:
#         abstract = True

# class ProductPhase(models.TextChoices):
#     TR1 = "TR1"
#     TR2 = "TR2"
#     TR3 = "TR3"
#     TR3_5 = "TR3.5"

# class Board(KanbanBase):
#     product_phase = models.CharField(
#         choices=ProductPhase.choices, max_length=255, null=True, blank=True
#     )
#     project = models.ForeignKey(
#         Project, 
#         on_delete=models.CASCADE,
#         null=True,
#         blank=True,
#     )

# class Card(KanbanBase):
#     board = models.ForeignKey(Board, on_delete=models.CASCADE)
    
# class Group(KanbanBase):
#     board = models.ForeignKey(Board, on_delete=models.CASCADE)
    
# class Item(KanbanBase):
#     desc = models.TextField(blank=True)
#     internal_link = models.CharField(max_length=255, null=True, blank=True)
#     external_link = models.URLField(null=True, blank=True)
#     card = models.ForeignKey(Card, on_delete=models.CASCADE)
#     group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True)

# class KanbanTemplate(KanbanBase):
#     """store the template of kanban board
#     """
    

class Factory(TimeStampedModel):
    name = models.CharField(
        "Factory Name",
        max_length=255,
    )
    slug = AutoSlugField(
        "Factory Address", unique=True, always_update=False, populate_from="name"
    ) # type: ignore
    addr = models.CharField(
        "Factory Address(Physics)",
        max_length=255,
        blank=True,
    )
    desc = models.TextField("description", blank=True)

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
    ) # type: ignore
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
    ) # type: ignore
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
    ) # type: ignore

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
    ) # type: ignore
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
