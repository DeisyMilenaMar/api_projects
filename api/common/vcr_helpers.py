from contextlib import contextmanager
from os import path
from django.conf import settings
import vcr as orig_vcr


def vcr_fpg(function):
    """Generates the cassette path for a Django unittest method."""
    mod_str = str(function.__self__.__class__.__module__)
    submods = mod_str.split('.')
    app_name = submods[0]
    path_comps = (
        [app_name, 'vcr_cassettes'] + submods[2:] +
        [
            function.__self__.__class__.__name__,
            '{}.vcr'.format(function.__name__),
        ]
    )
    target_path = path.join(*path_comps)
    return target_path


vcr = orig_vcr.VCR(func_path_generator=vcr_fpg)

vcr_inject = orig_vcr.VCR(func_path_generator=vcr_fpg, inject_cassette=True)