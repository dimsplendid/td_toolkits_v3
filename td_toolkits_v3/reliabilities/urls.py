from django.urls import path
from . import views


app_name = "reliabilities"
urlpatterns = [
    path('', view=views.IndexView.as_view(), name='index'),
    path(
        'upload/',
        view=views.ReliabilitiesUploadView.as_view(),
        name='upload',
    ),
    path(
        'search/',
        view=views.ReliabilitySearchView.as_view(),
        name='search',
    ),
    path(
        'search/download/',
        view=views.ReliabilitySearchResultDownload.as_view(),
        name='search_download'
    )
    ,
    path(
        'search/profile/list/',
        views.ReliabilitySearchProfileListView.as_view(),
        name='search_profile_list',
    ),
    path(
        'search/profile/add/',
        views.ReliabilitySearchProfileCreateView.as_view(),
        name='search_profile_add',
    ),
    path(
        'search/profile/<slug:slug>/',
        views.ReliabilitySearchProfileDetailView.as_view(),
        name='search_profile_detail',
    ),
    path(
        'search/profile/<slug:slug>/update/',
        views.ReliabilitySearchProfileUpdateView.as_view(),
        name='search_profile_update',
    ),
    path(
        'search/profile/<slug:slug>/copy/',
        views.ReliabilitySearchProfileCopyView.as_view(),
        name='search_profile_copy',
    ),
    path(
        'ushape/',
        views.UShapeView.as_view(),
        name='ushape',
    ),
    path(
        'tr2/',
        views.ReliabilityPhaseTwoView.as_view(),
        name='tr2'
    ),
    path(
        'tr2/success/',
        views.ReliabilityPhaseTwoSuccessView.as_view(),
        name='tr2_result'
    )
]