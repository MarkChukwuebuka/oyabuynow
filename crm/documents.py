from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry

from media.models import Upload
from products.models import Product, Category, Subcategory, Brand, Tag


@registry.register_document
class ProductDocument(Document):
    """Elasticsearch document for Product model"""

    # Category fields
    category = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'name': fields.TextField(),
    })

    # Subcategories as nested objects
    sub_categories = fields.NestedField(properties={
        'id': fields.IntegerField(),
        'name': fields.TextField(),
    })

    # Brand fields
    brand = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'name': fields.TextField(),
    })

    # Tags as nested objects
    tags = fields.NestedField(properties={
        'id': fields.IntegerField(),
        'name': fields.TextField(),
    })

    # Colors as nested objects
    colors = fields.NestedField(properties={
        'id': fields.IntegerField(),
        'name': fields.TextField(),
        'hex_code': fields.TextField(),
    })

    # Product media/images
    product_media = fields.NestedField(properties={
        'id': fields.IntegerField(),
        'image': fields.TextField(),  # store URL or string identifier
    })

    # Define analyzed text fields here
    name = fields.TextField(analyzer='ngram_analyzer', search_analyzer='search_analyzer')
    description = fields.TextField(analyzer='ngram_analyzer', search_analyzer='search_analyzer')
    short_description = fields.TextField(analyzer='ngram_analyzer', search_analyzer='search_analyzer')


    # Computed fields
    discounted_price = fields.FloatField()
    reviews_count = fields.IntegerField()

    # Additional custom fields
    views = fields.IntegerField()
    quantity_sold = fields.IntegerField()
    rating = fields.FloatField()
    weight = fields.FloatField()
    dimensions = fields.TextField()
    sizes = fields.TextField()

    # Add completion suggester for autocomplete
    name_suggest = fields.CompletionField()
    # name_suggest = fields.CompletionField(
    #     analyzer='ngram_analyzer',
    #     search_analyzer='search_analyzer'
    # )

    class Index:
        name = 'products'

        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0,
            'index': {
                'max_ngram_diff': 18
            },
            'analysis': {
                'filter': {
                    'ngram_filter': {
                        'type': 'ngram',
                        'min_gram': 2,
                        'max_gram': 20
                    }
                },
                'analyzer': {
                    'ngram_analyzer': {
                        'type': 'custom',
                        'tokenizer': 'standard',
                        'filter': ['lowercase', 'asciifolding', 'ngram_filter']
                    },
                    'search_analyzer': {
                        'type': 'custom',
                        'tokenizer': 'standard',
                        'filter': ['lowercase', 'asciifolding']
                    }
                }
            }
        }

    class Django:
        model = Product
        fields = [
            'id',
            # 'name',
            'slug',
            'price',
            'percentage_discount',
            'sku',
            # 'description',
            # 'short_description',
            'stock',
            'add_product_to_sales',
            'sale_start',
            'sale_end',
            'created_at',
            'updated_at',

        ]
        related_models = [Category, Subcategory, Brand, Tag, Upload]

    def get_instances_from_related(self, related_instance):
        # when a related model changed, return products to re-index
        if isinstance(related_instance, Category):
            return related_instance.products.all()
        if isinstance(related_instance, Subcategory):
            return related_instance.products.all()
        if isinstance(related_instance, Brand):
            # brand may use product_set or related_name — adjust if different
            return related_instance.product_set.all()
        if isinstance(related_instance, Tag):
            return related_instance.products.all()
        if isinstance(related_instance, Upload):
            # Upload has foreign key 'product' (nullable). Return that product if present
            if related_instance.product:
                return [related_instance.product]
            return []

        return None

    def prepare_category(self, instance):
        """Prepare category data"""
        if instance.category:
            return {
                'id': instance.category.id,
                'name': instance.category.name,
            }
        return None

    def prepare_sub_categories(self, instance):
        """Prepare subcategories data"""
        return [
            {
                'id': sub.id,
                'name': sub.name,
            }
            for sub in instance.sub_categories.all()
        ]


    def prepare_brand(self, instance):
        """Prepare brand data"""
        if instance.brand:
            return {
                'id': instance.brand.id,
                'name': instance.brand.name,
            }
        return None

    def prepare_tags(self, instance):
        """Prepare tags data"""
        return [
            {
                'id': tag.id,
                'name': tag.name,
            }
            for tag in instance.tags.all()
        ]

    def prepare_colors(self, instance):
        """Prepare colors data"""
        return [
            {
                'id': color.id,
                'name': color.name,
                'hex_code': getattr(color, 'hex_code', ''),
            }
            for color in instance.colors.all()
        ]

    def prepare_discounted_price(self, instance):
        """Calculate discounted price"""
        if instance.percentage_discount:
            discount = (instance.price * instance.percentage_discount) / 100
            return float(instance.price - discount)
        return float(instance.price)

    def prepare_product_media(self, instance):
        """
        Return list of media dicts. Use Upload.image.url if available,
        otherwise fall back to str(image) (CloudinaryField often stores public_id).
        """
        media = []
        for up in instance.product_media.all():  # related_name on Upload model
            # Try to get a usable URL:
            url = None
            try:
                # many storage fields provide .url
                url = up.image.url
            except Exception:
                # fallback to text repr (public_id) — client may need to construct final URL
                url = str(up.image) if up.image else None

            media.append({'id': up.id, 'image': url})
        return media


    def prepare_name_suggest(self, instance):
        """Prepare autocomplete suggestions"""
        return {
            'input': [instance.name],
            'weight': instance.stock if instance.stock else 1,
        }


@registry.register_document
class CategoryDocument(Document):
    """Elasticsearch document for Category model"""

    # Count of products in category
    product_count = fields.IntegerField()

    class Index:
        name = 'categories'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0
        }

    class Django:
        model = Category
        fields = [
            'id',
            'name',
            'created_at',
            'updated_at',
        ]

    def prepare_product_count(self, instance):
        """Get product count for category"""
        return instance.products.count()


@registry.register_document
class BrandDocument(Document):
    """Elasticsearch document for Brand model"""

    product_count = fields.IntegerField()

    class Index:
        name = 'brands'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0
        }

    class Django:
        model = Brand
        fields = [
            'id',
            'name',
            'created_at',
            'updated_at',
        ]

    def prepare_product_count(self, instance):
        """Get product count for brand"""
        return instance.product_set.count()