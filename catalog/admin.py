from django.contrib import admin
from .models import Category, Tag, Collection, Product, ProductMedia, ProductVariant, Discount, Review

class MediaInline(admin.TabularInline):
    model = ProductMedia
    extra = 1

class VariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("title","category","badge","base_price","active","rating_avg","rating_count")
    list_filter = ("active","category","tags","collections","badge")
    search_fields = ("title","subtitle","description")
    inlines = [MediaInline, VariantInline]
    prepopulated_fields = {"slug": ("title",)}

admin.site.register([Category, Tag, Collection, Discount, Review])
