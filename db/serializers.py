from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from db.models import Database, Table, Column, Row, Value


class TableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Table
        fields = ("id", "database", "name")


class DatabaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Database
        fields = ("id", "name")


class DatabaseListSerializer(serializers.ModelSerializer):
    tables = TableSerializer(many=True, read_only=True)

    class Meta:
        model = Database
        fields = ("id", "name", "tables")


class ColumnSerializer(serializers.ModelSerializer):
    class Meta:
        model = Column
        fields = ("id", "name", "info", "table")


class ValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Value
        fields = ("id", "info", "column", "row")
        read_only_fields = ("row",)


class RowSerializer(serializers.ModelSerializer):
    values = ValueSerializer(many=True, allow_empty=False)

    def create(self, validated_data: dict) -> Row:
        with transaction.atomic():  # transaction because multiple writes - for db consistency
            values_data = validated_data.pop("values")
            if len(values_data) != validated_data["table"].columns.count():
                raise ValidationError(
                    {"values": "Number of columns and values in row mismatch!"}
                )
            row = Row.objects.create(**validated_data)
            for value_data in values_data:
                value_data["column"].validate_value(value_data["info"]["value"])
                Value.objects.create(row=row, **value_data)

            return row

    class Meta:
        model = Row
        fields = ("id", "table", "values")


class TableListSerializer(serializers.ModelSerializer):
    columns = ColumnSerializer(many=True, read_only=True)
    rows = RowSerializer(many=True, read_only=True)

    class Meta:
        model = Table
        fields = ("id", "database", "name", "columns", "rows")
