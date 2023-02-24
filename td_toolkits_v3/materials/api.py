from typing import List
from ninja import NinjaAPI, ModelSchema
from django.http import HttpRequest
from .models import LiquidCrystal

api = NinjaAPI()

@api.get("/add")
def add(request: HttpRequest, a: int, b: int):
    return {"result": a + b}

class LiquidCrystalSchema(ModelSchema):
    class Config:   # type: ignore
        model = LiquidCrystal
        model_fields = "__all__"
        
@api.get("/lc/list", response=List[LiquidCrystalSchema])
def lc_list(request: HttpRequest):
    return LiquidCrystal.objects.all()

@api.get("lc/{name}", response=LiquidCrystalSchema)
def lc_detail(request: HttpRequest, name: str):
    return LiquidCrystal.objects.get(name=name)