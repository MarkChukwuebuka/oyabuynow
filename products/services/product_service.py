import random
import string

from django.db import models
from django.db.models import Count, Case, When, ExpressionWrapper, DecimalField, F, Q, Avg
from django.utils.text import slugify

from services.util import CustomRequestUtil


def generate_sku(product_name):
    name_part = product_name[:3].upper()

    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

    sku = f"{name_part}-{random_part}"

    return sku


def generate_unique_slug(instance, field_value, slug_field_name='slug'):
    """
    Generates a unique slug for a Django model instance.

    :param instance: The model instance to generate the slug for
    :param field_value: The text (usually product name) to base the slug on
    :param slug_field_name: The field name where the slug is stored
    :return: A unique slug string
    """
    slug = slugify(field_value)
    model_class = instance.__class__
    unique_slug = slug
    num = 1

    # Keep generating until it's unique
    while model_class.objects.filter(**{slug_field_name: unique_slug}).exists():
        unique_slug = f"{slug}-{num}"
        num += 1

    return unique_slug


class ProductService(CustomRequestUtil):

    def create_single(self, payload):
        from products.models import Product

        name = payload.get("name")
        price = payload.get("price")
        percentage_discount = payload.get("percentage_discount")
        description = payload.get("description")
        stock = payload.get("stock")
        cost_price = payload.get("cost_price")
        weight = payload.get("weight")
        dimensions = payload.get("dimensions")
        brand = payload.get("brand")

        product, is_created = Product.objects.create(
            name=name,
            price=price,
            percentage_discount=percentage_discount,
            sku=generate_sku(name),
            description=description,
            stock=stock,
            cost_price=cost_price,
            weight=weight,
            brand=brand,
            dimensions=dimensions,
            slug=generate_unique_slug(Product, name),
            created_by=self.auth_user
        )

        if not is_created:
            return None, self.make_error("There was an error creating the product")

        return product, None

    def fetch_list(self, filter_params=None, category=None):
        q = Q()
        if category:
            q &= Q(categories__name__iexact=category)

        return self.get_base_query().filter(q)

    def update_product_views(self, product):
        product.views += 1
        product.save(update_fields=["views"])
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
        qs = Product.objects.prefetch_related(
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
        return self.get_base_query().filter(id__in=random_ids)
