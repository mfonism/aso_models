from django.db import connection, models
from django.db.models.base import ModelBase
from django.test import TransactionTestCase
from django.utils import timezone

from ..models import AbstractShrewdModel
from ..querysets import ShrewdQuerySet


class ShrewdQuerySetTest(TransactionTestCase):

    abstract_model = AbstractShrewdModel

    @classmethod
    def setUpClass(cls):
        cls.model = ModelBase(
            f'__TestModel__{cls.abstract_model.__name__}',
            (cls.abstract_model,),
            {'__module__': cls.abstract_model.__module__}
        )
        super().setUpClass()

    def setUp(self):
        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(self.model)

        # create eight model objects, save them
        self.mos = [self.model() for i in range(8)]
        for mo in self.mos:
            mo.save()

        # populate the appropriate fields in the
        # last four objects to simulate soft delete
        for mo in self.mos[4:]:
            mo.activated_at = None
            mo.deleted_at = timezone.now()
            mo.save()

    def tearDown(self):
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(self.model)

    def test_mututally_exclusive_flags(self):
        '''
        Assert that a shrewd queryset cannot exist in its shrewd
        mode, and be operating on a recycle bin at the same time.
        '''
        with self.assertRaises(AssertionError) as cm:
            ShrewdQuerySet(self.model, shrewd_mode=True, on_recycle_bin=True)

        expected_error_msg = (
            'Shrewd queryset cannot exist in the shrewd mode and work on a '
            'recycle bin at the same time!'
        )
        self.assertEqual(str(cm.exception), expected_error_msg)

    def test_shrewd_mode_fetch(self):
        '''
        Assert that shrewd mode fetches only
        active objects which are not currently soft-deleted.
        '''
        qs = ShrewdQuerySet(self.model, shrewd_mode=True)
        self.assertEqual(qs.count(), 4)
        for mo in qs:
            self.assertIsNotNone(mo.activated_at)
            self.assertIsNone(mo.deleted_at)

    def test_recycle_bin_fetch(self):
        '''
        Assert that shrewd queryset operating on the
        recycle bin fetches only soft-deleted objects.
        '''
        qs = ShrewdQuerySet(self.model, on_recycle_bin=True)
        self.assertEqual(qs.count(), 4)
        for mo in qs:
            self.assertIsNotNone(mo.deleted_at)

    def test_default_fetch(self):
        '''
        Assert that by default, shrewd queryset fetches
        every object of the underlying model which exists in the database.
        '''
        qs = ShrewdQuerySet(self.model)
        self.assertEqual(qs.count(), 8)
        self.assertEqual(list(qs), self.mos)

    def test_shrewd_mode_bulk_delete(self):
        '''
        Assert that bulk delete on a shrewd queryset in
        shrewd mode clears the queryset.
        '''
        qs = ShrewdQuerySet(self.model, shrewd_mode=True)
        self.assertEqual(qs.count(), 4)

        num, _ = qs.delete()
        self.assertEqual(num, 4)
        self.assertIsInstance(_, dict)
        self.assertEqual(qs.count(), 0)

    def test_shrewd_mode_bulk_delete_is_soft(self):
        '''
        Assert that bulk delete on a shrewd queryset in
        shrewd mode sends the so deleted objects to the recycle bin.
        '''
        qs = ShrewdQuerySet(self.model, shrewd_mode=True)
        onbin = ShrewdQuerySet(self.model, on_recycle_bin=True)
        pre_deletion_qs_pks = [mo.pk for mo in qs]

        self.assertEqual(onbin.count(), 4)
        qs.delete()
        self.assertEqual(onbin.count(), 8)

        recycle_bin_pks = [mo.pk for mo in onbin]
        for deleted_mo_pk in pre_deletion_qs_pks:
            self.assertIn(deleted_mo_pk, recycle_bin_pks)

    def test_recycle_bin_delete(self):
        '''
        Assert that bulk delete on a recycle bin clears the recycle bin.
        '''
        onbin = ShrewdQuerySet(self.model, on_recycle_bin=True)
        self.assertEqual(onbin.count(), 4)

        num, _ = onbin.delete()
        self.assertEqual(num, 4)
        self.assertIsInstance(_, dict)
        self.assertEqual(onbin.count(), 0)

    def test_recycle_bin_delete_is_permanent(self):
        '''
        Assert that the recycle bin deletes objects for good on bulk deletion.
        '''
        onbin = ShrewdQuerySet(self.model, on_recycle_bin=True)
        indb = models.QuerySet(self.model)
        pre_deletion_onbin_pks = [mo.pk for mo in onbin]

        self.assertEqual(indb.count(), 8)
        onbin.delete()
        self.assertEqual(indb.count(), 4)

        indb_pks = [mo.pk for mo in indb]
        for deleted_mo_pk in pre_deletion_onbin_pks:
            self.assertNotIn(deleted_mo_pk, indb_pks)
