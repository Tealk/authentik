"""Tokens API Viewset"""
from django.db.models.base import Model
from django.http.response import Http404
from drf_yasg2.utils import swagger_auto_schema
from rest_framework.decorators import action
from rest_framework.fields import CharField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer, Serializer
from rest_framework.viewsets import ModelViewSet

from authentik.core.models import Token
from authentik.events.models import Event, EventAction


class TokenSerializer(ModelSerializer):
    """Token Serializer"""

    class Meta:

        model = Token
        fields = ["pk", "identifier", "intent", "user", "description"]


class TokenViewSerializer(Serializer):
    """Show token's current key"""

    key = CharField(read_only=True)

    def create(self, validated_data: dict) -> Model:
        raise NotImplementedError

    def update(self, instance: Model, validated_data: dict) -> Model:
        raise NotImplementedError


class TokenViewSet(ModelViewSet):
    """Token Viewset"""

    lookup_field = "identifier"
    queryset = Token.filter_not_expired()
    serializer_class = TokenSerializer

    @swagger_auto_schema(responses={200: TokenViewSerializer(many=False)})
    @action(detail=True)
    def view_key(self, request: Request, identifier: str) -> Response:
        """Return token key and log access"""
        tokens = Token.filter_not_expired(identifier=identifier)
        if not tokens.exists():
            raise Http404
        token = tokens.first()
        Event.new(  # noqa # nosec
            EventAction.SECRET_VIEW, secret=token
        ).from_http(request)
        return Response(TokenViewSerializer({"key": token.key}).data)
