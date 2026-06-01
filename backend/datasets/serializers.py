"""
datasets/serializers.py
────────────────────────────────────────────────────────────────────────────────
TODO: define your datasets serializers here.

Serializers validate incoming request data and control what fields are
returned in responses.

Pattern used in this project:
    • One serializer per logical operation (Create, Update, List, Detail)
    • Never expose internal fields like file_path in responses
    • Use read_only_fields for fields the client should not be able to set

Example:

    from rest_framework import serializers
    from .models import MyModel

    class MyModelSerializer(serializers.ModelSerializer):
        class Meta:
            model  = MyModel
            fields = ["id", "name", "created_at"]
            read_only_fields = ["id", "created_at"]
"""

# Placeholder — no serializers implemented yet.
