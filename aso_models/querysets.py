from django.db import models
from django.db.models.query_utils import Q
from django.utils import timezone


class ShrewdQuerySet(models.QuerySet):
    '''
    I am the queryset for shrewd models.

    FETCH OP:
    * In my shrewd mode I fetch objects (of the model) which
    are active and have not been soft deleted.
    * In the non-shrewd mode I fetch every darned object of the model.
    * I can also operate on the recycle bin - in this state I fetch
    only objects that have been soft deleted.

    DELETE OP:
    * In my shrewd mode, (bulk) delete is 'soft' and can be undone from
    outside my shrewd mode (you'll probably do that with a counterpart
    of mine that's working on the recycle bin).
    * Outside my shrewd mode, (bulk) delete is 'hard' and CANNOT be undone.
    '''
    def __init__(self, *args, **kwargs):
        self.is_shrewd = kwargs.pop('shrewd_mode', False)
        self.is_on_recycle_bin = kwargs.pop('on_recycle_bin', False)
        assert not (self.is_shrewd and self.is_on_recycle_bin), (
            'Shrewd queryset cannot exist in the shrewd mode and work on a '
            'recycle bin at the same time!'
        )
        super().__init__(*args, **kwargs)
        if self.is_shrewd:
            # queryset should fetch only active, non soft-deleted objects
            self.query.add_q(
                Q(deleted_at__isnull=True, activated_at__isnull=False)
            )
        elif self.is_on_recycle_bin:
            # queryset should fetch only soft-deleted objects
            self.query.add_q(Q(deleted_at__isnull=False))

    def delete(self):
        '''
        Perform soft-delete if in shrewd mode, otherwise delete for good.

        Soft delete sets the `deleted_at` field and clears the `activated_at`
        field. This way, the object can be found by a shrewd queryset operating
        on the recycle bin.
        '''
        if self.is_shrewd:
            # in respecting the interface of
            # `models.QuerySet.delete`, we return a 2-tuple containing
            # the number of the soft-deleted objects and
            # a dict representation of a counter/bag of their respective models
            #
            # for now we just go with an empty counter/bag
            return self.update(deleted_at=timezone.now(), activated_at=None), {}
        return super().delete()

    def restore(self):
        '''
        Attempt to restore soft-deleted model objects in the shrewd queryset.

        Calling this anyway outside a recycle bin raises an error.
        '''
        assert self.is_on_recycle_bin, (
            'Restore operation is only allowed (on a shrewd '
            'queryset which is operating) on the recycle bin.'
        )
