#! /usr/bin/env python

import time
import math
import qless
import unittest

class TestQless(unittest.TestCase):
    def setUp(self):
        # Clear the script cache, and nuke everything
        qless.r.execute_command('script', 'flush')
        self.q = qless.Queue('testing')
        # This represents worker 'a'
        self.a = qless.Queue('testing')
        self.a.worker = 'worker-a'
        self.b = qless.Queue('testing')
        self.b.worker = 'worker-b'
    
    def tearDown(self):
        self.q.delete()
    
    def test_config(self):
        # Set this particular configuration value
        qless.Config.set('testing', 'foo')
        self.assertEqual(qless.Config.get('testing'), 'foo')
        # Now let's get all the configuration options and make
        # sure that it's a dictionary, and that it has a key for 'testing'
        self.assertTrue(isinstance(qless.Config.get(), dict))
        self.assertEqual(qless.Config.get()['testing'], 'foo')
        # Now we'll delete this configuration option and make sure that
        # when we try to get it again, it doesn't exist
        qless.Config.set('testing')
        self.assertEqual(qless.Config.get('testing'), None)
    
    def test_push_peek_pop_many(self):
        # In this test, were going to add several jobs, and make
        # sure that they:
        #   1) get put onto the queue
        #   2) we can peek at them
        #   3) we can pop them all off
        #   4) once we've popped them off, we can 
        jobs = [qless.Job({'name': 'test_push_pop_many', 'count': c}) for c in range(10)]
        self.assertEqual(len(self.q), 0, 'Start with an empty queue')
        for j in jobs:
            self.q.push(j, 60)
        self.assertEqual(len(self.q), len(jobs), 'Inserting should increase the size of the queue')
        
        # Alright, they're in the queue. Let's take a peek
        self.assertEqual(len(self.q.peek(7)) , 7)
        self.assertEqual(len(self.q.peek(10)), 10)
        
        # Now let's pop them all off one by one
        self.assertEqual(len(self.q.pop(7)) , 7)
        self.assertEqual(len(self.q.pop(10)), 3)
        
        for j in jobs:
            j.delete()
    
    def test_put_get(self):
        # Test just a basic put followed by a get
        job = qless.Job({'name': 'test_put_get'})
        self.q.push(job, 60)
        j = qless.Job.get(job.id)
        self.assertEqual(j['priority'], 0)
        self.assertEqual(j['data']    , {'name': 'test_put_get'})
        # For whatever reason, empty lists from lua encode into {}
        self.assertEqual(j['tags']    , {})
        self.assertEqual(j['worker']  , '')
        self.assertEqual(j['state']   , 'waiting')
        j['history'][0]['put'] = math.floor(j['history'][0]['put'])
        self.assertEqual(j['history'] , [{
            'queue'    : 'testing',
            'put'      : math.floor(time.time()),
            'popped'   : None,
            'worker'   : '',
            'completed': None
        }])
        job.delete()
    
    def test_put_pop_get(self):
        # Test putting a job on, popping it, and then making sure
        # that the history is updated
        job = qless.Job({'name': 'test_put_pop_get'})
        self.q.push(job, 60)
        jobs = self.q.pop(5)
        self.assertEqual(len(jobs), 1)
        j = qless.Job.get(jobs[0]['id'])
        print j['history']
    
    def test_put_history(self):
        job = qless.Job({'name': 'test_put_history'})
        self.q.push(job, 60)
        j = qless.Job.get(job.id)        
        job.delete()
    
    def test_heartbeat(self):
        # In this test, we want to make sure that we can still 
        # keep our lock on an object if we renew it in time.
        # The gist of this test is:
        #   1) A gets an item, with positive heartbeat
        #   2) B tries to get an item, fails
        #   3) A renews its heartbeat successfully
        #   4) Both clean up
    
    def test_locks(self):
        # In this test, we're going to have two queues that point
        # to the same queue, but we're going to have them represent
        # different workers. The gist of it is this
        #   1) A gets an item, with negative heartbeat
        #   2) B gets the same item,
        #   3) A tries to renew lock on item, should fail
        #   4) B tries to renew lock on item, should succeed
        #   5) Both clean up
        # j = qless.Job({'name':'test_locks'})
        # self.q.push(job, -10)
        # # Make sure a gets a job
        # ja = self.a.pop(1)[0]
        # self.assertNotEqual(ja, None)
        # # Now, make sure that b gets that same job
        # jb = self.b.pop(1)[0]
        # self.assertNotEqual(jb, None)
        # self.assertEqual(ja['id'], jb['id'])


if __name__ == '__main__':
    unittest.main()