from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

from gge_marketplace.common.domain.exceptions import DomainError, DomainObjectNotFoundError, DomainValidationError


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if isinstance(exc, DomainValidationError):
        return Response(
            {'details': {exc.field: [exc.message]}},
            status=status.HTTP_400_BAD_REQUEST
        )

    if isinstance(exc, DomainObjectNotFoundError):
        return Response(
            {'details': [str(exc)]},
            status=status.HTTP_404_NOT_FOUND
        )

    if isinstance(exc, DomainError):
        return Response(
            {'details': [str(exc)]},
            status=status.HTTP_400_BAD_REQUEST
        )

    return response
