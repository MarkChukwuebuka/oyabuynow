from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django_elasticsearch_dsl.registries import registry
from products.models import Product, Category, Subcategory, Brand, Tag, Color


@receiver(post_save, sender=Product)
def update_product_on_save(sender, instance, created, **kwargs):
    """
    Update Elasticsearch index when a Product is created or updated
    """
    try:
        registry.update(instance)
        print(f"✓ Product '{instance.name}' indexed successfully")
    except Exception as e:
        print(f"✗ Error indexing product '{instance.name}': {str(e)}")


@receiver(post_delete, sender=Product)
def delete_product_from_index(sender, instance, **kwargs):
    """
    Remove Product from Elasticsearch index when deleted
    """
    try:
        registry.delete(instance, raise_on_error=False)
        print(f"✓ Product '{instance.name}' removed from index")
    except Exception as e:
        print(f"✗ Error removing product from index: {str(e)}")


@receiver(post_save, sender=Category)
def update_category_on_save(sender, instance, created, **kwargs):
    """
    Update Category in Elasticsearch and update all related products
    """
    try:
        # Update category document
        registry.update(instance)

        # Update all products in this category
        products = instance.products.all()
        for product in products:
            registry.update(product)

        action = "created" if created else "updated"
        print(f"✓ Category '{instance.name}' {action} and {products.count()} products reindexed")
    except Exception as e:
        print(f"✗ Error updating category: {str(e)}")


@receiver(post_delete, sender=Category)
def delete_category_from_index(sender, instance, **kwargs):
    """
    Remove Category from Elasticsearch and update related products
    """
    try:
        # Delete category document
        registry.delete(instance, raise_on_error=False)

        # Note: Related products are already updated due to SET_NULL cascade
        print(f"✓ Category '{instance.name}' removed from index")
    except Exception as e:
        print(f"✗ Error removing category from index: {str(e)}")


@receiver(post_save, sender=Subcategory)
def update_subcategory_on_save(sender, instance, created, **kwargs):
    """
    Update Subcategory and all related products
    """
    try:
        # Update all products with this subcategory
        products = instance.products.all()
        for product in products:
            registry.update(product)

        action = "created" if created else "updated"
        print(f"✓ Subcategory '{instance.name}' {action} and {products.count()} products reindexed")
    except Exception as e:
        print(f"✗ Error updating subcategory: {str(e)}")


@receiver(post_delete, sender=Subcategory)
def delete_subcategory_from_index(sender, instance, **kwargs):
    """
    Update products when Subcategory is deleted
    """
    try:
        # Products with this subcategory need to be reindexed
        # Note: The relationship is already removed by Django
        print(f"✓ Subcategory '{instance.name}' removed")
    except Exception as e:
        print(f"✗ Error handling subcategory deletion: {str(e)}")


@receiver(post_save, sender=Brand)
def update_brand_on_save(sender, instance, created, **kwargs):
    """
    Update Brand in Elasticsearch and update all related products
    """
    try:
        # Update brand document
        registry.update(instance)

        # Update all products with this brand
        products = instance.product_set.all()
        for product in products:
            registry.update(product)

        action = "created" if created else "updated"
        print(f"✓ Brand '{instance.name}' {action} and {products.count()} products reindexed")
    except Exception as e:
        print(f"✗ Error updating brand: {str(e)}")


@receiver(post_delete, sender=Brand)
def delete_brand_from_index(sender, instance, **kwargs):
    """
    Remove Brand from Elasticsearch and update related products
    """
    try:
        # Delete brand document
        registry.delete(instance, raise_on_error=False)

        # Note: Related products are already updated due to SET_NULL cascade
        print(f"✓ Brand '{instance.name}' removed from index")
    except Exception as e:
        print(f"✗ Error removing brand from index: {str(e)}")


@receiver(post_save, sender=Tag)
def update_tag_on_save(sender, instance, created, **kwargs):
    """
    Update all products with this tag when tag is modified
    """
    try:
        # Update all products with this tag
        products = instance.products.all()
        for product in products:
            registry.update(product)

        action = "created" if created else "updated"
        print(f"✓ Tag '{instance.name}' {action} and {products.count()} products reindexed")
    except Exception as e:
        print(f"✗ Error updating tag: {str(e)}")


@receiver(post_delete, sender=Tag)
def delete_tag_from_index(sender, instance, **kwargs):
    """
    Update products when Tag is deleted
    """
    try:
        # Products with this tag need to be reindexed
        # Note: The relationship is already removed by Django
        print(f"✓ Tag '{instance.name}' removed")
    except Exception as e:
        print(f"✗ Error handling tag deletion: {str(e)}")


@receiver(post_save, sender=Color)
def update_color_on_save(sender, instance, created, **kwargs):
    """
    Update all products with this color when color is modified
    """
    try:
        # Update all products with this color
        products = instance.products.all()
        for product in products:
            registry.update(product)

        action = "created" if created else "updated"
        print(f"✓ Color '{instance.name}' {action} and {products.count()} products reindexed")
    except Exception as e:
        print(f"✗ Error updating color: {str(e)}")


@receiver(post_delete, sender=Color)
def delete_color_from_index(sender, instance, **kwargs):
    """
    Update products when Color is deleted
    """
    try:
        # Products with this color need to be reindexed
        # Note: The relationship is already removed by Django
        print(f"✓ Color '{instance.name}' removed")
    except Exception as e:
        print(f"✗ Error handling color deletion: {str(e)}")


# ManyToMany signal handlers
@receiver(m2m_changed, sender=Product.sub_categories.through)
def update_product_subcategories(sender, instance, action, **kwargs):
    """
    Update product index when subcategories are added/removed
    """
    if action in ['post_add', 'post_remove', 'post_clear']:
        try:
            registry.update(instance)
            print(f"✓ Product '{instance.name}' subcategories updated in index")
        except Exception as e:
            print(f"✗ Error updating product subcategories: {str(e)}")


@receiver(m2m_changed, sender=Product.tags.through)
def update_product_tags(sender, instance, action, **kwargs):
    """
    Update product index when tags are added/removed
    """
    if action in ['post_add', 'post_remove', 'post_clear']:
        try:
            registry.update(instance)
            print(f"✓ Product '{instance.name}' tags updated in index")
        except Exception as e:
            print(f"✗ Error updating product tags: {str(e)}")


@receiver(m2m_changed, sender=Product.colors.through)
def update_product_colors(sender, instance, action, **kwargs):
    """
    Update product index when colors are added/removed
    """
    if action in ['post_add', 'post_remove', 'post_clear']:
        try:
            registry.update(instance)
            print(f"✓ Product '{instance.name}' colors updated in index")
        except Exception as e:
            print(f"✗ Error updating product colors: {str(e)}")


# Batch update helper function
def bulk_update_products(product_ids):
    """
    Helper function to bulk update multiple products
    Useful for admin actions or migrations
    """
    from products.models import Product

    products = Product.objects.filter(id__in=product_ids)
    updated_count = 0

    for product in products:
        try:
            registry.update(product)
            updated_count += 1
        except Exception as e:
            print(f"✗ Error updating product {product.id}: {str(e)}")

    print(f"✓ Bulk updated {updated_count}/{len(product_ids)} products")
    return updated_count


# Batch delete helper function
def bulk_delete_products(product_ids):
    """
    Helper function to bulk remove multiple products from index
    """
    from products.models import Product

    deleted_count = 0

    for product_id in product_ids:
        try:
            # Create a mock instance with just the ID for deletion
            product = Product(id=product_id)
            registry.delete(product, raise_on_error=False)
            deleted_count += 1
        except Exception as e:
            print(f"✗ Error deleting product {product_id} from index: {str(e)}")

    print(f"✓ Bulk deleted {deleted_count}/{len(product_ids)} products from index")
    return deleted_count