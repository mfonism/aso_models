from django.db.models.manager import BaseManager

from .querysets import ShrewdQuerySet, NaiveQuerySet


class ShrewdManager(BaseManager.from_queryset(ShrewdQuerySet)):
    pass

class NaiveManager(BaseManager.from_queryset(NaiveQuerySet)):
    pass
