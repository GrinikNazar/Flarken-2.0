from django.urls import path
from .views import WriteOffAPIView

urlpatterns = [
    path("write-off/", WriteOffAPIView.as_view()),
]
