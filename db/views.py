from typing import Type

from django.db.models import QuerySet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
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
        if self.action in ("list", "retrieve"):
            return DatabaseListSerializer

        return DatabaseSerializer


class TableViewSet(viewsets.ModelViewSet):
    queryset = Table.objects.all()
    serializer_class = TableSerializer

    def get_queryset(self) -> QuerySet:
        return Table.objects.filter(database=self.kwargs["database_pk"])

    def get_serializer_class(self) -> Type[Serializer]:
        if self.action in ("list", "retrieve"):
            return TableListSerializer

        return TableSerializer

    def perform_create(self, serializer: TableSerializer) -> None:
        serializer.save(database_id=self.kwargs["database_pk"])


class ColumnViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Column.objects.all()
    serializer_class = ColumnSerializer

    def get_queryset(self) -> QuerySet:
        return Column.objects.filter(table=self.kwargs["table_pk"])

    def perform_create(self, serializer: ColumnSerializer):
        new_column_data = serializer.validated_data
        table = Table.objects.get(id=self.kwargs["table_pk"])

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

    def create(self, request, *args, **kwargs):
        """
        Create Column endpoint details:
        Use one of the following types: `("int", "char", "real", "string", "email", "enum")`

        Example: `
        {
            "name": "user_types",
            "info": {
                "type": "enum",
                "default": "user",
                "available_values": [
                    "user",
                    "admin"
                ],
                "column_type": "string"
            },
            "table": 1
        }
        `
        """
        return super().create(request, *args, **kwargs)


class RowViewSet(viewsets.ModelViewSet):
    queryset = Row.objects.all()
    serializer_class = RowSerializer

    def get_queryset(self) -> QuerySet:
        queryset = self.queryset.filter(table=self.kwargs["table_pk"])

        search_string = self.request.query_params.get("search_string", None)

        if search_string:
            queryset = queryset.filter(values__info__value=search_string)

        return queryset

    def get_serializer_context(self) -> dict:
        return {"table_id": self.kwargs["table_pk"]}

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "search_string",
                type=OpenApiTypes.STR,
                description="Filter by values in rows (ex. ?search_string=user)",
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        """
        Search by `search_string` string.
        It can be searched by specific value. Only 100% match is supported!
        Example: `?search_string=user`
        """
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """
        Create Row endpoint details:
        be cautious, because all values will be evaluated on creation

        Example: `
        {
            "table": 1,
            "values": [
                {
                    "info": {
                        "value": 5
                    },
                    "column": 1,
                },
                {
                    "info": {
                        "value": "user"
                    },
                    "column": 2,
                }
            ]
        }
        `
        """
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """
        Update Row endpoint details:
        be cautious, because all values will be evaluated during update

        Example: `
        {
            "id": 1,
            "table": 1,
            "values": [
                {
                    "id": 1,
                    "info": {
                        "value": 10
                    },
                    "column": 1,
                    "row": 1
                },
                {
                    "id": 2,
                    "info": {
                        "value": "admin"
                    },
                    "column": 2,
                    "row": 1
                }
            ]
        }
        `
        """
        return super().update(request, *args, **kwargs)
