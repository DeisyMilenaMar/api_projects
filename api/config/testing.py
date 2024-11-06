from fnmatch import fnmatch
import unittest

from django.test.runner import DiscoverRunner


class TestLoader(unittest.TestLoader):
    def _match_path(self, path, full_path, pattern):
        return fnmatch(full_path, pattern)


class DirBasedTestRunner(DiscoverRunner):

    test_loader = TestLoader()

    def __init__(self, *args, **kwargs):
        kwargs['pattern'] = '*/tests/*.py'
        super().__init__(*args, **kwargs)

    def setup_test_environment(self, *args, **kwargs):
        from django.apps import apps
        self.unmanaged_models = [
            model for model in apps.get_models() if not model._meta.managed
        ]
        for model in self.unmanaged_models:
            model._meta.managed = True
        super().setup_test_environment(*args, **kwargs)

    def teardown_test_environment(self, *args, **kwargs):
        super().teardown_test_environment(*args, **kwargs)
        for model in self.unmanaged_models:
            model._meta.managed = False
