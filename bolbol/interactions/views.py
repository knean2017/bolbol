from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import Bookmark, Comment
from .serializers import BookmarkSerializer, CommentSerializer
from products.models import Product


class BookmarkAPIView(APIView):
    authentication_classes = [JWTAuthentication]

    def get(self, request):
       bookmarks = Bookmark.objects.filter(user=request.user)
       serializer = BookmarkSerializer(bookmarks, many=True)
       return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        serializer = BookmarkSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(product=product)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class CommentAPIView(APIView):
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [AllowAny()]
    
    def get(self, request, product_id):
        comments = Comment.objects.filter(product_id=product_id)
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(request_body=CommentSerializer)
    def post(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user, product=product)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
