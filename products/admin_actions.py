from django.contrib import admin, messages
from django_elasticsearch_dsl.registries import registry


@admin.action(description='Reindex selected products in Elasticsearch')
def reindex_products(modeladmin, request, queryset):
    """
    Admin action to reindex selected products
    """
    success_count = 0
    error_count = 0

    for product in queryset:
        try:
            registry.update(product)
            success_count += 1
        except Exception as e:
            error_count += 1
            messages.error(request, f"Error indexing {product.name}: {str(e)}")

    if success_count > 0:
        messages.success(
            request,
            f"Successfully reindexed {success_count} product(s)"
        )

    if error_count > 0:
        messages.warning(
            request,
            f"Failed to reindex {error_count} product(s)"
        )


@admin.action(description='Remove selected products from Elasticsearch index')
def remove_from_index(modeladmin, request, queryset):
    """
    Admin action to remove products from Elasticsearch without deleting from database
    """
    success_count = 0
    error_count = 0

    for product in queryset:
        try:
            registry.delete(product, raise_on_error=False)
            success_count += 1
        except Exception as e:
            error_count += 1
            messages.error(request, f"Error removing {product.name} from index: {str(e)}")

    if success_count > 0:
        messages.success(
            request,
            f"Successfully removed {success_count} product(s) from index"
        )

    if error_count > 0:
        messages.warning(
            request,
            f"Failed to remove {error_count} product(s) from index"
        )


@admin.action(description='Reindex selected categories and their products')
def reindex_categories(modeladmin, request, queryset):
    """
    Admin action to reindex selected categories and all their products
    """
    success_count = 0
    error_count = 0
    product_count = 0

    for category in queryset:
        try:
            # Reindex category
            registry.update(category)
            success_count += 1

            # Reindex all products in category
            products = category.products.all()
            for product in products:
                try:
                    registry.update(product)
                    product_count += 1
                except Exception as e:
                    error_count += 1

        except Exception as e:
            error_count += 1
            messages.error(request, f"Error indexing category {category.name}: {str(e)}")

    if success_count > 0:
        messages.success(
            request,
            f"Successfully reindexed {success_count} category(ies) and {product_count} product(s)"
        )

    if error_count > 0:
        messages.warning(
            request,
            f"Encountered {error_count} error(s) during reindexing"
        )


@admin.action(description='Reindex selected brands and their products')
def reindex_brands(modeladmin, request, queryset):
    """
    Admin action to reindex selected brands and all their products
    """
    success_count = 0
    error_count = 0
    product_count = 0

    for brand in queryset:
        try:
            # Reindex brand
            registry.update(brand)
            success_count += 1

            # Reindex all products with this brand
            products = brand.product_set.all()
            for product in products:
                try:
                    registry.update(product)
                    product_count += 1
                except Exception as e:
                    error_count += 1

        except Exception as e:
            error_count += 1
            messages.error(request, f"Error indexing brand {brand.name}: {str(e)}")

    if success_count > 0:
        messages.success(
            request,
            f"Successfully reindexed {success_count} brand(s) and {product_count} product(s)"
        )

    if error_count > 0:
        messages.warning(
            request,
            f"Encountered {error_count} error(s) during reindexing"
        )
