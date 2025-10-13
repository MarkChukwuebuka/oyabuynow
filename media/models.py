import cloudinary.uploader
from cloudinary.models import CloudinaryField
from django.db import models

from crm.models import BaseModel


class Upload(BaseModel):
    image = CloudinaryField("image", null=True, blank=True)
    product = models.ForeignKey(
        "products.Product", null=True, blank=True, on_delete=models.SET_NULL, related_name="product_media"
    )

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if self.image and not str(self.image).startswith("http") and self.product:
            # Count existing product images
            count = Upload.objects.filter(product=self.product).count() + 1

            upload = cloudinary.uploader.upload(
                self.image,
                folder=f"products/{self.product.sku}",   # products/<sku>/
                public_id=str(count),                   # 1, 2, 3 ...
                overwrite=True,
                resource_type="image"
            )
            self.image = upload["public_id"]

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} - {self.product.sku}"
