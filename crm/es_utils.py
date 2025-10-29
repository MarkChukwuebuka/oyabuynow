from elasticsearch import Elasticsearch
from django.conf import settings
from django_elasticsearch_dsl.registries import registry
from products.models import Product, Category, Brand


class ElasticsearchUtils:
    """
    Utility class for Elasticsearch operations and debugging
    """

    @staticmethod
    def get_es_client():
        """Get Elasticsearch client instance"""
        es_config = settings.ELASTICSEARCH_DSL['default']
        return Elasticsearch(hosts=es_config['hosts'])

    @staticmethod
    def check_connection():
        """
        Check if Elasticsearch is running and accessible
        Returns: dict with status and info
        """
        try:
            es = ElasticsearchUtils.get_es_client()
            info = es.info()
            return {
                'status': 'connected',
                'cluster_name': info['cluster_name'],
                'version': info['version']['number'],
                'message': 'Elasticsearch is running and accessible'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Cannot connect to Elasticsearch: {str(e)}'
            }

    @staticmethod
    def get_index_stats():
        """
        Get statistics for all indices
        Returns: dict with index statistics
        """
        try:
            es = ElasticsearchUtils.get_es_client()
            stats = {}

            # Get stats for each index
            indices = ['products', 'categories', 'brands']

            for index_name in indices:
                try:
                    count = es.count(index=index_name)
                    index_stats = es.indices.stats(index=index_name)

                    stats[index_name] = {
                        'document_count': count['count'],
                        'size': index_stats['indices'][index_name]['total']['store']['size_in_bytes'],
                        'size_human': ElasticsearchUtils._bytes_to_human(
                            index_stats['indices'][index_name]['total']['store']['size_in_bytes']
                        )
                    }
                except Exception as e:
                    stats[index_name] = {
                        'error': str(e),
                        'status': 'Index may not exist'
                    }

            return stats
        except Exception as e:
            return {'error': str(e)}

    @staticmethod
    def _bytes_to_human(bytes_value):
        """Convert bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} PB"

    @staticmethod
    def rebuild_all_indices(force=False):
        """
        Rebuild all Elasticsearch indices
        Use with caution - this deletes and recreates all indices
        """
        try:
            from django.core.management import call_command

            if force:
                call_command('search_index', '--rebuild', '-f')
                return {
                    'status': 'success',
                    'message': 'All indices rebuilt successfully'
                }
            else:
                return {
                    'status': 'warning',
                    'message': 'Set force=True to rebuild indices'
                }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error rebuilding indices: {str(e)}'
            }

    @staticmethod
    def delete_all_indices():
        """
        Delete all Elasticsearch indices
        Use with extreme caution!
        """
        try:
            es = ElasticsearchUtils.get_es_client()
            indices = ['products', 'categories', 'brands']
            deleted = []

            for index_name in indices:
                try:
                    es.indices.delete(index=index_name)
                    deleted.append(index_name)
                except Exception:
                    pass

            return {
                'status': 'success',
                'deleted_indices': deleted,
                'message': f'Deleted {len(deleted)} indices'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error deleting indices: {str(e)}'
            }

    @staticmethod
    def sync_database_to_index():
        """
        Sync all database records to Elasticsearch
        Useful after data imports or manual database changes
        """
        results = {
            'products': {'success': 0, 'errors': 0},
            'categories': {'success': 0, 'errors': 0},
            'brands': {'success': 0, 'errors': 0}
        }

        # Sync products
        for product in Product.objects.all():
            try:
                registry.update(product)
                results['products']['success'] += 1
            except Exception as e:
                results['products']['errors'] += 1
                print(f"Error syncing product {product.id}: {str(e)}")

        # Sync categories
        for category in Category.objects.all():
            try:
                registry.update(category)
                results['categories']['success'] += 1
            except Exception as e:
                results['categories']['errors'] += 1
                print(f"Error syncing category {category.id}: {str(e)}")

        # Sync brands
        for brand in Brand.objects.all():
            try:
                registry.update(brand)
                results['brands']['success'] += 1
            except Exception as e:
                results['brands']['errors'] += 1
                print(f"Error syncing brand {brand.id}: {str(e)}")

        return results

    @staticmethod
    def verify_product_in_index(product_id):
        """
        Verify if a specific product exists in the index
        Returns: dict with verification results
        """
        try:
            es = ElasticsearchUtils.get_es_client()
            result = es.get(index='products', id=product_id)

            return {
                'status': 'found',
                'document': result['_source'],
                'message': f'Product {product_id} exists in index'
            }
        except Exception as e:
            return {
                'status': 'not_found',
                'message': f'Product {product_id} not in index: {str(e)}'
            }

    @staticmethod
    def compare_db_vs_index():
        """
        Compare database counts with index counts
        Useful for verifying sync status
        """
        try:
            es = ElasticsearchUtils.get_es_client()

            comparison = {
                'products': {
                    'database': Product.objects.count(),
                    'index': es.count(index='products')['count']
                },
                'categories': {
                    'database': Category.objects.count(),
                    'index': es.count(index='categories')['count']
                },
                'brands': {
                    'database': Brand.objects.count(),
                    'index': es.count(index='brands')['count']
                }
            }

            # Add status for each
            for key in comparison:
                db_count = comparison[key]['database']
                idx_count = comparison[key]['index']
                comparison[key]['status'] = 'synced' if db_count == idx_count else 'out_of_sync'
                comparison[key]['difference'] = abs(db_count - idx_count)

            return comparison
        except Exception as e:
            return {'error': str(e)}

    @staticmethod
    def test_search(query="test"):
        """
        Run a simple test search
        Returns: search results
        """
        from .search import ProductSearch

        try:
            results = ProductSearch.search_products(query=query, page_size=5)
            return {
                'status': 'success',
                'total_results': results['total'],
                'returned': len(results['products']),
                'query': query
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }


# Django management command helper
def run_diagnostics():
    """
    Run full diagnostics on Elasticsearch setup
    Usage: from your_app.es_utils import run_diagnostics; run_diagnostics()
    """
    print("=" * 60)
    print("ELASTICSEARCH DIAGNOSTICS")
    print("=" * 60)

    # Check connection
    print("\n1. Connection Status:")
    connection = ElasticsearchUtils.check_connection()
    print(f"   Status: {connection['status']}")
    print(f"   Message: {connection['message']}")

    # Index statistics
    print("\n2. Index Statistics:")
    stats = ElasticsearchUtils.get_index_stats()
    for index_name, index_stats in stats.items():
        print(f"\n   {index_name.upper()}:")
        if 'error' in index_stats:
            print(f"     Error: {index_stats['error']}")
        else:
            print(f"     Documents: {index_stats.get('document_count', 'N/A')}")
            print(f"     Size: {index_stats.get('size_human', 'N/A')}")

    # Database vs Index comparison
    print("\n3. Database vs Index Comparison:")
    comparison = ElasticsearchUtils.compare_db_vs_index()
    if 'error' not in comparison:
        for model, counts in comparison.items():
            print(f"\n   {model.upper()}:")
            print(f"     Database: {counts['database']}")
            print(f"     Index: {counts['index']}")
            print(f"     Status: {counts['status']}")
            if counts['difference'] > 0:
                print(f"     Difference: {counts['difference']} records")

    # Test search
    print("\n4. Test Search:")
    test = ElasticsearchUtils.test_search()
    print(f"   Status: {test['status']}")
    if test['status'] == 'success':
        print(f"   Total Results: {test['total_results']}")
        print(f"   Returned: {test['returned']}")
    else:
        print(f"   Message: {test.get('message', 'Unknown error')}")

    print("\n" + "=" * 60)
    print("DIAGNOSTICS COMPLETE")
    print("=" * 60)