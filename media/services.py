from django.core.files.base import ContentFile
from django.utils.translation import gettext_lazy as _t
import time
import abc
import re
from abc import ABC

import cloudinary
import cloudinary.uploader
from django.conf import settings

from media.models import Upload
from services.util import CustomRequestUtil


class FileUploader(CustomRequestUtil):
    def __init__(self, request, upload_to=None, user=None):
        super().__init__(request)
        self.upload_to = upload_to or "general"
        self.user = user or self.auth_user

    def get_file_size(self, file):
        original_position = file.tell()  # Store the original position
        file.seek(0, 2)  # Move the file pointer to the end of the file
        file_size = file.tell()  # Get the current position (file size)
        file.seek(original_position)  # Return to the original position
        return file_size

    def generate_file_name(self, ext):
        file_name = f"{str(time.time()).replace('.', '')}{str(time.time()).replace('.', '')}.{ext}"
        return file_name

    def upload(self, file, media_type, product=None):
        original_file_name = file.name
        file_extension = original_file_name.split('.')[-1].lower()
        file_size = self.get_file_size(file)

        if not media_type:
            return None, _t("File type not found.")

        allowed_file_types = [aft.strip(".") for aft in media_type.allowed_file_types]

        if file_extension not in allowed_file_types:
            return None, _t("File extension not supported.")

        max_file_size_in_mb = int(media_type.max_file_size_in_kb / 1024)

        if file_size > (media_type.max_file_size_in_kb * 1024):
            return None, _t("File too large. Max size is %d KB." % max_file_size_in_mb)

        self.upload_to = media_type.upload_to

        file_path = f"{self.upload_to}/{self.generate_file_name(file_extension)}"
        file_content = ContentFile(file.read())

        uploader = CloudinaryUploader(file_path, file_content, file_extension)

        full_url = uploader.upload()

        uploaded_file = Upload.objects.create(
            created_by=self.user,
            file_url=full_url,
            file_name=original_file_name.strip(f".{file_extension}"),
            file_size=file_size,
            file_type=self.get_content_type_from_extension(file_extension),
            product=product,
            user=self.user
        )

        return uploaded_file, _t("File uploaded.")


    def get_content_type_from_extension(self, file_extension):
        extension_mapping = {
            'txt': 'text/plain',
            'jpg': 'image/jpeg',
            'png': 'image/png',
            'pdf': 'application/pdf',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'mp4': 'video/mp4',
            'mp3': 'audio/mp3',
            'html': 'text/html',
            'css': 'text/css',
        }

        return extension_mapping.get(file_extension, 'application/octet-stream')


class Uploader:
    video_extensions = ["mp4", "mov", "avi"]
    image_extensions = ["jpg", "jpeg", "png", "gif"]
    audio_extensions = ["mp3", "wav", "aac", "ogg", "flac"]
    doc_extensions = ["doc", "docx", "csv", "xlsx", "xls"]

    def __init__(self, file_path=None, file_content=None, file_extension=None):
        self.file_path = file_path
        self.file_content = file_content
        self.file_extension = file_extension

    @abc.abstractmethod
    def upload(self):
        pass

    @abc.abstractmethod
    def delete(self):
        pass


class CloudinaryUploader(Uploader, ABC):
    def __init__(self, file_path=None, file_content=None, file_extension=None):
        super().__init__(file_path, file_content, file_extension)

        # Configuration
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_API_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
            secure=True
        )

    def upload(self):
        if self.file_extension in self.video_extensions:
            resource_type = "video"
        elif self.file_extension in self.audio_extensions:
            resource_type = "raw"
        elif self.file_extension in self.doc_extensions:
            resource_type = "raw"
        else:
            resource_type = "image"

        # Upload an image
        upload_result = cloudinary.uploader.upload(
            self.file_content,
            public_id=self.file_path,
            resource_type=resource_type
        )

        url = upload_result.get("secure_url")

        return url

    def delete(self):
        match = re.search(r'upload/.*?/(.+?)(\.[^.]+)?$', self.file_path)
        if not match:
            raise ValueError(f"Could not extract public ID from URL: {self.file_path}")

        public_id = match.group(1)

        # Delete the file
        result = cloudinary.uploader.destroy(public_id)

        return True


