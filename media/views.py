
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Upload

@require_http_methods(["DELETE"])
def delete_product_image(request, upload_id):
    try:
        image = Upload.objects.get(id=upload_id)
        image.delete()
        return JsonResponse({"success": True})
    except Upload.DoesNotExist:
        return JsonResponse({"success": False, "error": "Image not found"}, status=404)
