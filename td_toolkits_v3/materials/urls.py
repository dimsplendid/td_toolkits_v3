from django.urls import path
from . import views


app_name = "materials"
urlpatterns = [
    path(
        route='lcs/',
        view=views.LiquidCrystalListView.as_view(),
        name='lc_list'
    ),
    path(
        route='lcs/add/',
        view=views.LiquidCrystalCreateView.as_view(),
        name='lc_add'
    ),
    path(
        route='lcs/<slug:slug>/',
        view=views.LiquidCrystalDetailView.as_view(),
        name='lc_detail'
    ),
    path(
        route='venders/',
        view=views.VenderListView.as_view(),
        name='vender_list'
    ),
    path(
        route='upload/',
        view=views.MaterialsBatchCreateView.as_view(),
        name='upload'
    )
]
