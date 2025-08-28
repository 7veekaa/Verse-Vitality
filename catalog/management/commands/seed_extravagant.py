from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from catalog.models import (
    Category,
    Tag,
    Collection,
    Product,
    ProductMedia,
    ProductVariant,
)

def set_if_has(obj, field, value):
    """Set field on obj if model has that field (keeps command compatible with your models)."""
    if hasattr(obj, field):
        setattr(obj, field, value)

class Command(BaseCommand):
    help = "Seed extravagant sample catalog data (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete all existing Products/Variants/Media before seeding.",
        )

    @transaction.atomic
    def handle(self, *args, **opts):
        if opts["reset"]:
            self.stdout.write(self.style.WARNING("Resetting catalog tables…"))
            ProductMedia.objects.all().delete()
            ProductVariant.objects.all().delete()
            Product.objects.all().delete()
            # Keeping Category/Tag/Collection so URLs remain stable

        # ---- Categories / Tags / Collections ----
        skincare, _ = Category.objects.get_or_create(name="Skincare")
        set_if_has(skincare, "slug", getattr(skincare, "slug", "skincare") or "skincare")
        skincare.save()

        bodycare, _ = Category.objects.get_or_create(name="Bodycare")
        set_if_has(bodycare, "slug", getattr(bodycare, "slug", "bodycare") or "bodycare")
        bodycare.save()

        calm, _ = Tag.objects.get_or_create(name="Calming")
        set_if_has(calm, "slug", getattr(calm, "slug", "calming") or "calming")
        calm.save()

        sleep_tag, _ = Tag.objects.get_or_create(name="Sleep")
        set_if_has(sleep_tag, "slug", getattr(sleep_tag, "slug", "sleep") or "sleep")
        sleep_tag.save()

        glow, _ = Tag.objects.get_or_create(name="Glow")
        set_if_has(glow, "slug", getattr(glow, "slug", "glow") or "glow")
        glow.save()

        bedtime, _ = Collection.objects.get_or_create(
            title="Bedtime Rituals", defaults={"is_featured": True}
        )
        unwind, _ = Collection.objects.get_or_create(
            title="Unwind Essentials", defaults={"is_featured": True}
        )

        # ---- Helper to upsert product + media + variants ----
        def upsert_product(
            title,
            subtitle,
            description,
            category,
            base_price,
            compare_at_price=None,
            badge=None,
            attributes=None,
            tags=None,
            collections=None,
            media=None,
            variants=None,
        ):
            p, created = Product.objects.get_or_create(
                title=title,
                defaults={
                    "subtitle": subtitle,
                    "description": description,
                    "category": category,
                    "base_price": base_price,
                    **({"compare_at_price": compare_at_price} if compare_at_price else {}),
                    **({"badge": badge} if badge else {}),
                    **({"attributes_json": attributes} if attributes else {}),
                },
            )
            if not created:
                # Keep it fresh on re-run
                p.subtitle = subtitle
                p.description = description
                p.category = category
                p.base_price = base_price
                set_if_has(p, "compare_at_price", compare_at_price)
                set_if_has(p, "badge", badge)
                if attributes is not None and hasattr(p, "attributes_json"):
                    p.attributes_json = attributes
                p.save()

            # tags / collections
            if tags:
                p.tags.add(*tags)
            if collections:
                p.collections.add(*collections)

            # media (ensure deterministic)
            if media:
                for i, m in enumerate(media, start=1):
                    ProductMedia.objects.get_or_create(
                        product=p,
                        url=m["url"],
                        defaults={
                            "alt": m.get("alt", title),
                            "sort_order": m.get("sort_order", i),
                        },
                    )

            # variants
            if variants:
                for v in variants:
                    pv, v_created = ProductVariant.objects.get_or_create(
                        product=p,
                        sku=v["sku"],
                        defaults={
                            "options": v.get("options", {}),
                            "price": v.get("price", base_price),
                            "stock_qty": v.get("stock_qty", 0),
                            "is_default": v.get("is_default", False),
                        },
                    )
                    if not v_created:
                        pv.options = v.get("options", pv.options)
                        pv.price = v.get("price", pv.price)
                        pv.stock_qty = v.get("stock_qty", pv.stock_qty)
                        pv.is_default = v.get("is_default", pv.is_default)
                        pv.save()
            return p

        # ---- Products ----
        p1 = upsert_product(
            title="Lavender Night Serum",
            subtitle="Deep-rest formula",
            description="Potent botanicals with lavender & bakuchiol.",
            category=skincare,
            base_price=1299,
            compare_at_price=1499,
            badge="Best Seller",
            attributes={"notes": "lavender", "skin_type": "all"},
            tags=[calm, sleep_tag],
            collections=[bedtime],
            media=[
                {"url": "https://picsum.photos/seed/serum/800/800", "alt": "Serum packshot"},
            ],
            variants=[
                {"sku": "SERUM-30ML", "options": {"size": "30ml"}, "price": 1299, "stock_qty": 120, "is_default": True},
                {"sku": "SERUM-50ML", "options": {"size": "50ml"}, "price": 1699, "stock_qty": 60},
            ],
        )

        p2 = upsert_product(
            title="Chamomile Sleep Mist",
            subtitle="Pillow spray for instant calm",
            description="A delicate chamomile & vanilla blend to cue your wind-down.",
            category=bodycare,
            base_price=899,
            compare_at_price=1099,
            badge="Editor’s Pick",
            attributes={"notes": "chamomile", "use": "pillow-spray"},
            tags=[calm, sleep_tag],
            collections=[bedtime, unwind],
            media=[
                {"url": "https://picsum.photos/seed/sleepmist/800/800", "alt": "Sleep mist bottle"},
            ],
            variants=[
                {"sku": "MIST-100ML", "options": {"size": "100ml"}, "price": 899, "stock_qty": 150, "is_default": True},
            ],
        )

        p3 = upsert_product(
            title="Bright C Glow Gel",
            subtitle="Daily vitamin C radiance",
            description="Water-light gel with stabilized vitamin C for everyday glow.",
            category=skincare,
            base_price=1199,
            compare_at_price=1399,
            badge="Trending",
            attributes={"notes": "citrus", "skin_goal": "glow"},
            tags=[glow],
            collections=[unwind],
            media=[
                {"url": "https://picsum.photos/seed/glowgel/800/800", "alt": "Glow gel flatlay"},
            ],
            variants=[
                {"sku": "GLOW-30ML", "options": {"size": "30ml"}, "price": 1199, "stock_qty": 90, "is_default": True},
            ],
        )

        # Friendly output
        self.stdout.write(self.style.SUCCESS("Seeded extravagant catalog ✔"))
        self.stdout.write(f"Products: {Product.objects.count()} | Variants: {ProductVariant.objects.count()} | Media: {ProductMedia.objects.count()}")
        self.stdout.write(f"Categories: {Category.objects.count()} | Tags: {Tag.objects.count()} | Collections: {Collection.objects.count()}")
