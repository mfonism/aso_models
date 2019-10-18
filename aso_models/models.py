from django.db import models
from django.utils import timezone

from .managers import ShrewdManager, NaiveManager, RecycleBinManager


class AbstractShrewdModel(models.Model):
    '''
    Abstract model for objects under shrewd (and shrewd-ish) management.

    __ROW-LEVEL MANAGEMENT:__
    Objects of (models subclassed from) this model have two mutually exclusive
    resting places in their lifetime -- one is the recycle bin, the other is
    the yet-to-be-named, default resting place :).

    So there's the idea of objects which are in the recycle bin, and
    objects which are not in the recycle bin.

    Two operations, DELETE and RESTORE, are available on these objects. The
    operations act according to the resting place of the particular object, but
    basically:
    * DELETE sends an object to the recycle bin -- soft deletion, if you may.
    * RESTORE takes an object out of the recycle bin.

    For more on the nuances of these operations, read the
    documentation for their related methods, `delete` and `restore`.

    __TABLE-WIDE MANAGEMENT:__
    * Shrewd by default (via an instance of `ShrewdManager`).
    * Default manager manages only objects of the model which are not in the
    recycle bin.
    '''
    class Meta:
        abstract = True

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    activated_at = models.DateTimeField(
        default=timezone.now, blank=True, null=True
    )
    deleted_at = models.DateTimeField(blank=True, null=True)

    # model managers
    objects = ShrewdManager()
    all_objects = NaiveManager()
    recycle_bin = RecycleBinManager()

    def delete(self, **kwargs):
        '''
        Delete this model object (soft delete, by default).

        If `hard` kwarg is set to `True`:
        * delete for good.
        Otherwise:
        * if model object is outside the recycle bin, send it into the bin.
        * otherwise leave it untouched.

        Return the number of objects 'deleted' and a dictionary with
        the number of 'deletions' per object type (wherever possible).
        '''
        if kwargs.pop('hard', False):
            return super().delete(**kwargs)
        if not self.is_outside_bin():
            return 0, {}
        return self._send_to_bin()

    def restore(self):
        '''
        Restore this model object from the recycle bin -- if it is in there.

        Return the number of objects restored, and a dictionary with the
        number of restorations per object type (wherever possible).
        '''
        if self.is_outside_bin():
            return 0, {}
        return self._bring_back_from_bin()

    def _send_to_bin(self):
        self.deleted_at = timezone.now()
        self.activated_at = None
        self.save()
        return 1, {}

    def _bring_back_from_bin(self):
        self.deleted_at = None
        self.activated_at = timezone.now()
        self.save()
        return 1, {}

    def is_outside_bin(self):
        '''
        Return whether model object is outside recycle bin or not.
        '''
        return self.deleted_at is None
