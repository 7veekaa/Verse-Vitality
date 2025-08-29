from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .models import Cart, CartItem, ProductVariant, perform_checkout, IdempotencyKey, Order
from .serializers import CartSerializer, CartItemAddSerializer, CheckoutSerializer, CartItemSerializer

@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def cart_create(request):
    cart = Cart.objects.create(owner=request.user)
    return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)

@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def cart_detail(request, cart_id):
    cart = get_object_or_404(Cart, id=cart_id, owner=request.user)
    return Response(CartSerializer(cart).data)

@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def cart_add_item(request, cart_id):
    cart = get_object_or_404(Cart, id=cart_id, owner=request.user)
    if not cart.is_active:
        return Response({"detail": "Cart already checked out."}, status=400)

    ser = CartItemAddSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    variant_id = ser.validated_data["variant_id"]
    qty = ser.validated_data["qty"]

    variant = get_object_or_404(ProductVariant, id=variant_id)
    item, created = CartItem.objects.get_or_create(
        cart=cart, variant=variant, defaults={"qty": qty, "unit_price": variant.price}
    )
    if not created:
        item.qty += qty
        item.save(update_fields=["qty"])
    return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)

@api_view(["PATCH"])
@permission_classes([permissions.IsAuthenticated])
def cart_update_item(request, cart_id, item_id):
    cart = get_object_or_404(Cart, id=cart_id, owner=request.user)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    ser = CartItemSerializer(item, data=request.data, partial=True)
    ser.is_valid(raise_exception=True)
    ser.save()
    return Response(CartSerializer(cart).data)

@api_view(["DELETE"])
@permission_classes([permissions.IsAuthenticated])
def cart_remove_item(request, cart_id, item_id):
    cart = get_object_or_404(Cart, id=cart_id, owner=request.user)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    item.delete()
    return Response(CartSerializer(cart).data)

@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def checkout(request):
    idem = request.headers.get("Idempotency-Key") or None
    ser = CheckoutSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    cart = get_object_or_404(Cart, id=ser.validated_data["cart_id"], owner=request.user)

    if idem:
        existing = IdempotencyKey.objects.filter(key=idem).select_related("order").first()
        if existing:
            return Response({"order_id": str(existing.order.id), "total": str(existing.order.total)}, status=200)

    try:
        with transaction.atomic():
            order = perform_checkout(cart=cart, buyer=request.user, idem_key=idem)
    except ValueError as e:
        return Response({"detail": str(e)}, status=400)

    return Response({"order_id": str(order.id), "total": str(order.total)}, status=201)
