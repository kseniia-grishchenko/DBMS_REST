from django.contrib import admin

from db.models import Database, Table, Column, Row, Value

admin.site.register(Database)
admin.site.register(Table)
admin.site.register(Column)
admin.site.register(Row)
admin.site.register(Value)
