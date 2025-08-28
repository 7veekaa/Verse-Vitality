from rest_framework import serializers
from .models import (
    Category, Tag, Collection, Product, ProductMedia, ProductVariant, Review, Discount
)

class TagSerializer(serializers.ModelSerializer):
    class Meta: model = Tag; fields = ("id","name","slug")

class CategoryMiniSerializer(serializers.ModelSerializer):
    class Meta: model = Category; fields = ("id","name","slug")

class MediaSerializer(serializers.ModelSerializer):
    class Meta: model = ProductMedia; fields = ("url","kind","alt","sort_order")

class VariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ("id","sku","barcode","options","price","stock_qty","is_default","active")

class DiscountMiniSerializer(serializers.ModelSerializer):
    class Meta: model = Discount; fields = ("name","code","percentage","amount")

class ProductListSerializer(serializers.ModelSerializer):
    category = CategoryMiniSerializer()
    tags = TagSerializer(many=True)
    media = MediaSerializer(many=True)
    price = serializers.DecimalField(source="base_price", max_digits=10, decimal_places=2, read_only=True)
    discounts = DiscountMiniSerializer(many=True)
    class Meta:
        model = Product
        fields = ("id","title","slug","subtitle","badge","rating_avg","rating_count",
                  "price","compare_at_price","category","tags","media","discounts")

class ProductDetailSerializer(ProductListSerializer):
    variants = VariantSerializer(many=True)
    class Meta(ProductListSerializer.Meta):
        fields = ProductListSerializer.Meta.fields + (
            "description","attributes_json","seo_title","seo_description","variants","collections",
        )

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ("id","user_name","rating","title","body","created_at")
