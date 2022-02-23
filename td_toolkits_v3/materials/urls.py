from django.urls import path
from . import views


app_name = "materials"
urlpatterns = [
    path(
        route='',
        view=views.LiquidCrystalListView.as_view(),
        name='lc_list'
    ),
    path(
        route='venders/',
        view=views.VenderListView.as_view(),
        name='vender_list'
    ),
]
