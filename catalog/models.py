from django.db import models
from django.utils.text import slugify

class TimeStamped(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True

class Category(TimeStamped):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE, related_name="children")
    description = models.TextField(blank=True)
    hero_image = models.URLField(blank=True)
    class Meta: verbose_name_plural = "Categories"
    def save(self,*a,**kw):
        if not self.slug: self.slug = slugify(self.name)
        super().save(*a,**kw)
    def __str__(self): return self.name

class Tag(TimeStamped):
    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=80, unique=True, blank=True)
    def save(self,*a,**kw):
        if not self.slug: self.slug = slugify(self.name)
        super().save(*a,**kw)
    def __str__(self): return self.name

class Collection(TimeStamped):
    title = models.CharField(max_length=140)
    slug = models.SlugField(max_length=160, unique=True, blank=True)
    subtitle = models.CharField(max_length=180, blank=True)
    hero_image = models.URLField(blank=True)
    is_featured = models.BooleanField(default=False)
    def save(self,*a,**kw):
        if not self.slug: self.slug = slugify(self.title)
        super().save(*a,**kw)
    def __str__(self): return self.title

class Product(TimeStamped):
    title = models.CharField(max_length=180)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    subtitle = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    tags = models.ManyToManyField(Tag, blank=True, related_name="products")
    collections = models.ManyToManyField(Collection, blank=True, related_name="products")
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    compare_at_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    rating_avg = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    rating_count = models.PositiveIntegerField(default=0)
    attributes_json = models.JSONField(default=dict, blank=True)  
    seo_title = models.CharField(max_length=160, blank=True)
    seo_description = models.CharField(max_length=200, blank=True)
    active = models.BooleanField(default=True)
    badge = models.CharField(max_length=40, blank=True)           

    def save(self,*a,**kw):
        if not self.slug: self.slug = slugify(self.title)
        super().save(*a,**kw)
    def __str__(self): return self.title

class ProductMedia(TimeStamped):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="media")
    url = models.URLField()
    kind = models.CharField(max_length=20, default="image")  
    alt = models.CharField(max_length=140, blank=True)
    sort_order = models.PositiveIntegerField(default=0)

class ProductVariant(TimeStamped):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    sku = models.CharField(max_length=64, unique=True)
    barcode = models.CharField(max_length=64, blank=True)
    options = models.JSONField(default=dict, blank=True) 
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_qty = models.IntegerField(default=0)
    is_default = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    class Meta:
        indexes = [models.Index(fields=["sku"]), models.Index(fields=["active"])]
    def __str__(self): return f"{self.product.title} [{self.sku}]"

class Discount(TimeStamped):
    name = models.CharField(max_length=120)
    code = models.CharField(max_length=40, unique=True)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True) 
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)   
    active = models.BooleanField(default=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    products = models.ManyToManyField(Product, blank=True, related_name="discounts")
    collections = models.ManyToManyField(Collection, blank=True, related_name="discounts")

class Review(TimeStamped):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    user_name = models.CharField(max_length=80) 
    rating = models.PositiveSmallIntegerField() 
    title = models.CharField(max_length=160, blank=True)
    body = models.TextField(blank=True)
    is_public = models.BooleanField(default=True)
    def __str__(self): return f"{self.product.title} ★{self.rating}"

class InventoryLog(TimeStamped):
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name="inventory_logs")
    delta = models.IntegerField()   
    reason = models.CharField(max_length=80, default="adjustment")
