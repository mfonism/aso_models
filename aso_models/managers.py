from django.db.models.manager import BaseManager

from .querysets import ShrewdQuerySet, NaiveQuerySet, RecycleBinQuerySet


class ShrewdManager(BaseManager.from_queryset(ShrewdQuerySet)):
    pass

class NaiveManager(BaseManager.from_queryset(NaiveQuerySet)):
    pass

class RecycleBinManager(BaseManager.from_queryset(RecycleBinQuerySet)):
    pass
