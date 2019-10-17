from django.apps import registry
from django.db import connection
from django.db.models.base import ModelBase
from django.test import TransactionTestCase

from ..models import AbstractShrewdModel
from ..managers import ShrewdManager, NaiveManager, RecycleBinManager
from ..querysets import ShrewdQuerySet, NaiveQuerySet, RecycleBinQuerySet


class ShrewdManagerTest(TransactionTestCase):

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

        # mock up a shrewd manager
        self.shrewd_mgr = ShrewdManager()
        self.shrewd_mgr.model = self.model

        # mock up a naive manager
        self.naive_mgr = NaiveManager()
        self.naive_mgr.model = self.model

        # mock up a recycle bin manager
        self.recycle_bin_mgr = RecycleBinManager()
        self.recycle_bin_mgr.model = self.model

    def tearDown(self):
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(self.model)

    def test_shrewd_manager_operates_on_shrewd_queryset(self):
        self.assertEqual(
            type(self.shrewd_mgr.get_queryset()),
            ShrewdQuerySet
        )

    def test_naive_manager_operates_on_naive_queryset(self):
        self.assertEqual(
            type(self.naive_mgr.get_queryset()),
            NaiveQuerySet
        )

    def test_recycle_bin_manager_operates_on_recycle_bin_queryset(self):
        self.assertEqual(
            type(self.recycle_bin_mgr.get_queryset()),
            RecycleBinQuerySet
        )
