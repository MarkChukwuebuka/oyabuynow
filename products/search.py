from elasticsearch_dsl import Q
from .documents import ProductDocument


class ProductSearch:
    """Handle product search operations"""

    @staticmethod
    def search_products(query=None):
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
                    'short_description',
                    'brand.name',
                    'category.name',
                    'tags.name',
                ],
                fuzziness='AUTO'
            )

        # Execute search
        response = s.execute()


        return [
            {
                'text': hit.name,
                'score': hit.meta.score,
                'product': hit.to_dict()
            }
            for hit in response.hits
        ]

    @staticmethod
    def autocomplete(query, size=10):
        """
        Autocomplete suggestions for product names

        Args:
            query: Partial search term
            size: Number of suggestions to return
        """
        s = ProductDocument.search()
        s = s.query(
            'match',
            name__suggest=query
        )[:size]

        s = s.query(
            'bool',
            should=[
                {'match': {'name__suggest': {'query': query, 'boost': 2}}},
                {'prefix': {'name.raw': {'value': query.lower(), 'boost': 3}}}
            ],
            minimum_should_match=1
        )

        response = s.execute()
        # suggestions = response.suggest.product_suggestions[0].options

        return [
            {
                'text': hit.name,
                'score': hit.meta.score,
                'product': hit.to_dict()
            }
            for hit in response.hits
        ]



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

