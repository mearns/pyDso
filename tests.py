#! /usr/bin/env python
# vim: set fileencoding=utf-8: set encoding=utf-8:

from dso import *

from nose.tools import *

def test_subject():
    uut = Subject()
    observer = uut.subscribe(CollectingObsever())

    eq_(len(observer.get_events()), 0)
    eq_(len(observer.get_errors()), 0)

    uut.on_next(1)
    uut.on_next(2)
    uut.on_next(3)
    ok_(uut.join_all(1))
    eq_(len(observer.get_events()), 3)
    eq_(len(observer.get_errors()), 0)

    uut.on_next(4)
    uut.on_next(5)
    ok_(uut.join_all(1))
    eq_(len(observer.get_events()), 5)
    eq_(len(observer.get_errors()), 0)

    uut.on_error('e')
    uut.on_error('f')
    uut.on_next(6)
    uut.on_error('g')
    uut.on_next(7)
    ok_(uut.join_all(1))
    eq_(len(observer.get_events()), 7)
    eq_(len(observer.get_errors()), 3)

    eq_(observer.get_events(), (1,2,3,4,5,6,7))
    eq_(observer.get_errors(), ('e', 'f', 'g'))
    ok_(not observer.is_complete())

    uut.on_complete()
    ok_(uut.join_all(1))
    ok_(observer.is_complete())

def test_map():
    
    subj = Subject()
    uut = subj.map(lambda x : 2*x)
    observer = uut.subscribe(CollectingObsever())

    subj.on_next(0)
    subj.on_next(1)
    subj.on_next(2)
    subj.on_next(3)
    subj.on_next(4)

    ok_(uut.join_all(1))

    eq_(observer.get_events(), (0, 2, 4, 6, 8))
    ok_(not observer.is_complete())

    subj.on_error('e')
    subj.on_error('f')
    ok_(uut.join_all(1))
    #Because we aren't propagating errors.
    eq_(len(observer.get_errors()), 0)

    subj.on_complete()
    ok_(uut.join_all(1))
    #Because we aren't propagating complete
    ok_(not observer.is_complete())

def test_propagate_errors():

    subj = Subject()
    uut = DerivedObservable(subj, True)
    observer = uut.subscribe(CollectingObsever())
    
    subj.on_next(0)
    subj.on_next(1)
    subj.on_next(2)
    subj.on_error('e')
    subj.on_error('f')
    subj.on_next(3)
    subj.on_error('g')

    ok_(uut.join_all(1))
    eq_(observer.get_events(), (0,1,2,3))
    eq_(observer.get_errors(), ('e', 'f', 'g'))
    ok_(not observer.is_complete())

    subj.on_complete()
    ok_(uut.join_all(1))
    #Still not propagating complete.
    ok_(not observer.is_complete())

def test_propagate_complete():

    subj = Subject()
    uut = DerivedObservable(subj, False, True)
    observer = uut.subscribe(CollectingObsever())
    
    subj.on_next(0)
    subj.on_next(1)
    subj.on_next(2)
    subj.on_error('e')
    subj.on_error('f')
    subj.on_next(3)
    subj.on_error('g')

    ok_(uut.join_all(1))
    eq_(observer.get_events(), (0,1,2,3))
    eq_(len(observer.get_errors()), 0)
    ok_(not observer.is_complete())

    subj.on_complete()
    ok_(uut.join_all(1))
    ok_(observer.is_complete())

def test_propagate_errors_and_complete():

    subj = Subject()
    uut = DerivedObservable(subj, True, True)
    observer = uut.subscribe(CollectingObsever())
    
    subj.on_next(0)
    subj.on_next(1)
    subj.on_next(2)
    subj.on_error('e')
    subj.on_error('f')
    subj.on_next(3)
    subj.on_error('g')

    ok_(uut.join_all(1))
    eq_(observer.get_events(), (0,1,2,3))
    eq_(observer.get_errors(), ('e', 'f', 'g'))
    ok_(not observer.is_complete())

    subj.on_complete()
    ok_(uut.join_all(1))
    ok_(observer.is_complete())

def test_filter():

    subj = Subject()
    uut = subj.filter(lambda x : x % 2 == 0)
    observer = uut.subscribe(CollectingObsever())

    subj.on_next(0)
    subj.on_next(1)
    subj.on_next(2)
    subj.on_next(3)
    subj.on_next(4)

    ok_(uut.join_all(1))
    eq_(observer.get_events(), (0, 2, 4))

def test_merge():

    s1 = Subject()
    s2 = Subject()
    s3 = Subject()
    uut = s1.merge(s2, s3)
    observer = uut.subscribe(CollectingObsever())

    s1.on_next(1)
    s1.on_next(2)
    s2.on_next('a')
    s3.on_next('A')
    s1.on_next(3)
    s2.on_next('a')
    s2.on_next('b')
    s3.on_next('B')
    s2.on_next('c')
    s3.on_next('C')
    s1.on_next(4)
    s2.on_next('d')
    s3.on_next('D')
    s3.on_next('E')
    s3.on_next('F')
    s2.on_next('e')

    ok_(uut.join_all(1))
    events = observer.get_events()
    eq_(len(events), 16)
    for e in (1,2,3,4,'a','b','c','d','e','A','B','C','D','E','F'):
        ok_(e in events)

def test_combine_last():

    s1 = Subject()
    s2 = Subject()
    s3 = Subject()
    uut = s1.combine_last(s2, s3, propagate_errors=True, propagate_complete=True)
    observer = uut.subscribe(CollectingObsever())

    s1.on_next(0)
    ok_(uut.join_all(1))
    eq_(len(observer.get_events()), 0)

    s2.on_next('a')
    ok_(uut.join_all(1))
    eq_(len(observer.get_events()), 0)

    s2.on_next('b')
    ok_(uut.join_all(1))
    eq_(len(observer.get_events()), 0)

    s3.on_next('A')
    ok_(uut.join_all(1))
    eq_(len(observer.get_events()), 1)
    eq_(observer.get_events()[-1], (0, 'b', 'A'))

    s3.on_next('B')
    ok_(uut.join_all(1))
    eq_(len(observer.get_events()), 2)
    eq_(observer.get_events()[-1], (0, 'b', 'B'))

    s1.on_next(1)
    s1.on_next(2)
    s1.on_next(3)
    ok_(uut.join_all(1))
    eq_(len(observer.get_events()), 5)
    eq_(observer.get_events()[-1], (3, 'b', 'B'))

    s2.on_next('c')
    ok_(uut.join_all(1))
    eq_(len(observer.get_events()), 6)
    eq_(observer.get_events()[-1], (3, 'c', 'B'))

    eq_(len(observer.get_errors()), 0)

    s1.on_error('e')
    ok_(uut.join_all(1))
    eq_(len(observer.get_errors()), 1)
    eq_(observer.get_errors()[-1], ('e', None, None))

    s1.on_error('f')
    ok_(uut.join_all(1))
    eq_(len(observer.get_errors()), 2)
    eq_(observer.get_errors()[-1], ('f', None, None))

    s3.on_error('g')
    ok_(uut.join_all(1))
    s2.on_error('h')
    ok_(uut.join_all(1))
    eq_(len(observer.get_errors()), 4)
    eq_(observer.get_errors()[-2], (None, None, 'g'))
    eq_(observer.get_errors()[-1], (None, 'h', None))

    ok_(not observer.is_complete())
    s2.on_complete()
    ok_(uut.join_all(1))
    ok_(not observer.is_complete())

    s1.on_complete()
    ok_(uut.join_all(1))
    ok_(not observer.is_complete())

    s3.on_complete()
    ok_(uut.join_all(1))
    ok_(observer.is_complete())


    
