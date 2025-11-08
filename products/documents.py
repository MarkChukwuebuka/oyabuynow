from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry

from media.models import Upload
from .models import Product, Category, Subcategory, Brand, Tag


@registry.register_document
class ProductDocument(Document):
    """
    Elasticsearch document mapping with optimized text analysis and HTML processing
    """
    name = fields.TextField(
        analyzer='autocomplete_analyzer',
        search_analyzer='standard',
        fields={
            'raw': fields.KeywordField(),
            'suggest': fields.TextField(analyzer='autocomplete_analyzer')  # for search-based autocomplete
        }
    )

    short_description = fields.TextField(analyzer='english')
    description = fields.TextField(analyzer='english')
    category = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'name': fields.TextField(),
    })

    sub_categories = fields.NestedField(properties={
        'id': fields.IntegerField(),
        'name': fields.TextField(),
    })

    brand = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'name': fields.TextField(),
    })

    tags = fields.NestedField(properties={
        'id': fields.IntegerField(),
        'name': fields.TextField(),
    })

    colors = fields.NestedField(properties={
        'id': fields.IntegerField(),
        'name': fields.TextField(),
        'hex_code': fields.TextField(),
    })

    # Product media: nested list of {id, image}
    product_media = fields.NestedField(properties={
        'id': fields.IntegerField(),
        'image': fields.TextField(),  # store URL or string identifier
    })

    discounted_price = fields.FloatField()
    reviews_count = fields.IntegerField()

    views = fields.IntegerField()
    quantity_sold = fields.IntegerField()
    rating = fields.FloatField()
    weight = fields.FloatField()
    dimensions = fields.TextField()
    sizes = fields.TextField()
    name_suggest = fields.CompletionField(attr='name')

    class Index:
        name = 'products'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0,
            'analysis': {
                'analyzer': {
                    'autocomplete_analyzer': {
                        'type': 'custom',
                        'tokenizer': 'edge_ngram_tokenizer',
                        'filter': [
                            'lowercase'
                        ]
                    }
                },
                'tokenizer': {
                    'edge_ngram_tokenizer': {
                        'type': 'edge_ngram',
                        'min_gram': 2,
                        'max_gram': 20,
                        'token_chars': ['letter', 'digit']
                    }
                }
            }
        }

    class Django:
        model = Product
        fields = [
            'id',
            'slug',
            'price',
            'percentage_discount',
            'sku',
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

    def prepare_category(self, instance):
        if instance.category:
            return {'id': instance.category.id, 'name': instance.category.name}
        return None

    def prepare_sub_categories(self, instance):
        return [{'id': sub.id, 'name': sub.name} for sub in instance.sub_categories.all()]

    def prepare_brand(self, instance):
        if instance.brand:
            return {'id': instance.brand.id, 'name': instance.brand.name}
        return None

    def prepare_tags(self, instance):
        return [{'id': t.id, 'name': t.name} for t in instance.tags.all()]

    def prepare_colors(self, instance):
        return [
            {'id': c.id, 'name': c.name, 'hex_code': getattr(c, 'hex_code', '')}
            for c in instance.colors.all()
        ]

    def prepare_discounted_price(self, instance):
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
        for up in instance.product_media.all():   # related_name on Upload model
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
        # add name and maybe slug, brand, etc for better suggestions
        inputs = [instance.name]
        if instance.slug:
            inputs.append(instance.slug.replace('-', ' '))
        if instance.brand:
            inputs.append(instance.brand.name)
        return {'input': inputs, 'weight': instance.stock or 1}