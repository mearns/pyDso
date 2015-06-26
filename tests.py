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

def test_propagate_erros_and_complete():

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


    
