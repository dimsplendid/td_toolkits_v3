from django.urls import path
from . import views


app_name = "materials"
urlpatterns = [
    path('',
        view=views.IndexView.as_view(),
        name='index'
    ),
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
        route='lc/<slug:slug>/update/',
        view=views.LiquidCrystalUpdateView.as_view(),
        name='lc_update'
    ),
    path(
        route='vender/list',
        view=views.VenderListView.as_view(),
        name='vender_list'
    ),
    path(
        route='upload/',
        view=views.MaterialsUploadView.as_view(),
        name='upload'
    ),
    path(
        route='update/',
        view=views.MaterialsUpdateView.as_view(),
        name='update'
    )
    ,
    path(
        route='pi/list',
        view=views.PolyimideListView.as_view(),
        name='pi_list'
    ),
    path(
        route='seal/list',
        view=views.SealListView.as_view(),
        name='seal_list'
    ),
    path(
        'template/',
        views.TemplateDownloadView.as_view(),
        name='template'
    )
]
