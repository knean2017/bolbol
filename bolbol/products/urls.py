from django.urls import path

from .views import CityAPIView, ProductDetailAPIView


urlpatterns = [
    path("cities/", CityAPIView.as_view(), name="cities"),
    path("products/<int:prod_id>", ProductDetailAPIView.as_view(), name="product-detail")
    
]