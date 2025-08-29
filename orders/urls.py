from django.urls import path
from . import views

urlpatterns = [
    path("cart/", views.cart_create, name="cart-create"),
    path("cart/<uuid:cart_id>/", views.cart_detail, name="cart-detail"),
    path("cart/<uuid:cart_id>/items/", views.cart_add_item, name="cart-add-item"),
    path("cart/<uuid:cart_id>/items/<int:item_id>/", views.cart_update_item, name="cart-update-item"),
    path("cart/<uuid:cart_id>/items/<int:item_id>/delete/", views.cart_remove_item, name="cart-remove-item"),
    path("checkout/", views.checkout, name="checkout"),
]
