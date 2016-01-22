# -*- coding: utf-8 -*-

import os
import sys
import botocore
import base64

from unittest import TestCase
from nose.tools import ok_, eq_, raises
from mock import Mock,MagicMock,patch
from lamvery.client import *

TEST_CONF = {
  'runtime': 'python2.7',
  'name': 'test_lambda_function',
  'role': 'arn:aws:iam::000000000000:role/lambda_basic_execution',
  'handler': 'lambda_function.lambda_handler',
  'description': 'This is sample lambda function.',
  'timeout': 10,
  'memory_size': 128,
  'publish': True
}

class ClientTestCase(TestCase):

    def setUp(self):
        self.client = Client(region='us-east-1')
        self.client._lambda = Mock()
        self.client._kms = Mock()
        self.client._events = Mock()

    def test_get_function_conf(self):
        self.client._lambda.get_function = Mock(
            return_value={'Configuration': 'foo'})
        eq_(self.client.get_function_conf('test'), 'foo')
        self.client._lambda.get_function = Mock(
            side_effect=botocore.exceptions.ClientError({'Error': {}}, 'bar'))
        eq_(self.client.get_function_conf('test'), {})

    def test_create_function(self):
        self.client.create_function(Mock(), TEST_CONF, True)

    def test_update_function_code(self):
        self.client.update_function_code(Mock(), TEST_CONF, True)

    def test_update_function_conf(self):
        self.client.update_function_conf(TEST_CONF)

    def test_get_alias(self):
        self.client._lambda.get_alias = Mock(return_value='foo')
        eq_(self.client.get_alias('function', 'alias'), 'foo')
        self.client._lambda.get_alias = Mock(
            side_effect=botocore.exceptions.ClientError({'Error': {}}, 'bar'))
        eq_(self.client.get_alias('function', 'alias'), {})

    def test_create_alias(self):
        self.client.create_alias('function', 'alias', 'version')

    def test_update_alias(self):
        self.client.update_alias('function', 'alias', 'version')

    def test_encrypt(self):
        self.client._kms.encrypt = Mock(return_value={'CiphertextBlob': 'foo'})
        eq_(self.client.encrypt('key', 'val'), base64.b64encode('foo'))

    def test_decrypt(self):
        self.client._kms.decrypt = Mock(return_value={'Plaintext': 'bar'})
        eq_(self.client.decrypt(base64.b64encode('secret')), 'bar')

    def test_calculate_capacity(self):
        ret = {'Functions': [{'FunctionName':'foo'}, {'FunctionName':'bar'}]}
        self.client._lambda.list_functions = Mock(return_value=ret)
        self.client._calculate_versions_capacity = Mock(return_value=10)
        eq_(self.client.calculate_capacity(), 20)
        eq_(self.client.calculate_capacity(next_marker='foo'), 20)

    def test_calculate_versions_capacity(self):
        ret = {'Versions': [{'CodeSize':20}, {'CodeSize':20}]}
        self.client._lambda.list_versions_by_function = Mock(return_value=ret)
        eq_(self.client._calculate_versions_capacity('foo'), 40)
        eq_(self.client._calculate_versions_capacity('foo', next_marker='bar'), 40)

    def test_get_rules_by_target(self):
        self.client._get_rule_names_by_tagert = Mock(return_value=['foo', 'bar'])
        self.client._events.describe_rule = Mock(return_value={'foo': 'bar'})
        eq_(self.client.get_rules_by_target('foo'), [
            {'foo': 'bar'},
            {'foo': 'bar'}])

    def test_get_rule_names_by_tagert(self):
        self.client._events.list_rule_names_by_target = Mock(return_value={'RuleNames': ['foo', 'bar']})
        eq_(self.client._get_rule_names_by_tagert('foo'), ['foo', 'bar'])

        self.client._events.list_rule_names_by_target = Mock(
            side_effect=botocore.exceptions.ClientError({'Error': {}}, 'bar'))
        eq_(self.client._get_rule_names_by_tagert('foo', 'bar'), [])

    def test_put_rule(self):
        self.client.put_rule({'rule': 'foo'})

    def test_put_targets(self):
        self.client.put_targets(
            'foo', [{'id': 'foo', 'input': 'bar', 'input_path': 'baz'}], 'baz')

    def test_get_targets_by_rule(self):
        self.client._events.list_targets_by_rule = Mock(return_value={'Targets': [{'foo': 'bar'}]})
        eq_(self.client.get_targets_by_rule('foo'), [{'foo': 'bar'}])

        self.client._events.list_targets_by_rule = Mock(
            side_effect=botocore.exceptions.ClientError({'Error': {}}, 'bar'))
        eq_(self.client.get_targets_by_rule('foo', 'bar'), [])

    def test_remove_targets(self):
        self.client.remove_targets('foo', ['bar', 'baz'])

    def test_delete_rule(self):
        self.client.delete_rule('foo')
