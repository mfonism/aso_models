from django.db.models.manager import BaseManager

from .querysets import ShrewdQuerySet, NaiveQuerySet, RecycleBinQuerySet


class ShrewdManager(BaseManager.from_queryset(ShrewdQuerySet)):
    '''
    Shrewd manager for models.

    Manages only objects of the model which are __not in__ the recycle bin.
    '''
    pass


class NaiveManager(BaseManager.from_queryset(NaiveQuerySet)):
    '''
    Naive manager for models.

    Manages __all__ the objects of the model in the database.
    '''
    pass


class RecycleBinManager(BaseManager.from_queryset(RecycleBinQuerySet)):
    '''
    Recycle bin manager for models.

    Manages only objects of the model which are __in__ the recycle bin.
    '''
    pass
