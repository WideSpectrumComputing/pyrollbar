import collections
import base64
import copy
import math

from rollbar.lib import transforms, text
from rollbar.lib.transforms.serializable import SerializableTransform

from rollbar.test import BaseTest, SNOWMAN


# This base64 encoded string contains bytes that do not
# convert to utf-8 data
invalid_b64 = b'CuX2JKuXuLVtJ6l1s7DeeQ=='

invalid = base64.b64decode(invalid_b64)
undecodable_repr = '<Undecodable type:(str) base64:(%s)>' % invalid_b64.decode('ascii')


class SerializableTransformTest(BaseTest):
    def _assertSerialized(self, start, expected, whitelist=None, skip_id_check=False):
        serializable = SerializableTransform(whitelist_types=whitelist)
        result = transforms.transform(start, serializable)

        #print start
        print result
        print expected

        if not skip_id_check:
            self.assertNotEqual(id(result), id(expected))

        self.assertEqual(type(expected), type(result))

        if isinstance(result, collections.Mapping):
            self.assertDictEqual(result, expected)
        elif isinstance(result, tuple):
            self.assertTupleEqual(result, expected)
        elif isinstance(result, (list, set)):
            self.assertListEqual(result, expected)
        else:
            self.assertEqual(result, expected)

    def test_simple_dict(self):
        start = {
            'hello': 'world',
            '1': 2,
        }
        expected = copy.deepcopy(start)
        self._assertSerialized(start, expected)

    def test_encode_dict_with_invalid_utf8(self):
        start = {
            'invalid': invalid
        }
        expected = copy.copy(start)
        expected['invalid'] = undecodable_repr
        self._assertSerialized(start, expected)

    def test_encode_utf8(self):
        start = invalid
        expected = undecodable_repr
        self._assertSerialized(start, expected)

    def test_encode_None(self):
        start = None
        expected = None
        self._assertSerialized(start, expected, skip_id_check=True)

    def test_encode_float(self):
        start = 3.14
        expected = 3.14
        self._assertSerialized(start, expected, skip_id_check=True)

    def test_encode_int(self):
        start = 33
        expected = 33
        self._assertSerialized(start, expected, skip_id_check=True)

    def test_encode_NaN(self):
        start = float('nan')

        serializable = SerializableTransform()
        result = transforms.transform(start, serializable)

        self.assertTrue(math.isnan(result))

    def test_encode_Infinity(self):
        start = float('inf')

        serializable = SerializableTransform()
        result = transforms.transform(start, serializable)

        self.assertTrue(math.isinf(result))

    def test_encode_empty_tuple(self):
        start = ()
        expected = ()
        self._assertSerialized(start, expected)

    def test_encode_empty_list(self):
        start = []
        expected = []
        self._assertSerialized(start, expected)

    def test_encode_empty_dict(self):
        start = {}
        expected = {}
        self._assertSerialized(start, expected)

    def test_encode_namedtuple(self):
        MyType = collections.namedtuple('MyType', ('field_1', 'field_2'))
        nt = MyType(field_1='this is field 1', field_2=invalid)

        start = nt
        expected = "<MyType(field_1='this is field 1', field_2=u'%s')>" % undecodable_repr
        self._assertSerialized(start, expected)

    def test_encode_tuple_with_bytes(self):
        start = ('hello', 'world', invalid)
        expected = list(start)
        expected[2] = undecodable_repr
        self._assertSerialized(start, tuple(expected))

    def test_encode_list_with_bytes(self):
        start = ['hello', 'world', invalid]
        expected = list(start)
        expected[2] = undecodable_repr
        self._assertSerialized(start, expected)

    def test_encode_dict_with_bytes(self):
        start = {'hello': 'world', 'invalid': invalid}
        expected = copy.deepcopy(start)
        expected['invalid'] = undecodable_repr
        self._assertSerialized(start, expected)

    def test_encode_dict_with_bytes_key(self):
        start = {'hello': 'world', invalid: 'works?'}
        expected = copy.deepcopy(start)
        expected[undecodable_repr] = 'works?'
        del expected[invalid]
        self._assertSerialized(start, expected)

        """
        if python_major_version < 3:
            # Python 2 allows bytes as dict keys, however if those bytes
            # contain unicode that cannot be converted to utf8, we will
            # generate a custom key: <Undecodable base64:(%s)> for it.
            self.assertEqual(2, len(decoded))
            self.assertIn(quoted_undecodable_repr, decoded)
            self.assertEqual('works?', decoded[quoted_undecodable_repr])
        else:
            self.assertEqual(1, len(decoded))

        self.assertEqual('world', decoded['hello'])
        """

    def test_encode_with_custom_repr(self):
        class CustomRepr(object):
            def __repr__(self):
                return 'hello'

        start = {'hello': 'world', 'custom': CustomRepr()}
        expected = copy.deepcopy(start)
        expected['custom'] = 'hello'
        self._assertSerialized(start, expected, whitelist=[CustomRepr])

    def test_encode_with_custom_repr_returns_bytes(self):
        class CustomRepr(object):
            def __repr__(self):
                return b'hello'

        start = {'hello': 'world', 'custom': CustomRepr()}
        expected = copy.deepcopy(start)
        expected['custom'] = b'hello'
        self._assertSerialized(start, expected, whitelist=[CustomRepr])

    def test_encode_with_custom_repr_returns_object(self):
        class CustomRepr(object):
            def __repr__(self):
                return {'hi': 'there'}

        start = {'hello': 'world', 'custom': CustomRepr()}
        expected = copy.deepcopy(start)
        expected['custom'] = "<class 'test_serializable_transform.CustomRepr'>"
        self._assertSerialized(start, expected, whitelist=[CustomRepr])

    def test_encode_with_custom_repr_returns_unicode(self):
        class CustomRepr(object):
            def __repr__(self):
                return SNOWMAN

        start = {'hello': 'world', 'custom': CustomRepr()}
        expected = copy.deepcopy(start)
        expected['custom'] = SNOWMAN
        self._assertSerialized(start, expected, whitelist=[CustomRepr])

