# search/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from products.models import Product
from search.documents import ProductDocument

@receiver(post_save, sender=Product)
def index_product(sender, instance, **kwargs):
    ProductDocument(
        name=instance.name,
        description=instance.description,
        category=instance.category.name,
        brand=instance.brand.name,
        tags=[t.name for t in instance.tags.all()],
        price=float(instance.price),
        discounted_price=float(instance.discounted_price or 0),
        slug=instance.slug
    ).save()

@receiver(post_delete, sender=Product)
def delete_product(sender, instance, **kwargs):
    ProductDocument(meta={'id': instance.slug}).delete(ignore=404)
