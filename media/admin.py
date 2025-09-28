from django.contrib import admin

from media.models import Upload


class UploadInline(admin.TabularInline):  # you can also use StackedInline
    model = Upload
    extra = 1  # how many empty forms to show
    fields = ["image", "user"]
    readonly_fields = ["user"]

    def save_new_instance(self, form, commit=True):
        """
        Automatically attach the request.user to uploaded images.
        """
        instance = super().save_new_instance(form, commit=False)
        if hasattr(self, "request") and self.request.user.is_authenticated:
            instance.user = self.request.user
        if commit:
            instance.save()
        return instance