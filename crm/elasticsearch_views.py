from django.http import JsonResponse
from django.views import View
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from .search import ProductSearch, CategorySearch, BrandSearch
from .enhanced_search import EnhancedProductSearch, HybridSearch


class ProductSearchView(View):
    """API view for product search with ProductService integration"""

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request):
        """
        GET /api/search/products/

        Query parameters:
        - q: Search query
        - category: Category ID or name
        - brand: Brand ID or name
        - min_price: Minimum price
        - max_price: Maximum price
        - tags: Comma-separated tag names
        - in_stock: true/false
        - sort: relevance|price_asc|price_desc|newest|popular
        - page: Page number (default: 1)
        - page_size: Items per page (default: 20)
        """
        try:
            query = request.GET.get('q', None)
            category = request.GET.get('category', None)
            brand = request.GET.get('brand', None)
            min_price = request.GET.get('min_price', None)
            max_price = request.GET.get('max_price', None)
            tags = request.GET.get('tags', None)
            in_stock = request.GET.get('in_stock', None)
            sort_by = request.GET.get('sort', 'relevance')
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 20))

            # Convert string parameters to appropriate types
            if min_price:
                min_price = float(min_price)
            if max_price:
                max_price = float(max_price)
            if tags:
                tags = [tag.strip() for tag in tags.split(',')]
            if in_stock:
                in_stock = in_stock.lower() == 'true'

            # Try to convert category/brand to int if possible
            try:
                if category and category.isdigit():
                    category = int(category)
            except (ValueError, AttributeError):
                pass

            try:
                if brand and brand.isdigit():
                    brand = int(brand)
            except (ValueError, AttributeError):
                pass

            # Use hybrid search
            results = HybridSearch.search(
                request=request,
                query=query,
                category=category,
                brand=brand,
                min_price=min_price,
                max_price=max_price,
                tags=tags,
                in_stock=in_stock,
                sort_by=sort_by,
                page=page,
                page_size=page_size
            )

            # Serialize products
            from products.serializers import ProductSerializer  # Adjust import to your serializer
            serialized_products = []
            for product in results['products']:
                # If it's already a dict (from ES), use it
                if isinstance(product, dict):
                    serialized_products.append(product)
                else:
                    # If it's a model instance, serialize it
                    # You can use your existing serializer or create a dict manually
                    first_image = product.product_media.first()
                    serialized_products.append({
                        'id': product.id,
                        'name': product.name,
                        'slug': product.slug,
                        'price': float(product.price),
                        'discounted_price': float(product.discounted_price),
                        'percentage_discount': product.percentage_discount,
                        'stock': product.stock,
                        'views': product.views,
                        'quantity_sold': product.quantity_sold,
                        'rating': float(product.rating) if product.rating else 0,
                        'reviews_count': product.reviews_count,
                        'cover_image': str(first_image.image) if first_image else None,
                        'category': {
                            'id': product.category.id,
                            'name': product.category.name
                        } if product.category else None,
                        'brand': {
                            'id': product.brand.id,
                            'name': product.brand.name
                        } if product.brand else None,
                    })

            return JsonResponse({
                'success': True,
                'data': {
                    'total': results['total'],
                    'products': serialized_products,
                    'page': results['page'],
                    'page_size': results['page_size'],
                    'total_pages': results['total_pages']
                }
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)


class ProductAutocompleteView(View):
    """API view for product autocomplete with ProductService data"""

    def get(self, request):
        """
        GET /api/search/autocomplete/

        Query parameters:
        - q: Search query (required)
        - size: Number of suggestions (default: 10)
        - method: autocomplete method ('combined', 'ngram', 'wildcard', 'word_start')
        """
        try:
            query = request.GET.get('q', '')
            size = int(request.GET.get('size', 10))
            method = request.GET.get('method', 'combined')  # Use combined by default

            if not query or len(query.strip()) < 2:
                return JsonResponse({
                    'success': True,
                    'suggestions': [],
                    'message': 'Query too short'
                })

            # Check if index exists first
            from elasticsearch import Elasticsearch
            from django.conf import settings

            try:
                es = Elasticsearch(hosts=settings.ELASTICSEARCH_DSL['default']['hosts'])
                if not es.indices.exists(index='products'):
                    return JsonResponse({
                        'success': False,
                        'error': 'Search index not ready',
                        'suggestions': []
                    })
            except Exception:
                return JsonResponse({
                    'success': False,
                    'error': 'Search temporarily unavailable',
                    'suggestions': []
                })

            # Use advanced autocomplete
            from .advanced_autocomplete import ProductSearch as AdvancedProductSearch
            suggestions = AdvancedProductSearch.autocomplete(query, size, method=method)

            # If you want to enrich with ProductService data, use this:
            # enhanced_search = EnhancedProductSearch(request)
            # suggestions = enhanced_search.autocomplete_with_service(query, size)

            return JsonResponse({
                'success': True,
                'suggestions': suggestions
            })

        except Exception as e:
            print(f"Autocomplete error: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'error': 'Search error occurred',
                'suggestions': []
            }, status=500)


class ProductFacetsView(View):
    """API view for product facets/aggregations"""

    def get(self, request):
        """
        GET /api/search/facets/

        Query parameters:
        - q: Optional search query to filter facets
        """
        try:
            query = request.GET.get('q', None)
            facets = ProductSearch.get_facets(query)

            return JsonResponse({
                'success': True,
                'facets': facets
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)


class SimilarProductsView(View):
    """API view for similar products"""

    def get(self, request, product_id):
        """
        GET /api/search/similar/<product_id>/

        Query parameters:
        - size: Number of similar products (default: 5)
        """
        try:
            size = int(request.GET.get('size', 5))
            similar = ProductSearch.similar_products(product_id, size)

            return JsonResponse({
                'success': True,
                'similar_products': similar
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)


class CategorySearchView(View):
    """API view for category search"""

    def get(self, request):
        """
        GET /api/search/categories/

        Query parameters:
        - q: Search query
        """
        try:
            query = request.GET.get('q', None)
            results = CategorySearch.search_categories(query)

            return JsonResponse({
                'success': True,
                'categories': results
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)


class BrandSearchView(View):
    """API view for brand search"""

    def get(self, request):
        """
        GET /api/search/brands/

        Query parameters:
        - q: Search query
        """
        try:
            query = request.GET.get('q', None)
            results = BrandSearch.search_brands(query)

            return JsonResponse({
                'success': True,
                'brands': results
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)