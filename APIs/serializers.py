from rest_framework import serializers


class OCRSerializer(serializers.Serializer):
    url = serializers.CharField(max_length=200)
    section = serializers.CharField(max_length=100)
    _class = serializers.IntegerField()