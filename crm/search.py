from elasticsearch_dsl import Q
from .documents import ProductDocument, CategoryDocument, BrandDocument


class ProductSearch:
    """Handle product search operations"""

    @staticmethod
    def search_products(query=None, category=None, brand=None,
                        min_price=None, max_price=None,
                        tags=None, in_stock=None,
                        sort_by='relevance', page=1, page_size=20):
        """
        Advanced product search with filters

        Args:
            query: Search query string
            category: Category ID or name
            brand: Brand ID or name
            min_price: Minimum price filter
            max_price: Maximum price filter
            tags: List of tag names
            in_stock: Boolean to filter in-stock products
            sort_by: Sort option ('relevance', 'price_asc', 'price_desc', 'newest')
            page: Page number
            page_size: Items per page
        """
        s = ProductDocument.search()

        # Text search query
        if query:
            s = s.query(
                'multi_match',
                query=query,
                fields=[
                    'name^3',  # Boost name field
                    'description^2',
                    'short_description^2',
                    'brand.name',
                    'category.name',
                    'tags.name',
                    'sku'
                ],
                fuzziness='AUTO'
            )

        # Apply filters
        filters = []

        if category:
            if isinstance(category, int):
                filters.append(Q('term', category__id=category))
            else:
                filters.append(Q('match', category__name=category))

        if brand:
            if isinstance(brand, int):
                filters.append(Q('term', brand__id=brand))
            else:
                filters.append(Q('match', brand__name=brand))

        if min_price is not None:
            filters.append(Q('range', price={'gte': min_price}))

        if max_price is not None:
            filters.append(Q('range', price={'lte': max_price}))

        if tags:
            for tag in tags:
                filters.append(Q('nested',
                                 path='tags',
                                 query=Q('match', tags__name=tag)
                                 ))

        if in_stock:
            filters.append(Q('range', stock={'gt': 0}))

        # Apply all filters
        if filters:
            s = s.query('bool', filter=filters)

        # Sorting
        if sort_by == 'price_asc':
            s = s.sort('price')
        elif sort_by == 'price_desc':
            s = s.sort('-price')
        elif sort_by == 'newest':
            s = s.sort('-created_at')
        # Default is relevance (no sort needed)

        # Pagination
        start = (page - 1) * page_size
        s = s[start:start + page_size]

        # Execute search
        response = s.execute()

        return {
            'total': response.hits.total.value,
            'products': [hit.to_dict() for hit in response],
            'page': page,
            'page_size': page_size,
            'total_pages': (response.hits.total.value + page_size - 1) // page_size
        }

    @staticmethod
    def autocomplete(query, size=10):
        """
        Autocomplete suggestions for product names

        Args:
            query: Partial search term
            size: Number of suggestions to return
        """
        s = ProductDocument.search()
        s = s.suggest(
            'product_suggestions',
            query,
            completion={'field': 'name_suggest', 'size': size}
        )

        response = s.execute()
        suggestions = response.suggest.product_suggestions[0].options

        return [
            {
                'text': option.text,
                'score': option._score,
                'product': option._source.to_dict()
            }
            for option in suggestions
        ]


    @staticmethod
    def get_facets(query=None):
        """
        Get aggregations/facets for filters

        Args:
            query: Optional search query to filter facets
        """
        s = ProductDocument.search()

        if query:
            s = s.query(
                'multi_match',
                query=query,
                fields=['name', 'description']
            )

        # Add aggregations
        s.aggs.bucket('categories', 'terms', field='category.name.keyword', size=50)
        s.aggs.bucket('brands', 'terms', field='brand.name.keyword', size=50)
        s.aggs.bucket('tags', 'nested', path='tags').bucket(
            'tag_names', 'terms', field='tags.name.keyword', size=50
        )
        s.aggs.metric('price_stats', 'stats', field='price')

        s = s[:0]  # Don't return documents, only aggregations
        response = s.execute()

        return {
            'categories': [
                {'name': b.key, 'count': b.doc_count}
                for b in response.aggregations.categories.buckets
            ],
            'brands': [
                {'name': b.key, 'count': b.doc_count}
                for b in response.aggregations.brands.buckets
            ],
            'tags': [
                {'name': b.key, 'count': b.doc_count}
                for b in response.aggregations.tags.tag_names.buckets
            ],
            'price_range': {
                'min': response.aggregations.price_stats.min,
                'max': response.aggregations.price_stats.max,
                'avg': response.aggregations.price_stats.avg,
            }
        }

    @staticmethod
    def similar_products(product_id, size=5):
        """
        Find similar products using More Like This query

        Args:
            product_id: ID of the product to find similar items for
            size: Number of similar products to return
        """
        s = ProductDocument.search()
        s = s.query(
            'more_like_this',
            fields=['name', 'description', 'category.name', 'tags.name'],
            like=[{'_id': product_id}],
            min_term_freq=1,
            max_query_terms=12
        )
        s = s[:size]

        response = s.execute()
        return [hit.to_dict() for hit in response]


class CategorySearch:
    """Handle category search operations"""

    @staticmethod
    def search_categories(query=None):
        """Search categories"""
        s = CategoryDocument.search()

        if query:
            s = s.query('match', name=query)

        s = s.sort('-product_count')
        response = s.execute()

        return [hit.to_dict() for hit in response]


class BrandSearch:
    """Handle brand search operations"""

    @staticmethod
    def search_brands(query=None):
        """Search brands"""
        s = BrandDocument.search()

        if query:
            s = s.query('match', name=query)

        s = s.sort('-product_count')
        response = s.execute()

        return [hit.to_dict() for hit in response]