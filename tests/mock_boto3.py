import mock

import timewarp.ec2

class Boto3Mock(object):
    def __init__(self):
        self._session = mock.patch("timewarp.ec2.Session").start()

        self._resource = mock.Mock()
        self._instance = mock.Mock()
        self._resource.Instance.return_value = self._instance
        self._session.resource.return_value = self._resource

        self._client = mock.Mock()
        self._session.client.return_value = self._client

        self._paginator = mock.Mock()
        self._client.get_paginator.return_value = self._paginator

    def paginator(self):
        return self._paginator

    def instance(self):
        return self._instance

    def teardown(self):
        self._session.stop()

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
