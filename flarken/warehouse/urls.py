from django.urls import path
from .views import WriteOffAPIView, PurchaseListAPIView, ListOfPartAPIView

urlpatterns = [
    path("write-off/", WriteOffAPIView.as_view()), # http://127.0.0.1:8000/warehouse/write-off/
    path("purchase-list/<int:supplier_id>/", PurchaseListAPIView.as_view()), # http://127.0.0.1:8000/warehouse/purchase-list/
    path("purchase-list-part-type/<int:supplier_id>/<int:part_type_id>/", PurchaseListAPIView.as_view()),  # http://127.0.0.1:8000/warehouse/purchase-list-part-type/
    path("list-of-part-types/<int:part_type_id>/", ListOfPartAPIView.as_view()),  # http://127.0.0.1:8000/warehouse/list-of-part-types/
]
