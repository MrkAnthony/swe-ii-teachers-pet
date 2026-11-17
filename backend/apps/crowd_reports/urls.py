from django.urls import path

from . import views

app_name = "crowd_reports"

urlpatterns = [
    path("", views.CrowdReportCreateView.as_view(), name="create"),
    path("status/<uuid:location_id>/", views.LocationCrowdStatusView.as_view(), name="status"),
]
