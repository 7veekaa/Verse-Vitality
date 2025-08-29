from rest_framework import serializers
from .models import Cart, CartItem, Order, OrderItem

class CartItemAddSerializer(serializers.Serializer):
    variant_id = serializers.IntegerField()
    qty = serializers.IntegerField(min_value=1)

class CartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ["id", "variant", "qty", "unit_price"]

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Cart
        fields = ["id", "owner", "created_at", "checked_out_at", "is_active", "subtotal", "items"]
        read_only_fields = ["owner", "created_at", "checked_out_at", "is_active", "subtotal", "items"]

class CheckoutSerializer(serializers.Serializer):
    cart_id = serializers.UUIDField()
