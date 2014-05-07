from multiprocessing.pool import Pool, ThreadPool


class _ResultsPoolMixin(object):
    """multiprocessing.Pool boilerplate wrapper

- Stores results on a results property
- Task result successes are aggregated by the sucessful property

"""
    def __init__(self, *args, **kwargs):
        super(_ResultsPoolMixin, self).__init__(*args, **kwargs)
        self.results = list()

    def apply_async(self, *args, **kwargs):
        result = super(_ResultsPoolMixin, self).apply_async(*args, **kwargs)
        self.results.append(result)
        return result

    def map_async(self, *args, **kwargs):
        result = super(_ResultsPoolMixin, self).map_async(*args, **kwargs)
        self.results.append(result)
        return result

    @property
    def successful(self):
        if self.results:
            return all([result.successful() for result in self.results])
        else:
            return None

    def __enter__(self, *args, **kwargs):
        return type(self)(*args, **kwargs)

    def __exit__(self, *args, **kwargs):
        self.close()
        self.join()


class ResultsPool(_ResultsPoolMixin, Pool):
    pass


class ResultsThreadPool(_ResultsPoolMixin, ThreadPool):
    pass
