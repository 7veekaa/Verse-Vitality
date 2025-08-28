from rest_framework import viewsets, mixins, decorators, response, status
from django.db.models import Prefetch, Q
from .models import Product, Category, Tag, Collection, Review
from .serializers import (
    ProductListSerializer, ProductDetailSerializer, ReviewSerializer,
    CategoryMiniSerializer, TagSerializer
)

class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        Product.objects.filter(active=True)
        .select_related("category")
        .prefetch_related("tags","media","discounts",
            Prefetch("variants"))
    )
    filterset_fields = ["category__slug", "tags__slug", "collections__slug", "active", "badge"]
    search_fields = ["title","subtitle","description","attributes_json"]
    ordering_fields = ["base_price","title","rating_avg","created_at"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        return ProductDetailSerializer if self.action == "retrieve" else ProductListSerializer

    @decorators.action(detail=True, methods=["get"])
    def related(self, request, pk=None):
        p = self.get_object()
        qs = (
            Product.objects.filter(active=True)
            .exclude(id=p.id)
            .filter(Q(category=p.category) | Q(tags__in=p.tags.all()))
            .distinct()[:8]
        )
        ser = ProductListSerializer(qs, many=True, context={"request": request})
        return response.Response(ser.data)

    @decorators.action(detail=True, methods=["get","post"])
    def reviews(self, request, pk=None):
        if request.method == "GET":
            qs = Review.objects.filter(product_id=pk, is_public=True).order_by("-created_at")[:50]
            return response.Response(ReviewSerializer(qs, many=True).data)
        ser = ReviewSerializer(data=request.data)
        if ser.is_valid():
            ser.save(product_id=pk)
            return response.Response(ser.data, status=status.HTTP_201_CREATED)
        return response.Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategoryMiniSerializer
    lookup_field = "slug"

class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    lookup_field = "slug"
