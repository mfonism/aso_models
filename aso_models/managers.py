from django.db.models.manager import BaseManager

from .querysets import ShrewdQuerySet


class ShrewdManager(BaseManager.from_queryset(ShrewdQuerySet)):
    pass
