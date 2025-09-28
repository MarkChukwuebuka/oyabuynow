from products.services.category_brand_service import CategoryService


def categories(request):
    return {'categories': CategoryService(request).fetch_list()}