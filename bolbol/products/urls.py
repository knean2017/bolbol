from django.urls import path

from .views import CityAPIView, ProductDetailAPIView, ProductAPIView


urlpatterns = [
    path("cities/", CityAPIView.as_view(), name="cities"),
    path("products/", ProductAPIView.as_view(), name="products"),
    path("products/<int:prod_id>", ProductDetailAPIView.as_view(), name="product-detail")
    
]