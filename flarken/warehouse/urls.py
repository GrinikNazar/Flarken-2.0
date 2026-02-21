from django.urls import path
from .views import WriteOffAPIView, PurchaseListAPIView

urlpatterns = [
    path("write-off/", WriteOffAPIView.as_view()), # http://127.0.0.1:8000/warehouse/write-off/
    path("purchase-list/", PurchaseListAPIView.as_view()), # http://127.0.0.1:8000/warehouse/purchase-list/
]
