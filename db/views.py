from typing import Type

from rest_framework import viewsets, mixins
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import Serializer

from db.models import Database, Table, Column, Row
from db.serializers import (
    DatabaseSerializer,
    TableSerializer,
    ColumnSerializer,
    RowSerializer,
    DatabaseListSerializer,
    TableListSerializer,
)


class DatabaseViewSet(viewsets.ModelViewSet):
    queryset = Database.objects.all()
    serializer_class = DatabaseSerializer

    def get_serializer_class(self) -> Type[Serializer]:
        if self.action == "list":
            return DatabaseListSerializer

        return DatabaseSerializer


class TableViewSet(viewsets.ModelViewSet):
    queryset = Table.objects.all()
    serializer_class = TableSerializer

    def get_serializer_class(self) -> Type[Serializer]:
        if self.action == "list":
            return TableListSerializer

        return TableSerializer


class ColumnViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Column.objects.all()
    serializer_class = ColumnSerializer

    def perform_create(self, serializer: ColumnSerializer):
        new_column_data = serializer.validated_data
        table = new_column_data["table"]

        if Row.objects.filter(table=table).exists():
            raise ValidationError(
                {
                    "table": "You can not add columns to the Table, if there are some rows in it!"
                }
            )

        data = new_column_data["info"]

        provided_type = data.get("type", "no_type_provided_error")
        provided_default = data.get("default")

        if not Column.ColumnTypes.has_value(provided_type):
            raise ValidationError(
                {"data": f"Provided type: '{provided_type}' is not supported!"}
            )

        if provided_type != "enum":
            if provided_default is None:
                provided_default = Column.COLUMN_DEFAULTS[provided_type]

            Column.ColumnTypes.validate(provided_type, provided_default)
            return serializer.save(
                info={"type": provided_type, "default": provided_default}
            )

        if "available_values" not in data or "column_type" not in data:
            raise ValidationError(
                {
                    "data": "If type is 'enum' - you should provide "
                    "additionally 'column_type' and 'available_values'"
                }
            )
        column_type = data["column_type"]
        available_values = data["available_values"]

        if provided_default is None:
            provided_default = available_values[0]

        if not Column.ColumnTypes.has_value(column_type) or column_type == "enum":
            raise ValidationError(
                {"data": f"Column type '{column_type}' is not supported for enum!"}
            )

        for value in available_values:
            Column.ColumnTypes.validate(column_type, value)

        return serializer.save(
            info={
                "type": provided_type,
                "default": provided_default,
                "available_values": available_values,
                "column_type": column_type,
            }
        )


class RowViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Row.objects.all()
    serializer_class = RowSerializer
