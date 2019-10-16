from django.db import models
from django.db.models.query_utils import Q
from django.utils import timezone


class ShrewdQuerySet(models.QuerySet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # query for only active, non soft-deleted objects
        self.query.add_q(
            Q(deleted_at__isnull=True, activated_at__isnull=False)
        )

    def delete(self):
        return self.update(deleted_at=timezone.now(), activated_at=None), {}

    def restore(self):
        raise AssertionError(
            'Restore operation is not allowed on a shrewd queryset.\n'
            'Try restoring objects from a recycle bin queryset.'
        )


class NaiveQuerySet(models.QuerySet):
    def restore(self):
        raise AssertionError(
            'Restore operation is not allowed on a naive queryset.\n'
            'Try restoring objects from a recycle bin queryset.'
        )


class RecycleBinQuerySet(models.QuerySet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # query for only soft-deleted objects
        self.query.add_q(
            Q(deleted_at__isnull=False)
        )

    def restore(self):
        return self.update(deleted_at=None, activated_at=timezone.now())
