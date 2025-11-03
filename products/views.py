import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from accounts.services.vendor_service import VendorService
from products.models import Wishlist, Subcategory
from products.services.category_brand_service import CategoryService, ColorService, BrandService, TagService, \
    SubcategoryService
from products.services.product_service import ProductService
from products.services.review_service import ProductReviewService
from products.services.wishlist_service import WishlistService
from services.util import CustomRequestUtil, vendor_required


class VendorProductView(View, CustomRequestUtil):
    template_name = "frontend/vendor-product-detail.html"
    context_object_name = 'product'
    template_on_error = "frontend/vendor-product-detail.html"

    @vendor_required
    def get(self, request, *args, **kwargs):
        product_service = ProductService(self.request)
        product, _ = product_service.fetch_single_by_slug(kwargs.get("product_slug"))

        self.extra_context_data = {
            "title": f"{product.name}",
        }
        return self.process_request(
            request, target_function=product_service.fetch_single_by_slug, product_slug=kwargs.get("product_slug")
        )


class RetrieveProductView(View, CustomRequestUtil):
    template_name = "frontend/product-detail.html"
    context_object_name = 'product'
    template_on_error = "frontend/product-detail.html"

    def get(self, request, *args, **kwargs):
        product_service = ProductService(self.request)
        product, error = product_service.fetch_single_by_slug(kwargs.get("product_slug"))

        related_products = product_service.get_related_products(product.id)[:5]
        ratings_data = product_service.fetch_product_ratings(product.id)
        avg_rating = round(ratings_data.get('avg_rating', 0), 1)
        trending_products = product_service.fetch_list().order_by("-views").exclude(id=product.id)[:5]
        reviews = product.reviews.all().order_by('-created_at')[:3]

        product_service.update_product_views(product)

        self.extra_context_data = {
            "title": product.name,
            "related_products": related_products,
            'ratings_data': {**ratings_data, 'avg_rating': avg_rating},
            'rating_range': range(1, 6),
            'trending_products': trending_products,
            'reviews': reviews,
        }

        if self.auth_user:
            in_wishlist = Wishlist.objects.filter(user=self.auth_user, product=product).exists()
            self.extra_context_data['in_wishlist'] = in_wishlist

        return self.process_request(
            request, target_function=product_service.fetch_single_by_slug, product_slug=kwargs.get("product_slug")
        )

    def post(self, request, *args, **kwargs):
        product_id = request.POST.get('product_id')
        rating = request.POST.get('rating')
        review = request.POST.get('review')

        product_service = ProductService(self.request)
        product, error = product_service.fetch_single(product_id)

        self.extra_context_data = {
            "title": product.name,
            'product':product,
        }

        payload = {
            "rating": rating,
            "review": review,
            "product": product,
        }

        product_review_service = ProductReviewService(self.request)

        return self.process_request(
            request, target_function=product_review_service.create_single,
            target_view="product-detail", payload=payload
        )


class ListProductView(View, CustomRequestUtil):
    extra_context_data = {
        "title": "Our Shop"
    }

    def get(self, request, *args, **kwargs):
        self.template_name = "frontend/product-list.html"
        self.context_object_name = 'page_obj'

        category = kwargs.get('category_name', None)
        subcategory = kwargs.get('subcategory_name', None)
        if category:
            self.extra_context_data['title'] = f"{category}"
        if subcategory:
            self.extra_context_data['title'] = f"{subcategory}"
        product_service = ProductService(self.request)


        return self.process_request(
            request, target_function=product_service.fetch_list,
            category=category, subcategory=subcategory, paginate=True
        )


class ListProductByVendorView(View, CustomRequestUtil):

    def get(self, request, *args, **kwargs):
        self.template_name = "frontend/vendor-shop.html"
        self.context_object_name = 'page_obj'
        self.view_on_error = 'home'

        vendor_id = kwargs.get('vendor_id', None)
        vendor_service  = VendorService(request)
        vendor, error = vendor_service.fetch_single(vendor_id)

        if vendor:
            self.extra_context_data = {
                'title': f"{vendor.store_name}'s Products",
                'vendor': vendor
            }

        return self.process_request(
            request, target_function=vendor_service.fetch_vendor_products,
            vendor_id=vendor_id
        )




class CreateProductView(View, CustomRequestUtil):
    extra_context_data = {
        "title": "Add Product"
    }

    template_name = "backend/add-new-product.html"

    def get(self, request, *args, **kwargs):
        color_service = ColorService(request)
        brand_service = BrandService(request)
        tag_service = TagService(request)

        self.extra_context_data["colors"] = color_service.fetch_list()
        self.extra_context_data["brands"] = brand_service.fetch_list()
        self.extra_context_data["tags"] = tag_service.fetch_list()

        return self.process_request(
            request, target_view="add-product"
        )

    def post(self, request, *args, **kwargs):
        self.template_on_error = "backend/add-new-product.html"
        subcategory_service = SubcategoryService(request)
        tag_service = TagService(request)
        color_service = ColorService(request)
        brand_service = BrandService(request)
        category_service = CategoryService(request)
        product_service = ProductService(request)

        payload = {
            'name' : request.POST.get('name'),
            'price' : request.POST.get('price'),
            'percentage_discount' : request.POST.get('percentage_discount', None),
            'short_description' : request.POST.get('short_description'),
            'description' : request.POST.get('description'),
            'stock' : request.POST.get('stock'),
            'weight' : request.POST.get('weight'),
            'sale_start' : request.POST.get('sale_start'),
            'dimensions' : request.POST.get('dimensions'),
            'sale_end' : request.POST.get('sale_end'),
            'add_product_to_sales' : request.POST.get('add_product_to_sales'),
            'sizes' : request.POST.get('sizes'),
        }

        subcategory_ids = request.POST.getlist('subcategories')
        if subcategory_ids:
            payload['subcategories'] = subcategory_service.fetch_by_ids(subcategory_ids)

        tag_ids = request.POST.getlist('tags')
        if tag_ids:
            payload['tags'] = tag_service.fetch_by_ids(tag_ids)

        color_ids = request.POST.getlist('colors')
        if color_ids:
            payload['colors'] = color_service.fetch_by_ids(color_ids)

        brand_id = request.POST.get('brand')
        if brand_id:
            payload['brand'], _ = brand_service.fetch_single_by_id(brand_id)

        category_id = request.POST.get('category')
        if category_id:
            payload['category'], _ = category_service.fetch_single_by_id(category_id)

        payload['media'] = request.FILES.getlist('media')


        return self.process_request(
            request, target_function=product_service.create_single,
            target_view="add-product", payload=payload
        )



class UpdateDeleteProductView(View, CustomRequestUtil):
    extra_context_data = {
        "title": "Update Product"
    }

    def get(self, request, *args, **kwargs):
        self.template_name = "backend/update-product.html"
        self.context_object_name = "product"
        color_service = ColorService(request)
        brand_service = BrandService(request)
        tag_service = TagService(request)
        product_service = ProductService(request)

        self.extra_context_data["colors"] = color_service.fetch_list()
        self.extra_context_data["brands"] = brand_service.fetch_list()
        self.extra_context_data["tags"] = tag_service.fetch_list()

        return self.process_request(
            request, target_view="update-product", target_function=product_service.fetch_single,
            product_id=kwargs.get("product_id")
        )

    def post(self, request, *args, **kwargs):
        self.template_on_error = "backend/add-new-product.html"
        subcategory_service = SubcategoryService(request)
        tag_service = TagService(request)
        color_service = ColorService(request)
        brand_service = BrandService(request)
        category_service = CategoryService(request)
        product_service = ProductService(request)

        payload = {
            'name' : request.POST.get('name'),
            'price' : request.POST.get('price'),
            'percentage_discount' : request.POST.get('percentage_discount', None),
            'short_description' : request.POST.get('short_description'),
            'description' : request.POST.get('description'),
            'stock' : request.POST.get('stock'),
            'weight' : request.POST.get('weight'),
            'sale_start' : request.POST.get('sale_start'),
            'dimensions' : request.POST.get('dimensions'),
            'sale_end' : request.POST.get('sale_end'),
            'add_product_to_sales' : request.POST.get('add_product_to_sales'),
            'sizes' : request.POST.get('sizes'),
        }

        subcategory_ids = request.POST.getlist('subcategories')
        if subcategory_ids:
            payload['subcategories'] = subcategory_service.fetch_by_ids(subcategory_ids)

        tag_ids = request.POST.getlist('tags')
        if tag_ids:
            payload['tags'] = tag_service.fetch_by_ids(tag_ids)

        color_ids = request.POST.getlist('colors')
        if color_ids:
            payload['colors'] = color_service.fetch_by_ids(color_ids)

        brand_id = request.POST.get('brand')
        if brand_id:
            payload['brand'], _ = brand_service.fetch_single_by_id(brand_id)

        category_id = request.POST.get('category')
        if category_id:
            payload['category'], _ = category_service.fetch_single_by_id(category_id)

        payload['media'] = request.FILES.getlist('media')


        return self.process_request(
            request, target_view="vendor-dashboard-products", target_function=product_service.update_single,
            payload=payload,
            product_id=kwargs.get("product_id")
        )



@csrf_exempt
def delete_product(request, product_id):
    product_service = ProductService(request)

    if request.method == "DELETE":

        message, error = product_service.delete_single(product_id)

        if message:
            return JsonResponse({
                "success": True,
                "message": message
            })

    return JsonResponse({
        "success": True,
        "message": "An error occurred"
    })


class CreateCategoryView(View, CustomRequestUtil):
    extra_context_data = {
        "title": "Add Category"
    }
    template_name = "backend/add-new-category.html"

    def get(self, request, *args, **kwargs):

        return self.process_request(
            request, target_view="add-category"

        )

    def post(self, request, *args, **kwargs):

        self.template_on_error = "backend/add-new-category.html"
        name = request.POST.get('name')
        cover_image = request.FILES.get('cover_image')

        payload = {
            "name": name,
            "cover_image": cover_image
        }
        category_service = CategoryService(self.request)

        return self.process_request(
            request, target_function=category_service.create_single,
            target_view="add-category", payload=payload
        )



class AddOrRemoveFromWishlistView(View, CustomRequestUtil):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        product_id = int(data.get('product_id'))
        wishlist_service = WishlistService(self.request)

        message, error = wishlist_service.add_or_remove({"product": product_id})

        if error:
            return JsonResponse({"error": error}, status=400)

        return JsonResponse({
            "success": True,
            "message": message
        })


class WishlistView(LoginRequiredMixin, View, CustomRequestUtil):
    extra_context_data = {
        "title":"My Wishlist"
    }

    def get(self, request, *args, **kwargs):
        self.template_name = "frontend/wishlist.html"
        self.context_object_name = 'wishlist_items'

        wishlist_service = WishlistService(self.request)

        return self.process_request(
            request, target_function=wishlist_service.fetch_list
        )


def get_subcategories(request, category_id):
    subcategories = Subcategory.available_objects.filter(category_id=category_id).values('id', 'name')
    return JsonResponse(list(subcategories), safe=False)

