from django.urls import path

from .views import LocationDetailView, LocationFilterOptionsView, LocationListView

app_name = "locations"

urlpatterns = [
    path("locations/", LocationListView.as_view(), name="location-list"),
    path("locations/filters/", LocationFilterOptionsView.as_view(), name="location-filters"),
    path("locations/<uuid:pk>/", LocationDetailView.as_view(), name="location-detail"),
]