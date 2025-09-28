import json

from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt

from cart.services.cart_service import CartService


def add_to_cart(request):
    cart_service = CartService(request)
    if request.POST.get('action') == 'add':
        product_id = int(request.POST.get('product_id'))
        product_qty = int(request.POST.get('product_qty', 1))

        cart_service.add(product_id, product_qty)

    return redirect('shop')


@csrf_exempt
def add_to_cart(request):
    cart_service = CartService(request)

    if request.method == "POST":
        data = json.loads(request.body)
        product_id = int(data.get("product_id"))
        product_qty = int(data.get("product_qty", 1))

        res, _ = cart_service.add(product_id, product_qty)

        cart = request.session.get("cart")
        cart_count = len(cart) if cart else 0

        return JsonResponse({
            "success": True,
            "message": res,
            "cart_count": cart_count
        })

    return None


@csrf_exempt
def remove_from_cart(request):
    cart_service = CartService(request)

    if request.method == "POST":
        data = json.loads(request.body)
        product_id = data.get("product_id")

        res, _ = cart_service.remove(product_id)

        cart = request.session.get("cart")
        cart_count = len(cart) if cart else 0

        return JsonResponse({
            "success": True,
            "message": res,
            "cart_count": cart_count
        })

    return None


def cart(request):
    context = {
        "title": "Cart"
    }
    return render(request, 'cart.html', context)


def update_cart(request):
    cart_service = CartService(request)
    action = request.POST.get('action')
    product_id = int(request.POST.get('product_id'))

    if action == 'update':
        quantity = int(request.POST.get('product_qty'))
        cart_service.add(product_id, quantity, True)

        return redirect('cart')

    elif action == 'remove':
        cart_service.remove(product_id)

        return redirect('cart')
