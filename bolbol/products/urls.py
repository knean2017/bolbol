from django.urls import path

from .views import CityAPIView, ProductDetailAPIView, ProductListAPIView, UserProductsAPIView


urlpatterns = [
    path("cities/", CityAPIView.as_view(), name="cities"),
    path("products/", ProductListAPIView.as_view(), name="products"),
    path("products/<int:prod_id>", ProductDetailAPIView.as_view(), name="product-detail"),
    path("users/profile/products/", UserProductsAPIView.as_view(), name="user-products"),
    
]