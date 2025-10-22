import random
import string
from django.core.paginator import Paginator
from django.db import models
from django.db.models import Count, Case, When, ExpressionWrapper, DecimalField, F, Q, Avg
from django.utils import timezone

from media.models import Upload
from services.util import CustomRequestUtil


def generate_sku(product_name):
    name_part = product_name[:3].upper()

    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

    sku = f"{name_part}-{random_part}"

    return sku



class ProductService(CustomRequestUtil):

    def create_single(self, payload):
        from products.models import Product

        name = payload.get("name")
        price = payload.get("price")
        percentage_discount = payload.get("percentage_discount") or None
        short_description = payload.get("short_description") or None
        description = payload.get("description") or None
        stock = payload.get("stock") or None
        weight = payload.get("weight") or None
        dimensions = payload.get("dimensions") or None
        sizes = payload.get("sizes") or None
        brand = payload.get("brand") or None
        add_product_to_sales = payload.get("add_product_to_sales") or False
        sale_start = payload.get("sale_start") or None
        sale_end = payload.get("sale_end") or None
        colors = payload.get("colors")
        tags = payload.get("tags")
        category = payload.get("category")
        subcategories = payload.get("subcategories")
        media = payload.get("media", [])


        product, is_created = Product.available_objects.get_or_create(
            sku__iexact=generate_sku(name),
            defaults=dict(
                name=name,
                price=price,
                percentage_discount=percentage_discount,
                sku=generate_sku(name),
                description=description,
                short_description=short_description,
                stock=stock,
                add_product_to_sales=add_product_to_sales,
                sale_end=sale_end,
                sale_start=sale_start,
                sizes=sizes,
                category=category,
                weight=weight,
                brand=brand,
                dimensions=dimensions,
                created_by=self.auth_user
            )
        )
        if not is_created:
            return None, self.make_error("There was an error creating the product")


        if colors:
            product.colors.set(colors)
        if tags:
            product.tags.set(tags)
        if subcategories:
            product.sub_categories.set(subcategories)

        for img in media:
            Upload.objects.create(
                image=img,
                product=product,
                created_by=self.auth_user
            )

        message = "Product was created successfully"

        return message, None

    def fetch_list(self, category=None, subcategory=None, paginate=False, vendor=None):
        q = Q()
        if category:
            q &= Q(category__name__iexact=category)

        if subcategory:
            q &= Q(sub_categories__name__iexact=subcategory)

        if vendor:
            q &= Q(created_by=vendor.user)

        products = self.get_base_query().filter(q).distinct()

        if paginate:
            paginator = Paginator(products, 25)  # 25 items per page

            # get the current page number from request
            page_number = self.request.GET.get("page", 1)
            page_obj = paginator.get_page(page_number)

            return page_obj

        return products

    def update_product_views(self, product):
        product.views += 1
        product.save(update_fields=["views"])
        product.refresh_from_db()

        return None

    def update_quantity_sold(self, product, quantity=1):
        product.quantity_sold += quantity
        product.save(update_fields=["quantity_sold"])
        product.refresh_from_db()

        return None

    def get_related_products(self, product_id, limit=5):
        product, _ = self.fetch_single(product_id)

        related_products = self.get_base_query().filter(
            models.Q(category=product.category) | models.Q(tags__in=product.tags.all())
        ).exclude(id=product.id).distinct()[:limit]

        return related_products

    def get_base_query(self):
        from products.models import Product
        qs = Product.available_objects.prefetch_related(
            "tags", "colors", "sub_categories", "product_media"
        ).select_related(
            "category", "brand"
        ).order_by("rating")

        qs = qs.annotate(
            discounted_price=Case(
                When(
                    percentage_discount__isnull=False,
                    percentage_discount__gt=0,
                    then=ExpressionWrapper(
                        F('price') - ((F('percentage_discount') * F("price")) / 100),
                        output_field=DecimalField(max_digits=15, decimal_places=2)
                    )
                ),
                default=F('price'),
                output_field=DecimalField(max_digits=15, decimal_places=2)
            ),

            reviews_count=Count('reviews')
        )

        return qs

    def fetch_single(self, product_id):
        product = self.get_base_query().filter(id=product_id).first()
        if not product:
            return None, self.make_error("Product does not exist")

        return product, None


    def update_single(self, payload, product_id):
        product, _ = self.fetch_single(product_id)
        if not product:
            return None, _

        if product.created_by != self.auth_user:
            return None, "Invalid Action"

        product.name = payload.get("name") or product.name
        product.price = payload.get("price") or product.price
        product.percentage_discount = payload.get("percentage_discount") or product.percentage_discount
        product.short_description = payload.get("short_description") or product.short_description
        product.description = payload.get("description") or product.description
        product.stock = payload.get("stock") or product.stock
        product.weight = payload.get("weight") or product.weight
        product.dimensions = payload.get("dimensions") or product.dimensions
        product.sizes = payload.get("sizes") or product.sizes
        product.add_product_to_sales = payload.get("add_product_to_sales") or product.add_product_to_sales
        product.sale_end = payload.get("sale_end") or product.sale_end
        product.sale_start = payload.get("sale_start") or product.sale_start
        product.category = payload.get("category") or product.category
        product.updated_by = self.auth_user
        product.updated_at = timezone.now()

        product.save()

        if "colors" in payload:
            colors = payload.get("colors")
            if isinstance(colors, (list, tuple)):
                product.colors.set(colors)
            elif not colors:
                product.colors.clear()

        if "tags" in payload:
            tags = payload.get("tags")
            if isinstance(tags, (list, tuple)):
                product.tags.set(tags)
            elif not tags:
                product.tags.clear()

        if "subcategories" in payload:
            subcategories = payload.get("subcategories")
            if isinstance(subcategories, (list, tuple)):
                product.sub_categories.set(subcategories)
            elif not subcategories:
                product.sub_categories.clear()

        media_files = payload.get("media")
        if media_files:
            # Optional: clear existing images if desired
            # Upload.objects.filter(product=product).delete()

            for img in media_files:
                Upload.objects.create(
                    image=img,
                    product=product,
                    created_by=self.auth_user
                )

        message = "Product was updated successfully"

        return message, None


    def delete_single(self, product_id):
        product = self.get_base_query().filter(id=product_id).first()
        if not product:
            return None, self.make_error("Product does not exist")

        if product.created_by != self.auth_user:
            return None, "Invalid Action"

        product.deleted_at = timezone.now()
        product.deleted_by = self.auth_user
        product.save()

        message = "Product was deleted successfully"

        return message, None

    def fetch_single_by_slug(self, product_slug):
        product = self.get_base_query().filter(slug=product_slug).first()

        if not product:
            return None, self.make_error("Product does not exist")

        return product, None

    def fetch_product_ratings(self, product_id):
        from products.models import ProductReview

        # Aggregate data for average rating and ratings distribution
        ratings_data = ProductReview.objects.filter(product_id=product_id).aggregate(
            avg_rating=Avg('rating'),
            total_reviews=Count('id'),
        )

        # Distribution of ratings (e.g., 5 stars, 4 stars, etc.)
        rating_distribution = ProductReview.objects.filter(product_id=product_id).values(
            'rating'
        ).annotate(
            count=Count('id')
        )

        # Format distribution into a list for progress bar calculations
        total_reviews = ratings_data['total_reviews'] or 1
        rating_distribution = [
            {
                'rating': i,
                'count': next((x['count'] for x in rating_distribution if x['rating'] == i), 0),
                'percentage': (next((x['count'] for x in rating_distribution if x['rating'] == i),
                                    0) / total_reviews) * 100
            }
            for i in range(5, 0, -1)
        ]

        return {
            'avg_rating': round(ratings_data['avg_rating'] or 0, 1),
            'total_reviews': ratings_data['total_reviews'],
            'rating_distribution': rating_distribution,
        }

    def get_random_products(self, n=20):
        ids = list(self.fetch_list().values_list('id', flat=True))
        random_ids = random.sample(ids, min(len(ids), n))
        return self.get_base_query().filter(id__in=random_ids).order_by("?")
