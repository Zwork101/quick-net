import logging as log
from threading import Thread, local

from quicknet.utils import check_annotations

__all__ = ["EventThreader", "ClientWorker"]
ClientWorker = local()


class EventThreader:

    def __init__(self):
        self.listeners = {}

    def on(self, event, **options):
        def wrapper(func):
            if event in self.listeners:
                if type(self.listeners[event]) == tuple:
                    other_event = self.listeners[event]
                    self.listeners[event] = []
                    self.listeners[event].append((func, options))
                    self.listeners[event].append(other_event)
                else:
                    self.listeners[event].append((func, options))
            else:
                self.listeners[event] = (func, options)
            log.debug("Event handler for {event} added.".format(event=event))
        return wrapper

    def emit(self, source, event, *args, **kwargs):
        if event not in self.listeners:
            return

        callbacks = self.listeners[event]
        if type(callbacks) == tuple:
            if callbacks[1].get("enforce_annotations", False):
                if not check_annotations(callbacks[0], args, kwargs):
                    log.warning("Invalid values were passed when matching annotations, not calling.")
                    return

            if callbacks[1].get("thread", True):
                args = list(args)
                args.insert(0, source)
                args.insert(1, callbacks[0])
                t = Thread(target=self._run_with_ctx, args=args, kwargs=kwargs)
                t.start()
                log.debug("Threaded event {event} from {source} started.".format(event=event, source=source))
                return t
            else:
                log.debug("Non-threaded event {event} from {source} started.".format(event=event, source=source))
                return self._run_with_ctx(*args, **kwargs)
        else:
            for callback in callbacks:
                if callback[1].get("enforce_annotations", False):
                    if not check_annotations(callback[0], args, kwargs):
                        log.warning("Invalid values were passed when matching annotations.")
                        return

                if callback[1].get("thread", True):
                    args = list(args)
                    args.insert(0, source)
                    args.insert(1, callback[0])
                    t = Thread(target=self._run_with_ctx, args=args, kwargs=kwargs)
                    t.start()
                    log.debug("Threaded event {event} from {source} started.".format(event=event, source=source))
                    return t
                else:
                    log.debug("Non-threaded event {event} from {source} started.".format(event=event, source=source))
                    return self._run_with_ctx(*args, **kwargs)

    @staticmethod
    def _run_with_ctx(ctx, target, *args, **kwargs):
        for key in dir(ctx):
            if not hasattr(ClientWorker, key):
                setattr(ClientWorker, key, getattr(ctx, key))
        log.debug("{ctx} copied to proxy ClientWorker".format(ctx=ctx))
        target(*args, **kwargs)
