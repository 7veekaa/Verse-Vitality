import uuid
from decimal import Decimal
from django.conf import settings
from django.db import models, transaction
from django.utils import timezone

# Assumption: you have a catalog app with a ProductVariant model that has: id, price (Decimal), stock (int)
# If your model path differs, adjust the ForeignKey's app_label/model name below.
class ProductVariant(models.Model):
    class Meta:
        managed = False
        db_table = "catalog_productvariant"
    id = models.IntegerField(primary_key=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()

class Cart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="carts"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    checked_out_at = models.DateTimeField(null=True, blank=True)

    @property
    def is_active(self):
        return self.checked_out_at is None

    @property
    def subtotal(self) -> Decimal:
        total = Decimal("0.00")
        for item in self.items.all():
            total += item.unit_price * item.qty
        return total

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT)
    qty = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ("cart", "variant")

class Order(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.OneToOneField(Cart, on_delete=models.PROTECT, related_name="order")
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="orders"
    )
    total = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default="created")

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT)
    qty = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

class IdempotencyKey(models.Model):
    key = models.CharField(max_length=200, unique=True)
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="idempotency")
    created_at = models.DateTimeField(auto_now_add=True)

def perform_checkout(cart: Cart, buyer, idem_key: str | None = None) -> Order:
    if not cart.is_active:
        return cart.order

    with transaction.atomic():
        items = list(cart.items.select_related("variant"))
        if not items:
            raise ValueError("Cart is empty.")

        total = Decimal("0.00")
        # Lock variants for update (works when ProductVariant is real/managed with a DB table)
        variant_ids = [i.variant_id for i in items]
        locked_variants = (
            ProductVariant.objects.select_for_update()
            .filter(id__in=variant_ids)
        )
        vmap = {v.id: v for v in locked_variants}

        for it in items:
            v = vmap.get(it.variant_id)
            if v is None:
                raise ValueError(f"Variant {it.variant_id} not found.")
            if it.qty > v.stock:
                raise ValueError(f"Insufficient stock for variant {it.variant_id}.")
            total += it.unit_price * it.qty

        order = Order.objects.create(cart=cart, buyer=buyer, total=total, status="created")

        bulk_items = []
        for it in items:
            v = vmap[it.variant_id]
            v.stock -= it.qty
            bulk_items.append(OrderItem(order=order, variant_id=it.variant_id, qty=it.qty, unit_price=it.unit_price))
        OrderItem.objects.bulk_create(bulk_items)
        ProductVariant.objects.bulk_update(locked_variants, ["stock"])

        cart.checked_out_at = timezone.now()
        cart.save(update_fields=["checked_out_at"])

        if idem_key:
            IdempotencyKey.objects.create(key=idem_key, order=order)

        return order
