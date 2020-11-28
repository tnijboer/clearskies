import pinject
import requests
from .columns import Columns


class BindingSpec(pinject.BindingSpec):
    object_graph = None

    def provide_requests(self):
        return requests

    def provide_object_graph(self):
        """
        This is very hacky.

        The object graph is the dependency injection container, which is never supposed to be
        injected.  However, there are some cases where it is just easier this way, so I'm cheating
        and making it injectable.  Unfortunately, pinject doesn't natively support this, so instead
        the startup of the given service will inject the object graph it builds into the binding spec
        so that we can provide it here.
        """
        if self.object_graph is None:
            raise ValueError("You must manually provide the object graph before requesting it!")

        return self.object_graph

    def provide_columns(self):
        return Columns(self.provide_object_graph())