from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from warehouse.services.stock_service import write_off_part, generate_list_of_type
from warehouse.services.stock_service import generate_purchase_list

from warehouse.models import Supplier, PhoneModel


class WriteOffAPIView(APIView):

    def post(self, request):
        quantity = request.data.get("quantity")
        phone_model = request.data.get("phone_model")
        try:
            part, dep_part = write_off_part(
                phone_model=phone_model,
                part_type=request.data.get("part_type"),
                quantity=quantity,
                color=request.data.get("color"),
                chip_type=request.data.get("chip_type"),
            )

            return Response(
                {
                    "message": f"Списано {part.part_type.name} для {PhoneModel.objects.get(pk=phone_model).name} - {quantity}шт\nЗалишилось {part.current_quantity} шт.",

                    "dep_part_type": dep_part.dependent_part.part_type.name if dep_part else None,
                    "dep_part_model": [m.name for m in dep_part.dependent_part.phone_models.all()] if dep_part else None,
                    "dep_part_quantity": quantity,
                },
                status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"message": e},
                status=status.HTTP_400_BAD_REQUEST
            )


class PurchaseListAPIView(APIView):

    def get(self, request):
        supplier_id = request.GET.get("supplier_id")
        try:
            part_type_id = request.GET.get("part_type_id")
        except Exception as e:
            part_type_id=None

        purchase_list = generate_purchase_list(supplier_id, part_type_id) # передаєм id постачальника в stock_service

        supplier_name = Supplier.objects.get(pk=supplier_id)

        return Response({
            "supplier_name": supplier_name.name,
            "list": purchase_list
        })


class ListOfPartAPIView(APIView):
    def get(self, request):
        part_type_id = request.GET.get("part_type_id")

        result = generate_list_of_type(part_type_id)

        return Response(result)