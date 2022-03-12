from django.urls import path
from . import views

app_name = "opticals"
urlpatterns = [
    path(
        '',
        views.IndexView.as_view(),
        name='index'
    ),
    # path(
    #     'upload/',
    #     views.OpticalsUploadView.as_view(),
    #     name='upload'
    # ),
    path(
        'axo/upload/',
        views.AxoUploadView.as_view(),
        name='axo_upload'
    ),
    path(
        'rdl/cell-gap/upload/',
        views.RDLCellGapUploadView.as_view(),
        name='rdl_cell_gap_upload'
    ),
    path(
        'toc/opt/upload/',
        views.OptUploadView.as_view(),
        name='toc_opt_log_upload'
    )
]