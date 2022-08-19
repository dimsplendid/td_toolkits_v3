from django.urls import path
from . import views


app_name = "products"
urlpatterns = [
    path(
        route='chip/list/',
        view=views.ChipListView.as_view(),
        name='chip_list'
    ),
    path(
        route='chip/upload/',
        view=views.ChipsBatchCreateView.as_view(),
        name='chip_upload'
    ),
    path(
        'chip/upload/success/',
        views.ChipBatchCreateSuccessView.as_view(),
        name='chip_upload_success',
    ),
]