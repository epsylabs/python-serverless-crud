import abc


class API(abc.ABC):
    @abc.abstractmethod
    def registry(self, model):
        pass

    @abc.abstractmethod
    def handle(self, event, context):
        pass

    def __call__(self, event, context, *args, **kwargs):
        return self.handle(event, context)
