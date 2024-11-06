from contextlib import contextmanager
from os import path

from django.conf import settings

import vcr as orig_vcr


def vcr_fpg(function):
    """provides a path for VCR cassettes associated to the received function.

    It assumes `function` is a unittest method, part of a Django project test
    suite.

    The resulting path will be:
        $PROJECT_DIR/$DJANGO_APP/vcr_cassettes/ ...
        $MODULE_PATH_FOR_TEST_CLASS/$TEST_CLASS/${TEST_METHOD}.vcr

    E.g., for a test located at
    gateway_topup.tests.services.TopUpAccountTestCase.test_normal_topup, the
    resulting path will be
    $PROJECT_DIR/gateway_topup/services/TopUpAccountTestCase/test_normal_topup.vcr

    Arguments:
        function (method): the method we want to generate a cassette path for.

    Returns:
        (str): the path for the cassette.
    """
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