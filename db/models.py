import re
from enum import Enum
from typing import Any

from django.db import models
from rest_framework.exceptions import ValidationError


class Database(models.Model):
    name = models.CharField(max_length=250, unique=True)

    def __str__(self) -> str:
        return self.name


class Table(models.Model):
    name = models.CharField(max_length=250)
    database = models.ForeignKey(
        Database, on_delete=models.CASCADE, related_name="tables"
    )

    class Meta:
        unique_together = ("name", "database")

    def __str__(self) -> str:
        return f"{self.name} (DB: {self.database.name})"


class Column(models.Model):
    class ColumnTypes(Enum):
        INT = "int"
        REAL = "real"
        CHAR = "char"
        STRING = "string"
        EMAIL = "email"
        ENUM = "enum"

        @classmethod
        def has_value(cls, value: str) -> bool:
            return value in cls._value2member_map_

        @classmethod
        def validate(cls, column_type: str, value: Any) -> None:
            validation_error_message = (
                f"Incorrect value '{value}' for type '{column_type}' provided!"
            )
            email_regex = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
            if (
                (
                    column_type == Column.ColumnTypes.INT.value
                    and not isinstance(value, int)
                )
                or (
                    column_type == Column.ColumnTypes.REAL.value
                    and not isinstance(value, float)
                )
                or (
                    column_type == Column.ColumnTypes.CHAR.value
                    and not isinstance(value, str)
                    and len(value) == 1
                )
                or (
                    column_type == Column.ColumnTypes.STRING.value
                    and not isinstance(value, str)
                )
                or (
                    column_type == Column.ColumnTypes.EMAIL.value
                    and not bool(re.fullmatch(email_regex, value))
                )
            ):
                raise ValidationError({"value": validation_error_message})

    COLUMN_DEFAULTS = {
        ColumnTypes.INT.value: 0,
        ColumnTypes.REAL.value: 0.0,
        ColumnTypes.CHAR.value: "_",
        ColumnTypes.STRING.value: "",
        ColumnTypes.EMAIL.value: "default@default.com",
    }

    name = models.CharField(max_length=250)
    info = models.JSONField()
    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name="columns")

    def validate_value(self, value: Any) -> None:
        if self.info["type"] != "enum":
            return Column.ColumnTypes.validate(self.info["type"], value)

        if value not in self.info["available_values"]:
            raise ValidationError(
                {
                    "value": f"Value '{value}' for enum column is not in available_values: "
                    f"'{self.info['available_values']}'"
                }
            )

    class Meta:
        unique_together = ("name", "table")

    def __str__(self) -> str:
        return self.name


class Row(models.Model):
    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name="rows")

    def __str__(self) -> str:
        return str(self.id)


class Value(models.Model):
    info = models.JSONField()
    column = models.ForeignKey(Column, on_delete=models.CASCADE, related_name="values")
    row = models.ForeignKey(Row, on_delete=models.CASCADE, related_name="values")

    class Meta:
        unique_together = ("column", "row")

    def __str__(self) -> str:
        return str(self.info)
