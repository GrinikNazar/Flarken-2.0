from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from warehouse.services.stock_service import write_off_part
from warehouse.services.stock_service import generate_purchase_list
from warehouse.models import Supplier


class WriteOffAPIView(APIView):

    def post(self, request):
        try:
            part = write_off_part(
                phone_model=request.data.get("phone_model"),
                part_type=request.data.get("part_type"),
                quantity=request.data.get("quantity"),
                color=request.data.get("color"),
                chip_type=request.data.get("chip_type"),
            )

            return Response({
                "success": True,
                "remaining": part.current_quantity
            })

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class PurchaseListAPIView(APIView):

    def post(self, request):
        supplier_id = request.data.get("supplier_id")

        purchase_list = generate_purchase_list(supplier_id)

        supplier_name = Supplier.objects.get(pk=supplier_id)
        return Response({
            "supplier_name": supplier_name.name,
            "list": purchase_list
        })
