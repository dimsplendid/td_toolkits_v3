from django.urls import path
from . import views


app_name = "materials"
urlpatterns = [
    path(
        route='lc/list/',
        view=views.LiquidCrystalListView.as_view(),
        name='lc_list'
    ),
    path(
        route='lc/add/',
        view=views.LiquidCrystalCreateView.as_view(),
        name='lc_add'
    ),
    path(
        route='lc/<slug:slug>/',
        view=views.LiquidCrystalDetailView.as_view(),
        name='lc_detail'
    ),
    path(
        route='vender/list',
        view=views.VenderListView.as_view(),
        name='vender_list'
    ),
    path(
        route='upload/',
        view=views.MaterialsBatchCreateView.as_view(),
        name='upload'
    )
]
