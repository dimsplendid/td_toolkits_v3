from django.urls import path
from . import views


app_name = "reliabilities"
urlpatterns = [
    path('', view=views.IndexView.as_view(), name='index'),
    path(
        'upload/',
        view=views.ReliabilitiesUploadView.as_view(),
        name='upload',
    )
]