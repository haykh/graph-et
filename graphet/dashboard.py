# Preliminary embedding of Dask dashboard


class Dashboard:
    def __init__(self, **kwargs):
        from dask.distributed import Client

        self._client = Client(**kwargs)

    def restart(self):
        self._client.restart()

    def close(self):
        self._client.close()

    @property
    def client(self):
        return self._client

    def _repr_html_(self):
        return self.client._repr_html_()
