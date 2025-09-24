from django.db import models
from crm.models import BaseModel


class Upload(BaseModel):
    file_url = models.URLField()
    file_name = models.CharField(max_length=255)
    file_size = models.IntegerField()
    file_type = models.CharField(max_length=255)
    product = models.ForeignKey(
        "products.Product", null=True, blank=True, on_delete=models.SET_NULL, related_name="product_media"
    )
    user = models.ForeignKey(
        "accounts.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="product_media"
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.file_url
