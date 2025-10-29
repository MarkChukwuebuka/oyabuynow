from django.http import JsonResponse
from elasticsearch_dsl import Q
from search.documents import ProductDocument, CategoryDocument, BrandDocument, TagDocument

def autocomplete_search(request):
    query = request.GET.get("q", "").strip()
    size = int(request.GET.get("size", 5))

    if not query:
        return JsonResponse({"success": True, "suggestions": []})

    suggestions = []

    # Product Search
    product_query = Q("multi_match", query=query, fields=["name^3", "description", "category", "brand", "tags"])
    product_results = ProductDocument.search().query(product_query)[:size]
    for hit in product_results:
        suggestions.append({
            "type": "product",
            "text": hit.name,
            "product": {
                "id": hit.meta.id,
                "slug": hit.slug,
                "name": hit.name,
                "category": {"name": hit.category},
                "price": hit.price,
                "discounted_price": hit.discounted_price,
                "product_media": []  # you can append media here if needed
            }
        })

    # Category suggestions
    cat_results = CategoryDocument.search().query("match", name=query)[:size]
    for hit in cat_results:
        suggestions.append({
            "type": "category",
            "text": hit.name,
            "product": {
                "id": None,
                "slug": "",
                "name": hit.name,
                "category": {"name": hit.name},
                "price": None,
                "discounted_price": None,
                "product_media": []
            }
        })

    # Brand suggestions
    brand_results = BrandDocument.search().query("match", name=query)[:size]
    for hit in brand_results:
        suggestions.append({
            "type": "brand",
            "text": hit.name,
            "product": {
                "id": None,
                "slug": "",
                "name": hit.name,
                "category": {"name": "Brand"},
                "price": None,
                "discounted_price": None,
                "product_media": []
            }
        })

    # Tag suggestions
    tag_results = TagDocument.search().query("match", name=query)[:size]
    for hit in tag_results:
        suggestions.append({
            "type": "tag",
            "text": hit.name,
            "product": {
                "id": None,
                "slug": "",
                "name": hit.name,
                "category": {"name": "Tag"},
                "price": None,
                "discounted_price": None,
                "product_media": []
            }
        })

    # Remove duplicates by text
    seen = set()
    unique_suggestions = []
    for s in suggestions:
        if s["text"].lower() not in seen:
            seen.add(s["text"].lower())
            unique_suggestions.append(s)

    return JsonResponse({
        "success": True,
        "suggestions": unique_suggestions[:size]
    })
