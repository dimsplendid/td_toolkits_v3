from django.urls import path
from . import views

app_name = 'autofill'
urlpatterns = [
    path(
        '',
        views.Index.as_view(),
        name='index',
    ),
    path(
        'ras-test/',
        views.RealiabilitySystemTest.as_view(),
        name='ras-test'
    )
]