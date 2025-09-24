from rest_framework import serializers


class UploadMediaSerializer(serializers.Serializer):
    files = serializers.ListField(
        child=serializers.FileField(),
        required=True,
        allow_empty=False
    )
    media_type = serializers.CharField(required=False, allow_null=True)

    def validate(self, attrs):
        data = attrs.copy()

        files = data.get("files")
        if not files:
            raise serializers.ValidationError("At least one file is required.")
        return data