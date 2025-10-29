"""
Advanced Autocomplete Methods for Better Search Experience
"""

from elasticsearch_dsl import Q
from .documents import ProductDocument


class AdvancedAutocomplete:
    """
    Advanced autocomplete with multiple search strategies
    """

    @staticmethod
    def autocomplete_ngram(query, size=10):
        """
        N-gram based autocomplete - matches anywhere in the text
        Works with your ngram_analyzer defined in ProductDocument

        This will match:
        - "lap" in "dell laptop"
        - "top" in "desktop"
        - "sam" in "samsung"
        """
        s = ProductDocument.search()

        # Use the ngram analyzer fields
        s = s.query(
            'multi_match',
            query=query,
            fields=[
                'name^3',  # Uses ngram_analyzer
                'description^2',
                'short_description^2',
                'brand.name',
                'category.name'
            ],
            operator='and'  # All terms must match
        )

        s = s[:size]
        response = s.execute()

        return AdvancedAutocomplete._format_results(response)

    @staticmethod
    def autocomplete_wildcard(query, size=10):
        """
        Wildcard based autocomplete - most flexible but slower
        Matches partial words anywhere in the text

        This will match:
        - "lap" in "dell laptop"
        - "sam" in "samsung galaxy"
        """
        s = ProductDocument.search()

        # Clean query and add wildcards
        clean_query = query.strip().lower()
        wildcard_query = f'*{clean_query}*'

        s = s.query(
            'query_string',
            query=wildcard_query,
            fields=['name^3', 'description^2', 'brand.name', 'category.name'],
            analyze_wildcard=False  # Don't analyze the wildcard
        )

        s = s[:size]
        response = s.execute()

        return AdvancedAutocomplete._format_results(response)

    @staticmethod
    def autocomplete_combined(query, size=10):
        """
        Combined autocomplete using multiple strategies for best results

        Uses:
        1. Phrase prefix (for "dell la..." matching "dell laptop")
        2. N-gram match (for "lap" matching "laptop")
        3. Wildcard (fallback for partial matches)

        This gives the most comprehensive results
        """
        s = ProductDocument.search()

        # Build a compound query with multiple strategies
        should_queries = [
            # Strategy 1: Phrase prefix - highest boost
            Q('multi_match',
              query=query,
              fields=['name^5', 'brand.name^3'],
              type='phrase_prefix',
              boost=3.0
              ),

            # Strategy 2: N-gram match for partial words
            Q('multi_match',
              query=query,
              fields=['name^3', 'description^2', 'brand.name^2'],
              operator='and',
              boost=2.0
              ),

            # Strategy 3: Fuzzy match for typos
            Q('multi_match',
              query=query,
              fields=['name^2', 'brand.name'],
              fuzziness='AUTO',
              boost=1.0
              ),
        ]

        # Combine all strategies
        s = s.query('bool', should=should_queries, minimum_should_match=1)

        # Boost popular products
        s = s.query('function_score',
                    query=s.query,
                    functions=[
                        {'field_value_factor': {
                            'field': 'views',
                            'factor': 0.1,
                            'modifier': 'log1p',
                            'missing': 1
                        }},
                        {'field_value_factor': {
                            'field': 'quantity_sold',
                            'factor': 0.2,
                            'modifier': 'log1p',
                            'missing': 1
                        }}
                    ],
                    score_mode='sum',
                    boost_mode='multiply'
                    )

        s = s[:size]
        response = s.execute()

        return AdvancedAutocomplete._format_results(response)

    @staticmethod
    def autocomplete_word_start(query, size=10):
        """
        Match only at the start of words (traditional autocomplete)

        This will match:
        - "lap" in "dell laptop" (because "lap" starts "laptop")
        - "sam" in "samsung"

        But NOT:
        - "top" in "laptop" (because "top" doesn't start a word)
        """
        s = ProductDocument.search()

        s = s.query(
            'multi_match',
            query=query,
            fields=['name^3', 'description^2', 'brand.name'],
            type='phrase_prefix'
        )

        s = s[:size]
        response = s.execute()

        return AdvancedAutocomplete._format_results(response)

    @staticmethod
    def _format_results(response):
        """
        Format Elasticsearch results into consistent structure
        """
        suggestions = []

        for hit in response:
            # Get first product image
            product_media = getattr(hit, 'product_media', [])
            first_image = product_media[0]['image'] if product_media else None

            # Get brand info
            brand_info = None
            if hasattr(hit, 'brand') and hit.brand:
                brand_info = {
                    'id': hit.brand.get('id'),
                    'name': hit.brand.get('name')
                } if isinstance(hit.brand, dict) else None

            # Get category info
            category_info = None
            if hasattr(hit, 'category') and hit.category:
                category_info = {
                    'id': hit.category.get('id'),
                    'name': hit.category.get('name')
                } if isinstance(hit.category, dict) else None

            suggestions.append({
                'text': hit.name,
                'score': hit.meta.score,
                'product': {
                    'id': hit.meta.id,
                    'name': hit.name,
                    'slug': getattr(hit, 'slug', ''),
                    'price': float(hit.price),
                    'discounted_price': float(getattr(hit, 'discounted_price', hit.price)),
                    'percentage_discount': getattr(hit, 'percentage_discount', None),
                    'stock': getattr(hit, 'stock', 0),
                    'views': getattr(hit, 'views', 0),
                    'quantity_sold': getattr(hit, 'quantity_sold', 0),
                    'rating': float(getattr(hit, 'rating', 0)),
                    'cover_image': first_image,
                    'brand': brand_info,
                    'category': category_info,
                }
            })

        return suggestions


# Update ProductSearch class to use the best autocomplete method
class ProductSearch:
    """Handle product search operations with advanced autocomplete"""

    @staticmethod
    def autocomplete(query, size=10, method='combined'):
        """
        Autocomplete with multiple strategies

        Args:
            query: Search term
            size: Number of results
            method: 'combined' (best), 'ngram', 'wildcard', 'word_start'

        Returns:
            List of suggestion dicts
        """
        if not query or len(query.strip()) < 2:
            return []

        # Choose autocomplete method
        if method == 'ngram':
            return AdvancedAutocomplete.autocomplete_ngram(query, size)
        elif method == 'wildcard':
            return AdvancedAutocomplete.autocomplete_wildcard(query, size)
        elif method == 'word_start':
            return AdvancedAutocomplete.autocomplete_word_start(query, size)
        else:  # combined (default and best)
            return AdvancedAutocomplete.autocomplete_combined(query, size)