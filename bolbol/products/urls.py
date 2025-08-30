from django.urls import path

from .views import CityAPIView


urlpatterns = [
    path("cities/", CityAPIView.as_view(), name="cities"),
    
]