import cloudinary
from cloudinary.models import CloudinaryField
from django.db import models
from django.utils import timezone


class BannerTypeChoices(models.TextChoices):
    main = "Main"
    side = "Side"



class AvailableManager(models.Manager):
    def get_queryset(self):
        return super(AvailableManager, self).get_queryset().filter(deleted_at__isnull=True)

class ObjectManager(models.Manager):
    def get_queryset(self):
        return super(ObjectManager, self).get_queryset()


class AppDbModel(models.Model):
    objects = ObjectManager()

    class Meta:
        abstract = True


class BaseModel(AppDbModel):

    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="+"
    )
    updated_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    deleted_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )


    available_objects = AvailableManager()

    class Meta:
        abstract = True


class ActivityLog(models.Model):
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="user_activities",
    )
    activity_type = models.CharField(max_length=255, null=True)
    note = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{} by {} - {}".format(self.activity_type, self.user, self.note)


class Color(models.Model):
    name = models.CharField(max_length=50)
    hex_code = models.CharField(max_length=7, null=True, blank=True)

    def __str__(self):
        return self.name


class Banner(BaseModel):


    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    image = CloudinaryField("image", null=True, blank=True)
    discount_title = models.CharField(max_length=50, blank=True, null=True)
    banner_type = models.CharField(max_length=15, choices=BannerTypeChoices.choices, default=BannerTypeChoices.main)
    discount_text = models.CharField(max_length=50, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.pk:
            if self.image and not str(self.image).startswith("http"):
                upload = cloudinary.uploader.upload(
                    self.image,
                    folder="banners",
                    public_id=self.title.replace(" ", "_").lower(),
                    overwrite=True,
                    resource_type="image"
                )
                self.image = upload["public_id"]

        super().save(*args, **kwargs)

