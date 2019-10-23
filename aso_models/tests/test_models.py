import random

from django.apps import registry
from django.db import connection
from django.db.models.base import ModelBase
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from ..models import AbstractShrewdModel
from ..managers import ShrewdManager, NaiveManager, RecycleBinManager


class AbstractnessTest(TestCase):
    '''
    Assert that all the abstract models in this app are indeed abstract.
    '''
    def test_abstract_shrewd_model_is_abstract(self):
        with self.assertRaises(AttributeError) as cm:
            AbstractShrewdModel.objects.create()
        expected_error_msg = (
            'Manager isn\'t available; AbstractShrewdModel is abstract'
        )
        self.assertEqual(str(cm.exception), expected_error_msg)


class ShrewdModelTest(TransactionTestCase):

    abstract_model = AbstractShrewdModel

    @classmethod
    def setUpClass(cls):
        '''
        Programmatically create a concrete subclass of the abstract model.

        If this particular model has been already created/registered (by some
        other test case), get that one.
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

    def tearDown(self):
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(self.model)

    def test_shrewd_manager_on_shrewd_model_dot_objects(self):
        '''
        Assert that the `objects` attribute on shrewd
        model points at a shrewd manager.
        '''
        self.assertEqual(type(self.model.objects), ShrewdManager)

    def test_naive_manager_on_shrewd_model(self):
        '''
        Assert that the `all_objects` attribute on shrewd
        model points at a naive manager.
        '''
        self.assertEqual(type(self.model.all_objects), NaiveManager)

    def test_recycle_bin_on_shrewd_model(self):
        '''
        Assert that the `recycle_bin` attribute on shrewd
        model points at a recycle bin manager.
        '''
        self.assertEqual(type(self.model.recycle_bin), RecycleBinManager)

    def test_default_manager_is_shrewd(self):
        '''
        Assert that the default manager for shrewd model is shrewd.
        '''
        self.assertEqual(type(self.model._default_manager), ShrewdManager)

    def test_base_manager_is_naive(self):
        '''
        Assert that the base manager for shrewd model is naive.
        '''
        self.assertEqual(type(self.model._base_manager), NaiveManager)


class ShrewdModelObjectTest(TransactionTestCase):
    '''
    Test single model objects.
    '''
    abstract_model = AbstractShrewdModel

    @classmethod
    def setUpClass(cls):
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

        # create five model objects, save them
        mos = [self.model() for i in range(5)]
        for mo in mos:
            mo.save()

        # keep the first three as is
        # send the remainder to the recycle bin
        self.viewable = mos[:3]
        self.recycled = mos[3:]
        for mo in self.recycled:
            mo.deleted_at = timezone.now()
            mo.save()

    def tearDown(self):
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(self.model)

    def test_is_outside_bin(self):
        for mo in self.viewable:
            self.assertTrue(mo.is_outside_bin())
        for mo in self.recycled:
            self.assertFalse(mo.is_outside_bin())

    def test_delete_is_soft_by_default(self):
        '''
        Assert that the delete op on a shrewd model object is soft by
        default -- the object is 'sent to the recycle bin'.
        '''
        mo = random.choice(self.viewable)

        self.assertIn(mo, self.model.objects.all())
        num, _ = mo.delete()
        self.assertEqual(num, 1)
        self.assertNotIn(mo, self.model.objects.all())
        self.assertIn(mo, self.model.recycle_bin.all())

    def test_soft_delete_is_a_no_op_in_the_recycle_bin(self):
        '''
        Assert that the delete op on a shrewd model object which
        is already in the recycle bin does nothing to the object.
        '''
        mo = random.choice(self.recycled)

        self.assertIn(mo, self.model.recycle_bin.all())
        num, _ = mo.delete()
        self.assertEqual(num, 0)
        self.assertIn(mo, self.model.recycle_bin.all())

    def test_restore_op(self):
        '''
        Assert that an object in the recycle bin can be restored --
        brought out of the bin.
        '''
        mo = random.choice(self.recycled)

        self.assertIn(mo, self.model.recycle_bin.all())
        self.assertNotIn(mo, self.model.objects.all())

        num, _ = mo.restore()
        self.assertEqual(num, 1)
        self.assertNotIn(mo, self.model.recycle_bin.all())
        self.assertIn(mo, self.model.objects.all())

    def test_restore_is_a_no_op_outside_the_recycle_bin(self):
        '''
        Assert that calling `restore` on a shrewd model object which
        is not in the recycle bin does nothing to the object.
        '''
        mo = random.choice(self.viewable)

        self.assertIn(mo, self.model.objects.all())
        num, _ = mo.restore()
        self.assertEqual(num, 0)
        self.assertIn(mo, self.model.objects.all())

    def test_hard_deletion(self):
        '''
        Assert that a shrewd model object can be deleted for good by
        calling delete with the kwarg `hard=True`.
        '''
        mo = random.choice(self.viewable)

        num, _ = mo.delete(hard=True)
        self.assertEqual(num, 1)
        with self.assertRaises(self.model.DoesNotExist):
            mo.refresh_from_db()

    def test_hard_deletion_on_soft_deleted_objects(self):
        '''
        Assert that hard deletion works even on objects that are
        already in the recycle bin.
        '''
        mo = random.choice(self.recycled)

        num, _ = mo.delete(hard=True)
        self.assertEqual(num, 1)
        with self.assertRaises(self.model.DoesNotExist):
            mo.refresh_from_db()
