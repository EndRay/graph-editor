class Subscribable:
    def __init__(self):
        self.subscribers = []

    def subscribe(self, func):
        self.subscribers.append(func)

    def unsubscribe(self, func):
        self.subscribers.remove(func)

    def notify(self, *args, **kwargs):
        for subscriber in self.subscribers:
            subscriber(*args[1:], **kwargs)


def subscribable(func):
    def wrapper(*args, **kwargs):
        wrapper.subscribable.notify(*args, **kwargs)
        result = func(*args, **kwargs)
        return result

    wrapper.subscribable = Subscribable()
    return wrapper