from django.shortcuts import render, redirect

from cart.services.cart_service import CartService


def add_to_cart(request):
    cart_service = CartService(request)
    if request.POST.get('action') == 'add':
        product_id = int(request.POST.get('product_id'))
        product_qty = int(request.POST.get('product_qty', 1))

        cart_service.add(product_id, product_qty)

    return redirect('shop')


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

    # product = Product.objects.get(pk=product_id)
    # quantity = cart_service.get_item(product_id)
    #
    # if quantity:
    #     quantity = quantity['quantity']
    #
    #     item = {
    #         'product': {
    #             'id': product.id,
    #             'name': product.name,
    #             'image': product.image,
    #             'get_thumbnail': product.get_thumbnail(),
    #             'price': product.price,
    #         },
    #         'total_price': (quantity * product.price),
    #         'quantity': quantity,
    #     }
    # else:
    #     item = None
    #
    # response = render(request, 'cart/components/cart_item.html', {'item': item})
    #
    # return response