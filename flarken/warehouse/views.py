from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from warehouse.services.stock_service import write_off_part


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
