from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.cache import cache

from .models import Category, SubCategory, Attribute, City, Product, ProductDetail
from .serializers import (CategorySerializer, SubCategorySerializer, AttributeSerializer, 
                          CitySerializer, ProductSerializer, ProductDetailSerializer)


class CityAPIView(APIView):
    def get(self, request):
        cities = cache.get("cities")

        if not cities:
            queryset = City.objects.all()
            serializer = CitySerializer(queryset, many=True)
            cities = serializer.data
            cache.set("cities", cities, timeout=None)
        
        return Response(cities)


# class ProductAPIView(APIView):
#     ...
