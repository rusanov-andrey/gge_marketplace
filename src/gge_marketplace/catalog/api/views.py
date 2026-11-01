from rest_framework.response import Response
from rest_framework.views import APIView

from gge_marketplace.catalog.api.serializers import (
    ProductCreateSerializer,
    ProductResponseSerializer,
    ProductUpdateSerializer,
)
from gge_marketplace.config.container import container


class ProductListAPIView(APIView):
    def get(self, request):
        repo = container.product_repository
        products = repo.get_all()

        serializer = ProductResponseSerializer(products, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ProductCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        use_case = container.create_product_use_case()
        product = use_case.execute(**serializer.validated_data)

        response_serializer = ProductResponseSerializer(product)
        return Response(response_serializer.data)


class ProductDetailAPIView(APIView):
    def get(self, request, product_id):
        repo = container.product_repository
        product = repo.get_by_id(product_id)

        serializer = ProductResponseSerializer(product)
        return Response(serializer.data)

    def put(self, request, product_id):
        serializer = ProductUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        use_case = container.update_product_use_case()
        product = use_case.execute(id=product_id, **serializer.validated_data)

        response_serializer = ProductResponseSerializer(product)
        return Response(response_serializer.data)

    def delete(self, request, product_id):
        use_case = container.delete_product_use_case()
        product = use_case.execute(id=product_id)

        response_serializer = ProductResponseSerializer(product)
        return Response(response_serializer.data)
