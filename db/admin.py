import nested_admin
from django.contrib import admin
from django.contrib.auth.models import Group

from db.models import Database, Table, Column, Row, Value


class ValueInline(nested_admin.NestedStackedInline):
    model = Value
    sortable_field_name = "id"
    extra = 0

    def has_delete_permission(self, request, obj=None):
        return False


class RowInline(nested_admin.NestedStackedInline):
    model = Row
    sortable_field_name = "id"
    extra = 0
    inlines = [ValueInline]

    def has_delete_permission(self, request, obj=None):
        return False


class ColumnInline(nested_admin.NestedStackedInline):
    model = Column
    sortable_field_name = "name"
    extra = 0

    def has_delete_permission(self, request, obj=None):
        return False


class TableInline(nested_admin.NestedStackedInline):
    model = Table
    sortable_field_name = "name"
    inlines = [ColumnInline, RowInline]
    extra = 0

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Database)
class DatabaseAdmin(nested_admin.NestedModelAdmin):
    inlines = [TableInline]
    search_fields = ("name",)


@admin.register(Table)
class TableAdmin(nested_admin.NestedModelAdmin):
    inlines = [ColumnInline, RowInline]
    search_fields = ("name",)


@admin.register(Value)
class TableAdmin(admin.ModelAdmin):
    search_fields = ("info",)


admin.site.unregister(Group)
admin.site.index_title = "Front-end"
