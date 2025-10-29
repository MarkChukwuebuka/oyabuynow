from django.core.management.base import BaseCommand
from products.models import Product, Category, Brand, Tag
from search.documents import ProductDocument, CategoryDocument, BrandDocument, TagDocument

class Command(BaseCommand):
    help = "Reindex all searchable models into Elasticsearch"

    def handle(self, *args, **kwargs):
        for doc_cls, model in [
            (ProductDocument, Product),
            (CategoryDocument, Category),
            (BrandDocument, Brand),
            (TagDocument, Tag),
        ]:
            doc_cls.init()
            for obj in model.objects.all():
                if model == Product:
                    doc = doc_cls(
                        name=obj.name,
                        description=obj.description,
                        category=obj.category.name,
                        brand=obj.brand.name if obj.brand else None,
                        tags=[t.name for t in obj.tags.all()],
                        price=float(obj.price),
                        percentage_discount=float(obj.percentage_discount or 0),
                        slug=obj.slug
                    )
                else:
                    doc = doc_cls(name=obj.name)
                doc.save()
        self.stdout.write(self.style.SUCCESS('✅ Reindexing complete'))
