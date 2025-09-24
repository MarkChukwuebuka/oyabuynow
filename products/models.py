
from cloudinary.models import CloudinaryField
from django.db import models
from django.db.models import ForeignKey
from django.utils import timezone

from accounts.models import User
from crm.models import BaseModel, Color
from media.models import Upload
from products.services.product_service import generate_sku, generate_unique_slug


class Availability(models.TextChoices):
    in_stock = "In Stock"
    out_of_stock = "Out of Stock"


class Category(BaseModel):
    name = models.CharField(max_length=255, unique=True)
    cover_image = ForeignKey("media.Upload", on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'categories'



class Subcategory(BaseModel):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    cover_image = ForeignKey("media.Upload", on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return f"{self.category.name} → {self.name}"


class Tag(BaseModel):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Brand(BaseModel):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Product(BaseModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="products")
    sub_categories = models.ManyToManyField(Subcategory, blank=True, related_name="products")
    brand = models.ForeignKey("Brand", on_delete=models.SET_NULL, null=True, blank=True)

    price = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    cost_price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    percentage_discount = models.IntegerField(null=True, blank=True)

    sku = models.CharField(max_length=255, blank=True, null=True, unique=True)
    description = models.TextField(null=True, blank=True)

    stock = models.PositiveIntegerField(null=True, blank=True)
    colors = models.ManyToManyField(Color, blank=True, related_name="products")
    tags = models.ManyToManyField(Tag, blank=True, related_name="products")

    is_featured = models.BooleanField(default=False)
    is_best_seller = models.BooleanField(default=False)

    weight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    rating = models.DecimalField(max_digits=2, decimal_places=1, null=True, blank=True)
    dimensions = models.CharField(max_length=100, blank=True, null=True)
    free_shipping = models.BooleanField(default=False)

    views = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name

    def availability(self):
        if not self.stock or self.stock <= 0:
            return Availability.out_of_stock
        return Availability.in_stock

    def save(self, *args, **kwargs):
        if not self.sku and self.name:
            self.sku = generate_sku(self.name)

        if not self.slug:
            self.slug = generate_unique_slug(self, self.name)

        super().save(*args, **kwargs)


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    name = models.CharField(max_length=100)  # e.g., "Size M", "256GB", etc.
    price = models.DecimalField(max_digits=15, decimal_places=2)
    stock = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.product.name} - {self.name}"



class ProductReview(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="product_reviews")
    rating = models.IntegerField(null=True, blank=True)
    review = models.CharField(max_length=500, null=True, blank=True)

    def __str__(self):
        return f"{self.user.first_name}'s Review on {self.product}"


class Wishlist(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="wishlist")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="wishlist_items")

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.first_name} - {self.product.name}"



class DealOfTheDay(BaseModel):
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=False)
    number_of_available_stock = models.IntegerField(default=0)

    def __str__(self):
        return f"Deal for {self.product.name} - {self.discount_percentage}% off"


