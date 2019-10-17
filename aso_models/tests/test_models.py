from django.apps import registry
from django.db import connection
from django.db.models.base import ModelBase
from django.test import TestCase, TransactionTestCase

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
