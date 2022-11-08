from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework_nested.serializers import NestedHyperlinkedModelSerializer

from db.models import Database, Table, Column, Row, Value


class TableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Table
        fields = ("id", "database", "name")
        read_only_fields = ("id", "database")


class DatabaseTableSerializers(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {
        "database_pk": "database__pk",
    }

    class Meta:
        model = Table
        fields = ("url", "name")


class DatabaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Database
        fields = ("id", "name")


class DatabaseListSerializer(serializers.HyperlinkedModelSerializer):
    tables = DatabaseTableSerializers(many=True, read_only=True)

    class Meta:
        model = Database
        fields = ("id", "name", "tables")


class ColumnSerializer(serializers.ModelSerializer):
    class Meta:
        model = Column
        fields = ("id", "name", "info", "table")
        read_only_fields = ("id", "table")


class ValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Value
        fields = ("id", "info", "column", "row")
        read_only_fields = ("row",)


class RowSerializer(serializers.ModelSerializer):
    values = ValueSerializer(many=True, allow_empty=False)

    def create(self, validated_data: dict) -> Row:
        with transaction.atomic():  # transaction because multiple writes - for db consistency
            table = Table.objects.get(id=self.context["table_id"])
            values_data = validated_data.pop("values")
            if len(values_data) != table.columns.count():
                raise ValidationError(
                    {"values": "Number of columns and values in row mismatch!"}
                )
            row = Row.objects.create(**validated_data, table=table)
            for value_data in values_data:
                value_data["column"].validate_value(value_data["info"]["value"])
                Value.objects.create(row=row, **value_data)

            return row

    def update(self, instance: Row, validated_data: dict) -> Row:
        with transaction.atomic():
            values_data = validated_data.pop("values")
            table = Table.objects.get(id=self.context["table_id"])
            if len(values_data) != table.columns.count():
                raise ValidationError(
                    {"values": "Number of columns and values in row mismatch!"}
                )

            if table != instance.table:
                raise ValidationError(
                    {"table": "Table of Row cannot be change during update!"}
                )

            for value_data in values_data:
                if not Value.objects.filter(
                    row=instance, column=value_data["column"]
                ).exists():
                    raise ValidationError(
                        {"values": "Incorrect columns provided for changing this row!"}
                    )

                value = Value.objects.get(row=instance, column=value_data["column"])
                value.column.validate_value(value_data["info"]["value"])
                value.info = {"value": value_data["info"]["value"]}
                value.save()

            instance.save()

            return instance

    class Meta:
        model = Row
        fields = ("id", "table", "values")
        read_only_fields = ("id", "table")


class TableColumnSerializers(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {
        "table_pk": "table__pk",
        "database_pk": "table__database__pk",
    }

    class Meta:
        model = Column
        fields = ("url", "name", "info")


class TableRowSerializers(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {
        "table_pk": "table__pk",
        "database_pk": "table__database__pk",
    }
    values = ValueSerializer(many=True, read_only=True)

    class Meta:
        model = Row
        fields = ("url", "values")


class TableListSerializer(serializers.HyperlinkedModelSerializer):
    columns = TableColumnSerializers(many=True, read_only=True)
    rows = TableRowSerializers(many=True, read_only=True)

    class Meta:
        model = Table
        fields = ("id", "database", "name", "columns", "rows")
