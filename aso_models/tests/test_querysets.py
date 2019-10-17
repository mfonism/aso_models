from django.apps import registry
from django.db import connection, models
from django.db.models.base import ModelBase
from django.test import TransactionTestCase
from django.utils import timezone

from ..models import AbstractShrewdModel
from ..querysets import ShrewdQuerySet, NaiveQuerySet, RecycleBinQuerySet


class ShrewdQuerySetTest(TransactionTestCase):

    abstract_model = AbstractShrewdModel

    @classmethod
    def setUpClass(cls):
        '''
        Programmatically create a concrete subclass of the abstract model.

        If this particular model has been already created (by some other test
        case), get that one.
        Otherwise, create it.
        '''
        # apps here, is a registry which stores the configuration of
        # installed applications, and keeps track of models
        # apps = registry.Apps(installed_apps=None)
        apps = registry.apps
        try:
            cls.model = apps.get_model(
                'aso_models', '__testmodel__abstractshrewdmodel'
            )
        except LookupError:
            cls.model = ModelBase(
                f'__TestModel__{cls.abstract_model.__name__}',
                (cls.abstract_model,),
                {'__module__': cls.abstract_model.__module__}
            )

        super().setUpClass()

    def setUp(self):
        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(self.model)

        # the querysets
        self.shrewd_qs = ShrewdQuerySet(self.model)
        self.naive_qs = NaiveQuerySet(self.model)
        self.recycle_bin_qs = RecycleBinQuerySet(self.model)

        # create ten model objects, save them
        self.mos = [self.model() for i in range(10)]
        for mo in self.mos:
            mo.save()
        # populate the appropriate fields in the
        # last four objects to simulate soft delete
        for mo in self.mos[-4:]:
            mo.activated_at = None
            mo.deleted_at = timezone.now()
            mo.save()

    def tearDown(self):
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(self.model)

    def test_shrewd_qs_fetch(self):
        '''
        Assert that shrewd queryset fetches only
        active objects which are not currently soft-deleted.
        '''
        self.assertEqual(self.shrewd_qs.count(), 6)
        for mo in self.shrewd_qs:
            self.assertIsNotNone(mo.activated_at)
            self.assertIsNone(mo.deleted_at)

    def test_recycle_bin_fetch(self):
        '''
        Assert that recycle bin queryset fetches only soft-deleted objects.
        '''
        self.assertEqual(self.recycle_bin_qs.count(), 4)
        for mo in self.recycle_bin_qs:
            self.assertIsNotNone(mo.deleted_at)

    def test_naive_fetch(self):
        '''
        Assert that naive queryset fetches every object of
        the underlying model which exists in the database.
        '''
        self.assertEqual(self.naive_qs.count(), 10)
        self.assertEqual(list(self.naive_qs), self.mos)

    def test_shrewd_bulk_delete(self):
        '''
        Assert that bulk delete on a shrewd queryset clears the queryset.
        '''
        self.assertEqual(self.shrewd_qs.count(), 6)

        num, _ = self.shrewd_qs.delete()
        self.assertEqual(num, 6)
        self.assertIsInstance(_, dict)
        self.assertEqual(self.shrewd_qs.count(), 0)

    def test_shrewd_bulk_delete_is_soft(self):
        '''
        Assert that bulk delete on a shrewd queryset
        sends the so deleted objects to the recycle bin.
        '''
        pre_deletion_pks = [mo.pk for mo in self.shrewd_qs]

        self.assertEqual(self.shrewd_qs.count(), 6)
        self.assertEqual(self.recycle_bin_qs.count(), 4)
        self.shrewd_qs.delete()
        self.assertEqual(self.recycle_bin_qs.count(), 10)

        recycle_bin_pks = [mo.pk for mo in self.recycle_bin_qs]
        for deleted_mo_pk in pre_deletion_pks:
            self.assertIn(deleted_mo_pk, recycle_bin_pks)

    def test_recycle_bin_delete(self):
        '''
        Assert that bulk delete on a recycle bin clears the recycle bin.
        '''
        self.assertEqual(self.recycle_bin_qs.count(), 4)

        num, _ = self.recycle_bin_qs.delete()
        self.assertEqual(num, 4)
        self.assertIsInstance(_, dict)
        self.assertEqual(self.recycle_bin_qs.count(), 0)

    def test_recycle_bin_delete_is_permanent(self):
        '''
        Assert that the recycle bin deletes objects for good on bulk deletion.
        '''
        pre_deletion_pks = [mo.pk for mo in self.recycle_bin_qs]

        self.assertEqual(self.naive_qs.count(), 10)
        self.assertEqual(self.recycle_bin_qs.count(), 4)
        self.recycle_bin_qs.delete()
        self.assertEqual(self.naive_qs.count(), 6)

        remaining_pks = [mo.pk for mo in self.naive_qs]
        for deleted_mo_pk in pre_deletion_pks:
            self.assertNotIn(deleted_mo_pk, remaining_pks)

    def test_naive_delete_is_permanent(self):
        '''
        Assert that naive queryset deletes objects for good on bulk deletion.
        '''
        indb = models.QuerySet(self.model)

        self.assertEqual(self.naive_qs.count(), 10)
        self.assertEqual(indb.count(), 10)
        self.naive_qs.delete()
        self.assertEqual(indb.count(), 0)
        self.assertEqual(self.naive_qs.count(), 0)

    def test_error_calling_restore_on_shrewd_qs(self):
        '''
        Assert that assertion error is raised on
        calling `restore` on shrewd queryset.
        '''
        with self.assertRaises(AssertionError) as cm:
            self.shrewd_qs.restore()

        expected_error_msg = (
            'Restore operation is not allowed on a shrewd queryset.\n'
            'Try restoring objects from a recycle bin queryset.'
        )
        self.assertEqual(str(cm.exception), expected_error_msg)

    def test_restore_op_on_recycle_bin(self):
        '''
        Assert that bulk restore is possible on the recycle bin,
        and that it actually clears the bin of the deleted objects.
        '''
        self.assertEqual(self.recycle_bin_qs.count(), 4)

        num = self.recycle_bin_qs.restore()
        self.assertEqual(num, 4)
        self.assertEqual(self.recycle_bin_qs.count(), 0)

    def test_restored_objects_can_be_found_outside_the_recycle_bin(self):
        '''
        Assert that restoration sends the so deleted objects outside the
        recycle bin -- where they can be found by a shrewd queryset
        operating on the respective model.
        '''
        pre_restoration_pks = [mo.pk for mo in self.recycle_bin_qs]

        self.assertEqual(self.shrewd_qs.count(), 6)
        self.assertEqual(self.recycle_bin_qs.count(), 4)
        self.recycle_bin_qs.restore()
        self.assertEqual(self.shrewd_qs.count(), 10)

        shrewd_qs_pks = [mo.pk for mo in self.shrewd_qs]
        for restored_mo_pk in pre_restoration_pks:
            self.assertIn(restored_mo_pk, shrewd_qs_pks)

    def test_error_calling_restore_on_naive_qs(self):
        '''
        Assert that assertion error is raised on
        calling `restore` on shrewd queryset in its default mode.
        '''
        with self.assertRaises(AssertionError) as cm:
            self.naive_qs.restore()

        expected_error_msg = (
            'Restore operation is not allowed on a naive queryset.\n'
            'Try restoring objects from a recycle bin queryset.'
        )
        self.assertEqual(str(cm.exception), expected_error_msg)
