"""
Enhanced Search Service that integrates with ProductService
"""


from .search import ProductSearch
from products.services.product_service import ProductService


class EnhancedProductSearch:
    """
    Enhanced search that combines Elasticsearch with ProductService
    """

    def __init__(self, request=None):
        self.request = request
        if request:
            self.product_service = ProductService(request)
        else:
            # Create a mock request for service
            from django.http import HttpRequest
            mock_request = HttpRequest()
            mock_request.user = None
            self.product_service = ProductService(mock_request)

    @staticmethod
    def search_products_elasticsearch(query=None, category=None, brand=None,
                                      min_price=None, max_price=None,
                                      tags=None, in_stock=None,
                                      sort_by='relevance', page=1, page_size=20):
        """
        Search using Elasticsearch and return product IDs
        Then fetch full products using ProductService
        """
        # Get search results from Elasticsearch
        es_results = ProductSearch.search_products(
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

        return es_results

    def search_and_fetch_products(self, query=None, category=None, brand=None,
                                  min_price=None, max_price=None,
                                  tags=None, in_stock=None,
                                  sort_by='relevance', page=1, page_size=20):
        """
        Search with Elasticsearch, then fetch full products with ProductService
        This gives you all the annotated fields and relationships
        """
        # Get ES results (just IDs and basic info)
        es_results = self.search_products_elasticsearch(
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

        if es_results['total'] == 0:
            return {
                'total': 0,
                'products': [],
                'page': page,
                'page_size': page_size,
                'total_pages': 0
            }

        # Extract product IDs from ES results
        product_ids = [product['id'] for product in es_results['products']]

        # Fetch full products using ProductService with all annotations
        products_qs = self.product_service.get_base_query().filter(id__in=product_ids)

        # Maintain ES order
        product_dict = {p.id: p for p in products_qs}
        ordered_products = [product_dict[pid] for pid in product_ids if pid in product_dict]

        return {
            'total': es_results['total'],
            'products': ordered_products,
            'page': page,
            'page_size': page_size,
            'total_pages': es_results['total_pages']
        }

    def autocomplete_with_service(self, query, size=10):
        """
        Get autocomplete suggestions and enrich with ProductService data
        """
        # Get ES suggestions
        suggestions = ProductSearch.autocomplete(query, size)

        if not suggestions:
            return []

        # Extract product IDs
        product_ids = [s['product']['id'] for s in suggestions]

        # Fetch full products with ProductService
        products_qs = self.product_service.get_base_query().filter(id__in=product_ids)
        product_dict = {p.id: p for p in products_qs}

        # Enrich suggestions with full product data
        enriched_suggestions = []
        for suggestion in suggestions:
            product_id = suggestion['product']['id']
            if product_id in product_dict:
                product = product_dict[product_id]

                # Get first product image
                first_image = product.product_media.first()
                cover_image = str(first_image.image) if first_image else None

                enriched_suggestions.append({
                    'text': suggestion['text'],
                    'score': suggestion['score'],
                    'product': {
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
                        'cover_image': cover_image,
                        'category': {
                            'id': product.category.id,
                            'name': product.category.name
                        } if product.category else None,
                        'brand': {
                            'id': product.brand.id,
                            'name': product.brand.name
                        } if product.brand else None,
                    }
                })

        return enriched_suggestions

    def get_related_products_hybrid(self, product_id, limit=5):
        """
        Get related products using both ES similarity and ProductService logic
        """
        # Get ES similar products
        es_similar = ProductSearch.similar_products(product_id, size=limit * 2)
        es_product_ids = [p['id'] for p in es_similar]

        # Get ProductService related products
        service_related = self.product_service.get_related_products(product_id, limit=limit * 2)
        service_product_ids = [p.id for p in service_related]

        # Combine and deduplicate (ES results first, then service results)
        combined_ids = []
        seen = set()

        for pid in es_product_ids:
            if pid not in seen:
                combined_ids.append(pid)
                seen.add(pid)

        for pid in service_product_ids:
            if pid not in seen and len(combined_ids) < limit:
                combined_ids.append(pid)
                seen.add(pid)

        # Fetch full products
        products = self.product_service.get_base_query().filter(
            id__in=combined_ids[:limit]
        )

        # Maintain order
        product_dict = {p.id: p for p in products}
        ordered_products = [product_dict[pid] for pid in combined_ids[:limit] if pid in product_dict]

        return ordered_products

    def search_by_category(self, category, paginate=False):
        """
        Search products by category using ProductService method
        """
        return self.product_service.fetch_list(category=category, paginate=paginate)

    def search_by_subcategory(self, subcategory, paginate=False):
        """
        Search products by subcategory using ProductService method
        """
        return self.product_service.fetch_list(subcategory=subcategory, paginate=paginate)

    def search_by_vendor(self, vendor, paginate=False):
        """
        Search products by vendor using ProductService method
        """
        return self.product_service.fetch_list(vendor=vendor, paginate=paginate)


class HybridSearch:
    """
    Hybrid search that uses Elasticsearch for text search and
    ProductService for fetching full data
    """

    @staticmethod
    def search(request, query=None, category=None, brand=None,
               min_price=None, max_price=None, tags=None,
               in_stock=None, sort_by='relevance', page=1, page_size=20):
        """
        Main search method that combines both approaches
        """
        enhanced_search = EnhancedProductSearch(request)

        if query:
            # Use Elasticsearch for text search
            return enhanced_search.search_and_fetch_products(
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
        else:
            # Use ProductService for simple filtering
            from django.core.paginator import Paginator

            service = ProductService(request)
            products = service.fetch_list(
                category=category,
                paginate=False
            )

            # Apply additional filters
            if brand:
                products = products.filter(brand__name__iexact=brand)

            if min_price:
                products = products.filter(price__gte=min_price)

            if max_price:
                products = products.filter(price__lte=max_price)

            if in_stock:
                products = products.filter(stock__gt=0)

            # Sorting
            if sort_by == 'price_asc':
                products = products.order_by('price')
            elif sort_by == 'price_desc':
                products = products.order_by('-price')
            elif sort_by == 'newest':
                products = products.order_by('-created_at')
            elif sort_by == 'popular':
                products = products.order_by('-views', '-quantity_sold')

            # Paginate
            paginator = Paginator(products, page_size)
            page_obj = paginator.get_page(page)

            return {
                'total': paginator.count,
                'products': list(page_obj),
                'page': page,
                'page_size': page_size,
                'total_pages': paginator.num_pages
            }