from rest_framework import serializers
from ..models import Product, ProductDetail


class ProductDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductDetail
        fields = ["attribute", "value"]

        
class ProductSerializer(serializers.ModelSerializer):
    product_details = ProductDetailSerializer(many=True, required=False)

    class Meta:
        model = Product
        fields = "__all__"


    def create(self, validated_data):
        details_data = validated_data.pop("product_details", [])
        print(details_data)
        
        product = Product.objects.create(**validated_data)
        
        for detail in details_data:
            print(detail)
            ProductDetail.objects.create(product=product, **detail)
        
        return product

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["product_details"] = ProductDetailSerializer(instance.productdetail_set.all(), many=True).data
        return rep


