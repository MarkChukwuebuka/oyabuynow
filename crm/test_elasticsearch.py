"""
Elasticsearch Testing Script

Run this in Django shell:
python manage.py shell
>>> from your_app.test_elasticsearch import *
>>> run_all_tests()

Or run individual tests:
>>> test_connection()
>>> test_product_indexing()
>>> etc.
"""

from django.db import transaction
from .models import Product, Category, Brand, Tag, Subcategory
from .search import ProductSearch
from .es_utils import ElasticsearchUtils
from django_elasticsearch_dsl.registries import registry


def test_connection():
    """Test 1: Elasticsearch Connection"""
    print("\n" + "=" * 60)
    print("TEST 1: Elasticsearch Connection")
    print("=" * 60)

    result = ElasticsearchUtils.check_connection()

    if result['status'] == 'connected':
        print("✓ SUCCESS: Connected to Elasticsearch")
        print(f"  Cluster: {result['cluster_name']}")
        print(f"  Version: {result['version']}")
        return True
    else:
        print("✗ FAILED: Cannot connect to Elasticsearch")
        print(f"  Error: {result['message']}")
        return False


def test_index_stats():
    """Test 2: Index Statistics"""
    print("\n" + "=" * 60)
    print("TEST 2: Index Statistics")
    print("=" * 60)

    stats = ElasticsearchUtils.get_index_stats()

    for index_name, index_stats in stats.items():
        print(f"\n{index_name.upper()}:")
        if 'error' in index_stats:
            print(f"  ✗ Error: {index_stats['error']}")
        else:
            print(f"  ✓ Documents: {index_stats['document_count']}")
            print(f"  ✓ Size: {index_stats['size_human']}")

    return True


def test_product_indexing():
    """Test 3: Product Create/Update/Delete"""
    print("\n" + "=" * 60)
    print("TEST 3: Product Indexing (Create/Update/Delete)")
    print("=" * 60)

    try:
        # Create test category
        category = Category.objects.create(name="Test Category ES")
        print("✓ Created test category")

        # Create test brand
        brand = Brand.objects.create(name="Test Brand ES")
        print("✓ Created test brand")

        # Create test product
        product = Product.objects.create(
            name="Test Product ES",
            slug="test-product-es",
            category=category,
            brand=brand,
            price=99.99,
            stock=10,
            description="This is a test product for Elasticsearch"
        )
        print("✓ Created test product")

        # Verify product in index
        import time
        time.sleep(1)  # Wait for indexing

        verify_result = ElasticsearchUtils.verify_product_in_index(product.id)
        if verify_result['status'] == 'found':
            print("✓ Product found in Elasticsearch index")
        else:
            print("✗ Product NOT found in index")
            print(f"  Error: {verify_result['message']}")

        # Update product
        product.name = "Updated Test Product ES"
        product.price = 149.99
        product.save()
        print("✓ Updated test product")

        time.sleep(1)  # Wait for re-indexing

        # Search for updated product
        search_results = ProductSearch.search_products(query="Updated Test Product")
        if search_results['total'] > 0:
            print("✓ Updated product found in search")
        else:
            print("✗ Updated product NOT found in search")

        # Clean up
        product.delete()
        category.delete()
        brand.delete()
        print("✓ Cleaned up test data")

        return True

    except Exception as e:
        print(f"✗ FAILED: {str(e)}")
        # Try to clean up on error
        try:
            Product.objects.filter(slug="test-product-es").delete()
            Category.objects.filter(name="Test Category ES").delete()
            Brand.objects.filter(name="Test Brand ES").delete()
        except:
            pass
        return False


def test_search_functionality():
    """Test 4: Search Functionality"""
    print("\n" + "=" * 60)
    print("TEST 4: Search Functionality")
    print("=" * 60)

    try:
        # Test basic search
        results = ProductSearch.search_products(query="", page=1, page_size=5)
        print(f"✓ Basic search returned {results['total']} products")

        # Test search with filters
        if Category.objects.exists():
            first_category = Category.objects.first()
            results = ProductSearch.search_products(
                category=first_category.id,
                page_size=5
            )
            print(f"✓ Category filter search returned {results['total']} products")

        # Test price range filter
        results = ProductSearch.search_products(
            min_price=0,
            max_price=1000,
            page_size=5
        )
        print(f"✓ Price range search returned {results['total']} products")

        # Test sorting
        results = ProductSearch.search_products(
            sort_by="price_asc",
            page_size=5
        )
        print(f"✓ Sorted search returned {results['total']} products")

        return True

    except Exception as e:
        print(f"✗ FAILED: {str(e)}")
        return False


def test_autocomplete():
    """Test 5: Autocomplete Functionality"""
    print("\n" + "=" * 60)
    print("TEST 5: Autocomplete")
    print("=" * 60)

    try:
        # Get first product name for testing
        if Product.objects.exists():
            product = Product.objects.first()
            # Use first 3 characters of product name
            query = product.name[:3] if len(product.name) >= 3 else product.name

            suggestions = ProductSearch.autocomplete(query, size=5)
            print(f"✓ Autocomplete for '{query}' returned {len(suggestions)} suggestions")

            if suggestions:
                print(f"  First suggestion: {suggestions[0]['text']}")
        else:
            print("⚠ No products in database to test autocomplete")

        return True

    except Exception as e:
        print(f"✗ FAILED: {str(e)}")
        return False


def test_facets():
    """Test 6: Facets/Aggregations"""
    print("\n" + "=" * 60)
    print("TEST 6: Facets and Aggregations")
    print("=" * 60)

    try:
        facets = ProductSearch.get_facets()

        print(f"✓ Found {len(facets.get('categories', []))} category facets")
        print(f"✓ Found {len(facets.get('brands', []))} brand facets")
        print(f"✓ Found {len(facets.get('tags', []))} tag facets")

        price_range = facets.get('price_range', {})
        if price_range:
            print(f"✓ Price range: ${price_range.get('min', 0):.2f} - ${price_range.get('max', 0):.2f}")

        return True

    except Exception as e:
        print(f"✗ FAILED: {str(e)}")
        return False


def test_similar_products():
    """Test 7: Similar Products"""
    print("\n" + "=" * 60)
    print("TEST 7: Similar Products")
    print("=" * 60)

    try:
        if Product.objects.exists():
            product = Product.objects.first()
            similar = ProductSearch.similar_products(product.id, size=5)

            print(f"✓ Found {len(similar)} similar products for '{product.name}'")

            if similar:
                print(f"  First similar product: {similar[0].get('name', 'N/A')}")
        else:
            print("⚠ No products in database to test similarity")

        return True

    except Exception as e:
        print(f"✗ FAILED: {str(e)}")
        return False


def test_manytomany_signals():
    """Test 8: ManyToMany Signal Updates"""
    print("\n" + "=" * 60)
    print("TEST 8: ManyToMany Signal Updates")
    print("=" * 60)

    try:
        # Create test data
        category = Category.objects.create(name="Test ManyToMany Category")
        product = Product.objects.create(
            name="Test ManyToMany Product",
            slug="test-m2m-product",
            category=category,
            price=50.00
        )

        tag1 = Tag.objects.create(name="Test Tag 1")
        tag2 = Tag.objects.create(name="Test Tag 2")

        # Add tags
        product.tags.add(tag1, tag2)
        print("✓ Added tags to product")

        import time
        time.sleep(1)

        # Verify tags in index
        verify = ElasticsearchUtils.verify_product_in_index(product.id)
        if verify['status'] == 'found':
            tags_in_index = verify['document'].get('tags', [])
            if len(tags_in_index) == 2:
                print("✓ Tags correctly indexed")
            else:
                print(f"✗ Expected 2 tags, found {len(tags_in_index)}")

        # Remove a tag
        product.tags.remove(tag1)
        print("✓ Removed tag from product")

        time.sleep(1)

        # Verify update
        verify = ElasticsearchUtils.verify_product_in_index(product.id)
        if verify['status'] == 'found':
            tags_in_index = verify['document'].get('tags', [])
            if len(tags_in_index) == 1:
                print("✓ Tag removal correctly indexed")
            else:
                print(f"✗ Expected 1 tag, found {len(tags_in_index)}")

        # Clean up
        product.delete()
        category.delete()
        tag1.delete()
        tag2.delete()
        print("✓ Cleaned up test data")

        return True

    except Exception as e:
        print(f"✗ FAILED: {str(e)}")
        # Clean up on error
        try:
            Product.objects.filter(slug="test-m2m-product").delete()
            Category.objects.filter(name="Test ManyToMany Category").delete()
            Tag.objects.filter(name__startswith="Test Tag").delete()
        except:
            pass
        return False


def test_related_model_updates():
    """Test 9: Related Model Updates"""
    print("\n" + "=" * 60)
    print("TEST 9: Related Model Updates")
    print("=" * 60)

    try:
        # Create test data
        category = Category.objects.create(name="Test Related Category")
        brand = Brand.objects.create(name="Test Related Brand")

        product = Product.objects.create(
            name="Test Related Product",
            slug="test-related-product",
            category=category,
            brand=brand,
            price=100.00
        )

        import time
        time.sleep(1)

        # Update category name
        old_category_name = category.name
        category.name = "Updated Related Category"
        category.save()
        print("✓ Updated category name")

        time.sleep(1)

        # Verify product has updated category
        verify = ElasticsearchUtils.verify_product_in_index(product.id)
        if verify['status'] == 'found':
            category_in_index = verify['document'].get('category', {})
            if category_in_index.get('name') == "Updated Related Category":
                print("✓ Product correctly updated with new category name")
            else:
                print(f"✗ Category name not updated in product index")

        # Update brand name
        brand.name = "Updated Related Brand"
        brand.save()
        print("✓ Updated brand name")

        time.sleep(1)

        # Verify product has updated brand
        verify = ElasticsearchUtils.verify_product_in_index(product.id)
        if verify['status'] == 'found':
            brand_in_index = verify['document'].get('brand', {})
            if brand_in_index.get('name') == "Updated Related Brand":
                print("✓ Product correctly updated with new brand name")
            else:
                print(f"✗ Brand name not updated in product index")

        # Clean up
        product.delete()
        category.delete()
        brand.delete()
        print("✓ Cleaned up test data")

        return True

    except Exception as e:
        print(f"✗ FAILED: {str(e)}")
        # Clean up on error
        try:
            Product.objects.filter(slug="test-related-product").delete()
            Category.objects.filter(name__contains="Related Category").delete()
            Brand.objects.filter(name__contains="Related Brand").delete()
        except:
            pass
        return False


def test_db_vs_index_sync():
    """Test 10: Database vs Index Sync"""
    print("\n" + "=" * 60)
    print("TEST 10: Database vs Index Synchronization")
    print("=" * 60)

    comparison = ElasticsearchUtils.compare_db_vs_index()

    if 'error' in comparison:
        print(f"✗ FAILED: {comparison['error']}")
        return False

    all_synced = True

    for model, counts in comparison.items():
        status_symbol = "✓" if counts['status'] == 'synced' else "✗"
        print(f"{status_symbol} {model.upper()}:")
        print(f"    Database: {counts['database']}")
        print(f"    Index: {counts['index']}")
        print(f"    Status: {counts['status']}")

        if counts['status'] != 'synced':
            all_synced = False
            print(f"    Difference: {counts['difference']} records")

    if all_synced:
        print("\n✓ All indices are in sync with database")
    else:
        print("\n⚠ Some indices are out of sync. Run sync_database_to_index() to fix.")

    return all_synced


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("ELASTICSEARCH COMPREHENSIVE TEST SUITE")
    print("=" * 60)

    tests = [
        ("Connection Test", test_connection),
        ("Index Statistics", test_index_stats),
        ("Product Indexing", test_product_indexing),
        ("Search Functionality", test_search_functionality),
        ("Autocomplete", test_autocomplete),
        ("Facets", test_facets),
        ("Similar Products", test_similar_products),
        ("ManyToMany Signals", test_manytomany_signals),
        ("Related Model Updates", test_related_model_updates),
        ("DB vs Index Sync", test_db_vs_index_sync),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} crashed: {str(e)}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status}: {test_name}")

    print("\n" + "-" * 60)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("✓ ALL TESTS PASSED!")
    else:
        print(f"⚠ {total - passed} test(s) failed")

    print("=" * 60)

    return passed == total


# Quick test helpers
def quick_test():
    """Run quick essential tests only"""
    print("\nRunning quick tests...")
    test_connection()
    test_product_indexing()
    test_search_functionality()
    print("\nQuick tests complete!")


def fix_sync_issues():
    """Helper to fix synchronization issues"""
    print("\nFixing synchronization issues...")
    print("This will sync all database records to Elasticsearch...")

    confirm = input("Continue? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Cancelled.")
        return

    results = ElasticsearchUtils.sync_database_to_index()

    print("\nSync Results:")
    for model, counts in results.items():
        print(f"{model.upper()}:")
        print(f"  Success: {counts['success']}")
        print(f"  Errors: {counts['errors']}")

    print("\nSync complete!")


# Usage instructions
def print_usage():
    """Print usage instructions"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║          ELASTICSEARCH TESTING SCRIPT - USAGE                ║
╚══════════════════════════════════════════════════════════════╝

To use this script, run in Django shell:
    python manage.py shell

Then import and run:
    >>> from your_app.test_elasticsearch import *
    >>> run_all_tests()          # Run all tests
    >>> quick_test()             # Run essential tests only

Individual tests:
    >>> test_connection()        # Test ES connection
    >>> test_product_indexing()  # Test product CRUD
    >>> test_search_functionality()
    >>> test_autocomplete()
    >>> test_facets()
    >>> test_similar_products()
    >>> test_manytomany_signals()
    >>> test_related_model_updates()
    >>> test_db_vs_index_sync()

Utilities:
    >>> fix_sync_issues()        # Fix DB/Index sync
    >>> from your_app.es_utils import run_diagnostics
    >>> run_diagnostics()        # Run full diagnostics

╚══════════════════════════════════════════════════════════════╝
    """)


# Auto-print usage when imported
print_usage()