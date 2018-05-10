# -*- coding: utf-8 -*-

import unittest

import devicehive
from devicehive import poll
from devicehive.device import ws as dws


class WsCommandTests(unittest.TestCase):
    def setUp(self):
        self.msg = {'action': 'command/insert', 'deviceGuid': '22345678-9012-3456-7890-123456789012', 'command': { 'id': 1, 'timestamp': None, 'userId': 2, 'command': 'cmd_name', 'parameters': [], 'lifetime': None, 'flags': 0, 'status': 'test status', 'result': None }}
    
    def test_interface(self):
        devicehive.interfaces.ICommand.implementedBy(dws.WsCommand)
    
    def test_create(self):
        ci = dws.WsCommand.create(self.msg)
        self.assertEqual(1, ci.id)
        self.assertEqual(2, ci.user_id)
        self.assertEqual(0, ci.flags)
        self.assertEqual('test status', ci.status)
    
    def test_to_dict(self):
        ci = dws.WsCommand.create(self.msg)
        d  = ci.to_dict()
        
        self.assertEqual(1, d['id'])
        self.assertEqual('cmd_name', d['command'])
        self.assertEqual(2, d['userId'])
        self.assertEqual([], d['parameters'])
        self.assertEqual(0, d['flags'])
        self.assertEqual('test status', d['status'])
        self.assertFalse('result' in d)
    
    def test__getter(self):
        ci = dws.WsCommand.create(self.msg)
        self.assertEqual('cmd_name', ci['command'])
        self.assertEqual([], ci['parameters']) 
        try :
            tmp = ci[123]
            self.fail('should raise TypeError')
        except TypeError :
            pass
        try :
            tmp = ci['test']
            self.fail('should raise IndexError')
        except IndexError :
            pass


class PollCommand(unittest.TestCase):
    def setUp(self) :
        self.message = {'id': 1, 'timestamp': None, 'userId': 2, 'command': 'cmdtest', 'parameters': [], 'lifetime': 123, 'flags': 4, 'status': 'status', 'result': 'result'}
    
    def test_getter(self):
        ci = poll.PollCommand.create(self.message)
        self.assertEqual('cmdtest', ci['command'])
        self.assertEqual([], ci['parameters'])
        try :
            tmp = ci[123]
            self.fail('should raise TypeError')
        except TypeError :
            pass
        try :
            tmp = ci['test']
            self.fail('should raise IndexError')
        except IndexError :
            pass
    
    def test_to_dict(self):
        ci = poll.PollCommand.create(self.message)
        self.assertEqual(1, ci.id)
        self.assertEqual(2, ci.user_id)
        self.assertEqual('cmdtest', ci.command)
        self.assertEqual([], ci.parameters)
        self.assertEqual(123, ci.lifetime)
        self.assertEqual(4, ci.flags)
        self.assertEqual('status', ci.status)
        self.assertEqual('result', ci.result)


if __name__ == '__main__':
    unittest.main()

