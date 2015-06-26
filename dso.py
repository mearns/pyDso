#! /usr/bin/env python
# vim: set fileencoding=utf-8: set encoding=utf-8:

import abc
import threading
import sys
import time

class Observer(object):
    """
    Simple interface for something that can observe an `Observable`.
    """

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def on_next(self, event):
        """
        Called by the `Observable` to which this Observer is subscribed,
        anytime an event happens.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def on_error(self, event):
        """
        Called by the `Observable` to which this Observer is subscribed,
        anytime an error happens.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def on_complete(self):
        """
        Called by the `Observable` to which this Observer is subscribed,
        when the ``Obserable`` is completed.
        """
        raise NotImplementedError()

class DefaultObserver(Observer):
    """
    A simple implementation of the `Observer` abstract class that implements
    all the required call back methods (`on_next`, `on_error`, and `on_complete`),
    but doesn't actually do anything. So you can subclass this and just override
    the ones you want.
    """
    def on_next(self, event): pass
    def on_error(self, event): pass
    def on_complete(self): pass

class PrintingObserver(Observer):
    def on_next(self, event):
        sys.stdout.write(event + '\n')
    def on_error(self, event):
        sys.stderr.write(event + '\n')
    def on_complete(self):
        sys.stdout.write('Complete')

class CollectingObsever(Observer):
    def __init__(self):
        self._events = []
        self._errors = []
        self._complete = False

    def on_next(self, event):
        self._events.append(event)

    def on_error(self, error):
        self._errors.append(error)

    def on_complete(self):
        self._complete = True

    def get_events(self):
        return tuple(self._events)

    def get_errors(self):
        return tuple(self._errors)

    def is_complete(self):
        return self._complete

class Observable(object):

    def __init__(self):
        self._observers = []
        self._threads = set()

    def _clean_threads(self):
        self._threads = {t for t in self._threads if t.isAlive()}

    def join(self, timeout=None):
        tick = time.time()
        for thread in self._threads:
            tock = time.time()
            timeleft = None if (timeout is None) else (timeout - (tock - tick))
            thread.join(timeleft)
            if timeleft <= 0:
                break
        self._clean_threads()
        return len(self._threads) == 0

    def join_all(self, timeout=None):
        return self.join(timeout)

    def get_observers(self):
        """
        Returns a tuple of all observers which have `subscribed <subscribe>`
        to this observable.
        """
        return tuple(self._observables)

    def subscribe(self, observer):
        if not isinstance(observer, Observer):
            raise TypeError('Only Observers can subscribe.')
        self._observers.append(observer)
        return observer

    def with_subscriber(self, observer):
        self.subscribe(observer)
        return self

    def _fire_to(self, target, args=tuple()):
        t = threading.Thread(target=target, args=args)
        self._threads.add(t)
        t.start()

    def _fire_next(self, event):
        for o in self._observers:
            self._fire_to(o.on_next, (event,))

    def _fire_error(self, event):
        for o in self._observers:
            self._fire_to(o.on_error, (event,))

    def _fire_complete(self):
        for o in self._observers:
            self._fire_to(o.on_complete)

    def map(self, func, *args, **kwargs):
        return MappedObservable(func, self, *args, **kwargs)

    def filter(self, func, *args, **kwargs):
        return FilteredObservable(func, self, *args, **kwargs)

    def merge(self, *sources, **kwargs):
        return MergedObservable(self, *sources, **kwargs)

    def combine_last(self, *sources, **kwargs):
        return CombinedLastObservable(self, *sources, **kwargs)

class DerivedObservable(Observable, Observer):
    def __init__(self, source, propagate_errors=False, propagate_complete=False):
        if not isinstance(source, Observable):
            raise TypeError('Source must be an Observable')
        self._source = source
        source.subscribe(self)
        self.propagate_errors = propagate_errors
        self.propagate_complete = propagate_complete
        Observable.__init__(self)

    def join_all(self, timeout=None):
        tick = time.time()
        if not self._source.join_all(timeout):
            return False
        timeleft = None if (timeout is None) else (timeout - (time.time() - tick))
        return self.join(timeleft)

    def with_propagate_errors(self, do_propagate):
        self.propagate_errors = do_propagate
        return self

    def with_propagate_complete(self, do_propagate):
        self.propagate_complete = do_propagate
        return self

    def on_next(self, event):
        self._fire_next(event)

    def on_error(self, event):
        if self.propagate_errors:
            self._fire_error(event)

    def on_complete(self):
        if self.propagate_complete:
            self._fire_complete()
        
class MappedObservable(DerivedObservable):
    def __init__(self, func, source, *args, **kwargs):
        self._func = func
        super(MappedObservable, self).__init__(source, *args, **kwargs)

    def on_next(self, event):
        super(MappedObservable, self).on_next(self._func(event))

class FilteredObservable(DerivedObservable):
    def __init__(self, func, source, *args, **kwargs):
        self._func = func
        super(FilteredObservable, self).__init__(source, *args, **kwargs)

    def on_next(self, event):
        if self._func(event):
            super(FilteredObservable, self).on_next(event)

class MergedObservable(DerivedObservable):
    def __init__(self, source, *sources, **kwargs):
        for s in sources:
            if not isinstance(s, Observable):
                raise TypeError('Can only merge Observables')
        super(MergedObservable, self).__init__(source, **kwargs)
        self._sources = sources
        for s in sources:
            s.subscribe(self)

    def join_all(self, timeout=None):
        tick = time.time()
        for source in self._sources:
            timeleft = None if (timeout is None) else (timeout - (time.time() - tick))
            if timeleft <= 0:
                break
            if not source.join_all(timeleft):
                return False
        timeleft = None if (timeout is None) else (timeout - (time.time() - tick))
        return super(MergedObservable, self).join_all(timeleft)


class CombinedLastObservable(Observable):
    def __init__(self, *sources, **kwargs):
        propagate_errors=kwargs.pop('propagate_errors', False)
        propagate_complete=kwargs.pop('propagate_complete', False)
        if kwargs:
            raise TypeError('Unsupported argument%s: %s' % ('s' if len(kwargs) > 1 else '', ', '.join(k for k in kwargs)))

        for s in sources:
            if not isinstance(s, Observable):
                raise TypeError('Can only merge Observables')

        self._last_values = [None for s in sources]
        self._has_value = [False for s in sources]

        self._sources = sources
        for i, s in enumerate(sources):
            s.subscribe(self.PrivateObserver(self, i))

        super(CombinedLastObservable, self).__init__()

    def join_all(self, timeout=None):
        tick = time.time()
        for source in self._sources:
            timeleft = None if (timeout is None) else (timeout - (time.time() - tick))
            if timeleft <= 0:
                break
            if not source.join_all(timeleft):
                return False
        timeleft = None if (timeout is None) else (timeout - (time.time() - tick))
        return super(CombinedLastObservable, self).join_all(timeleft)

    def set_last(self, idx, event):
        self._last_values[idx] = event
        self._has_value[idx] = True

        if all(self._has_value):
            self._fire_next(tuple(self._last_values))

    class PrivateObserver(DefaultObserver):
        def __init__(self, parent, idx):
            self._idx = idx
            self._parent = parent

        def on_next(self, event):
            self._parent.set_last(self._idx, event)



class Subject(Observable, Observer):
    """
    A `Subject` is an `Observable` _and_ an `Observer`. Everytime it receives
    an event (`on_next`, `on_error`, or `on_complete`) it passes it on to its
    subscribers.

    This is a simple way to create an `Observable`, you can just pass event in
    directly. Sort a "manual" ``Observable``.
    """

    def on_next(self, event):
        self._fire_next(event)

    def on_error(self, event):
        self._fire_error(event)

    def on_complete(self):
        self._fire_complete()




