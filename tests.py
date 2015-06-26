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
    uut.join(1)
    eq_(len(observer.get_events()), 3)
    eq_(len(observer.get_errors()), 0)

    uut.on_next(4)
    uut.on_next(5)
    uut.join(1)
    eq_(len(observer.get_events()), 5)
    eq_(len(observer.get_errors()), 0)

    uut.on_error('e')
    uut.on_error('f')
    uut.on_next(6)
    uut.on_error('g')
    uut.on_next(7)
    uut.join(1)
    eq_(len(observer.get_events()), 7)
    eq_(len(observer.get_errors()), 3)

    eq_(observer.get_events(), (1,2,3,4,5,6,7))
    eq_(observer.get_errors(), ('e', 'f', 'g'))
    ok_(not observer.is_complete())

    uut.on_complete()
    uut.join(1)
    ok_(observer.is_complete())
    
