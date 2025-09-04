from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication


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


class ProductAPIView(APIView):
    def get(self, request):
        products = Product.objects.filter(status="accepted")
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(request_body=ProductSerializer)
    def post(self,request):
        authentication_classes = [JWTAuthentication]
        permission_classes = [IsAuthenticated]

        data = request.data
        serializer = ProductSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductDetailAPIView(APIView):
    def get(self, request, prod_id):
        product = get_object_or_404(Product, id=prod_id)

        if product.status != "accepted":
            return Response({"error": "Product is not accepted"}, status=status.HTTP_400_BAD_REQUEST)
        product.increment_view()
        serializer = ProductSerializer(product)
        return Response({"data": serializer.data})
    