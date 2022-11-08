from django.urls import path, include
from rest_framework_nested import routers

from db.views import DatabaseViewSet, TableViewSet, ColumnViewSet, RowViewSet

router = routers.DefaultRouter()

router.register("databases", DatabaseViewSet)
databases_router = routers.NestedSimpleRouter(router, "databases", lookup="database")
databases_router.register("tables", TableViewSet)
tables_router = routers.NestedSimpleRouter(databases_router, "tables", lookup="table")
tables_router.register("columns", ColumnViewSet)
tables_router.register("rows", RowViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("", include(databases_router.urls)),
    path("", include(tables_router.urls)),
]
