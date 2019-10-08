from django.test import TestCase

from ..models import AbstractShrewdModel


class AbstractnessTest(TestCase):
    '''
    Assert that all the abstract models in this app are indeed abstract.
    '''
    def test_abstract_shrewd_model_is_abstract(self):
        with self.assertRaises(AttributeError) as e:
            AbstractShrewdModel.objects.create()
        expected_error_msg = (
            'Manager isn\'t available; AbstractShrewdModel is abstract'
        )
        self.assertEqual(e.exception.args[0], expected_error_msg)
