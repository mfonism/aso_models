from django.db import models
from django.db.models.query_utils import Q
from django.utils import timezone


class ShrewdQuerySet(models.QuerySet):
    '''
    Shrewd queryset for models.

    Fetches only objects of the underlying model which
    are __not__ in the recycle bin.
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ensure it only ever fetches objects which are not in the recycle bin
        self.query.add_q(
            Q(deleted_at__isnull=True, activated_at__isnull=False)
        )

    def delete(self):
        '''
        Send the fetched objects into the recycle bin.
        '''
        return self.update(deleted_at=timezone.now(), activated_at=None), {}

    def restore(self):
        raise AssertionError(
            'Restore operation is not allowed on a shrewd queryset.\n'
            'Try restoring objects from a recycle bin queryset.'
        )


class NaiveQuerySet(models.QuerySet):
    '''
    Naive queryset for models.

    Fetches __every__ object of the underlying model available on the database.
    '''
    def restore(self):
        raise AssertionError(
            'Restore operation is not allowed on a naive queryset.\n'
            'Try restoring objects from a recycle bin queryset.'
        )


class RecycleBinQuerySet(models.QuerySet):
    '''
    Recycle bin queryset for models.

    Fetches only objects of the underlying model which
    are __in__ the recycle bin.
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ensure it only ever fetches objects that are in the recycle bin
        self.query.add_q(
            Q(deleted_at__isnull=False)
        )

    def restore(self):
        '''
        Send the fetched objects out of the recycle bin.
        '''
        return self.update(deleted_at=None, activated_at=timezone.now())
