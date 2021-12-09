from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404
from rest_framework import fields, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.serializers import Serializer

from wagtail.api.v2.utils import BadRequestError
from wagtail.core.actions.create_alias import CreatePageAliasAction, CreatePageAliasIntegrityError
from wagtail.core.models import Page

from .base import APIAction


class CreatePageAliasAPIActionSerializer(Serializer):
    parent_page_id = fields.IntegerField(required=False)
    recursive = fields.BooleanField(default=False, required=False)
    update_slug = fields.CharField(required=False)
    update_locale = fields.CharField(required=False)
    reset_translation_key = fields.BooleanField(default=True, required=False)


class CreatePageAliasAPIAction(APIAction):
    serializer = CreatePageAliasAPIActionSerializer

    def _action_from_data(self, instance, data):
        parent, parent_page_id = None, data.get("parent_page_id")
        if parent_page_id:
            parent = get_object_or_404(Page, id=parent_page_id).specific

        return CreatePageAliasAction(
            page=instance,
            recursive=data["recursive"],
            parent=parent,
            update_slug=data.get("update_slug"),
            update_locale=data.get("update_locale"),
            user=self.request.user,
            reset_translation_key=data["reset_translation_key"],
        )

    def execute(self, instance, data):
        action = self._action_from_data(instance, data)

        try:
            new_page = action.execute()
        except DjangoValidationError as e:
            raise ValidationError(e.message_dict)
        except CreatePageAliasIntegrityError as e:
            raise BadRequestError(e.args[0])

        serializer = self.view.get_serializer(new_page)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
