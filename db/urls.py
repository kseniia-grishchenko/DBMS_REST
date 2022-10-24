from rest_framework import routers

from db.views import DatabaseViewSet, TableViewSet, ColumnViewSet, RowViewSet

router = routers.DefaultRouter()

router.register("databases", DatabaseViewSet)
router.register("tables", TableViewSet)
router.register("columns", ColumnViewSet)
router.register("rows", RowViewSet)

urlpatterns = router.urls

app_name = "db"
