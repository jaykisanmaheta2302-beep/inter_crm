from django.urls import path
from .views import voice_to_json
from .views import dashboard_results
from .views import *



urlpatterns = [
    path("extract/", voice_to_json),
    path("dashboard/", dashboard_results),
]
