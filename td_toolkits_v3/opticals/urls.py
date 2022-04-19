from django.urls import path
from . import views

app_name = "opticals"
urlpatterns = [
    path(
        '',
        views.IndexView.as_view(),
        name='index'
    ),
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
    ),
    path(
        'toc/rt/upload/',
        views.ResponseTimeUploadView.as_view(),
        name='toc_rt_log_upload'
    ),
    path(
        'ref/list/',
        views.OpticalReferenceListView.as_view(),
        name='ref_list'
    ),
    # path(
    #     'ref/add/',
    #     views.OpticalReferenceCreateView.as_view(),
    #     name='ref_add'
    # ),
    path(
        'ref/add/',
        views.ProductModelTypeCreateView.as_view(),
        name='ref_add'
    ),
    path(
        'ref/<slug:slug>/',
        views.OpticalReferenceDetailView.as_view(),
        name='ref_detail'
    ),
    path(
        'ref/<slug:slug>/update/',
        views.OpticalReferenceUpdateView.as_view(),
        name='ref_update'
    ),
    path(
        'calculate/',
        views.CalculateOpticalView.as_view(),
        name='calculate'
    ),
    path(
        'calculate/check/',
        views.CalculateCheckView.as_view(),
        name='calculate_check'
    ),
    path(
        'search/',
        views.OpticalSearchView.as_view(),
        name='search'
    ),
    path(
        'search/download/',
        views.OpticalSearchResultDownload.as_view(),
        name='search_download'
    ),
    path(
        'search/profile/list/',
        views.OpticalSearchProfileListView.as_view(),
        name='search_profile_list'
    ),
    path(
        'search/profile/add/',
        views.OpticalSearchProfileCreateView.as_view(),
        name='search_profile_add'
    ),
    path(
        'search/profile/<slug:slug>/',
        views.OpticalSearchProfileDetailView.as_view(),
        name='search_profile_detail'
    ),
    path(
        'search/profile/<slug:slug>/update/',
        views.OpticalSearchProfileUpdateView.as_view(),
        name='search_profile_update'
    ),
    path(
        'search/profile/<slug:slug>/copy/',
        views.OpticalSearchProfileCopyView.as_view(),
        name='search_profile_copy'
    ),
]