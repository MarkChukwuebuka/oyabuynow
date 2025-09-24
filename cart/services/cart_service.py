from django.conf import settings

from products.services.product_service import ProductService
from services.util import CustomRequestUtil


class CartService(CustomRequestUtil):

    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        self.request = request

        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}

        self.cart = cart
        # It first checks if there's an existing cart in the session.
        #  If not, it creates an empty cart in the session.
        # The cart is stored in the self.cart attribute for further use.

    def __iter__(self):
        product_service = ProductService(self.request)
        for p in self.cart.keys():
            self.cart[str(p)]['product'] = product_service.get_base_query().filter(pk=p).first()

        for item in self.cart.values():
            if item['product'].percentage_discount:
                item['total_price'] = int(item['product'].discounted_price * item['quantity'])
            else:
                item['total_price'] = int(item['product'].price * item['quantity'])

            yield item
        # This method makes the Cart class iterable,
        # meaning you can loop through the items in the cart using a for loop.

    def __len__(self):
        return len(self.cart)
        # This method returns the total number of items in the cart.

    def save(self):
        self.session[settings.CART_SESSION_ID] = self.cart
        self.session.modified = True
        #  This method saves the cart back to the user's session after making changes.

    def add(self, product_id, quantity, update_quantity=False):
        # This method is used to add products to the cart.
        product_id = str(product_id)

        if product_id not in self.cart:
            self.cart[product_id] = {'quantity': quantity, 'id': product_id}

        if update_quantity:
            self.cart[product_id]['quantity'] = int(quantity)

            if self.cart[product_id]['quantity'] == 0:
                self.remove(product_id)

        self.save()
        message = "Item has been added to cart"
        return message, None

    def remove(self, product_id):
        product_id = str(product_id)  # Ensure data type compatibility
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()  # Ensure cart data is saved to the session
        message = "Item was removed from cart"
        return message, None

        #  This method removes a product from the cart based on its product_id.

    def clear(self):
        del self.session[settings.CART_SESSION_ID]
        self.session.modified = True
        # This method clears the entire cart by deleting it from the session.

    def get_total_cost(self):
        total = 0
        product_ids = self.cart.keys()
        product_service = ProductService(self.request)
        products = product_service.get_base_query().filter(id__in=product_ids)

        for value in self.cart.values():
            key = int(value['id'])
            qty = value['quantity']
            for product in products:
                if key == product.id:
                    if product.percentage_discount:
                        total = total + (product.discounted_price * qty)
                    else:
                        total = total + (product.price * qty)

        return total

    def get_item(self, product_id):
        if str(product_id) in self.cart:
            return self.cart[str(product_id)]
        else:
            return None
    # This method retrieves an item from the cart based on its product_id and returns it