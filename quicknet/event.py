from threading import Thread

__all__ = ["EventThreader"]


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
        return wrapper

    def emit(self, source, event, *args, **kwargs):
        if event not in self.listeners:
            return

        callbacks = self.listeners[event]
        if type(callbacks) == tuple:
            args = EventThreader._handle_options(source, list(args), callbacks[1])
            if callbacks[1].get("thread", True):
                t = Thread(target=callbacks[0], args=args, kwargs=kwargs)
                t.start()
                return t
            else:
                return callbacks[0](*args, **kwargs)
        else:
            values = []
            for callback in callbacks:
                args = EventThreader._handle_options(source, list(args), callback[1])
                if callback[1].get("thread", True):
                    t = Thread(target=callback[0], args=args, kwargs=kwargs)
                    t.start()
                    return t
                else:
                    values.append(callback[0](*args, **kwargs))
            return values

    def _handle_options(self, args: list, kwargs: dict):
        if kwargs.get("pass_client", False):
            args.insert(0, self)
        return args
