import json
import unittest

from mock import patch, Mock

import buildapi_client
from buildapi_client.buildapi_client import SELF_SERVE

POST_RESPONSE = """{
    "body": {
        "msg": "Ok",
        "errors": false},
    "request_id": 1234567
    }
"""


def mock_response(content, status):
    """
    Mock of requests.get().
    The object returned must have content, status_code and reason
    properties and a json method.
    """
    response = Mock()
    response.content = content

    def mock_response_json():
        return json.loads(content)

    response.json = mock_response_json
    response.status_code = status
    response.reason = 'OK'
    return response


class TestTriggerJob(unittest.TestCase):

    """Test that trigger_arbitrary_job makes the right POST requests."""

    @patch('requests.post', return_value=mock_response(POST_RESPONSE, 200))
    def test_call_without_dry_run(self, post):
        """trigger_arbitrary_job should call requests.post."""
        buildapi_client.trigger_arbitrary_job(
            "repo", "builder", "123456123456", auth=None, dry_run=False)
        # We expect that trigger_arbitrary_job will call requests.post
        # once with the following arguments
        post.assert_called_once_with(
            '%s/%s/builders/%s/%s' % (SELF_SERVE, "repo", "builder", "123456123456"),
            headers={'Accept': 'application/json'},
            data={'properties':
                  '{"branch": "repo", "revision": "123456123456"}'},
            auth=None)

    @patch('requests.post', return_value=mock_response(POST_RESPONSE, 200))
    def test_call_with_dry_run(self, post):
        """trigger_arbitrary_job should return None when dry_run is True."""
        self.assertEquals(
            buildapi_client.trigger_arbitrary_job(
                "repo", "builder", "123456123456", auth=None, dry_run=True), None)
        # trigger_arbitrary_job should not call requests.post when dry_run is True
        assert post.call_count == 0

    @patch('requests.post', return_value=mock_response(POST_RESPONSE, 401))
    def test_bad_response(self, post):
        """trigger_arbitrary_job should raise an BuildapiAuthError if it receives a bad response."""
        with self.assertRaises(buildapi_client.BuildapiAuthError):
            buildapi_client.trigger_arbitrary_job(
                "repo", "builder", "123456123456", auth=None, dry_run=False)


class TestMakeRetriggerRequest(unittest.TestCase):

    """Test that make_retrigger_request makes the right POST requests."""

    @patch('requests.post', return_value=mock_response(POST_RESPONSE, 200))
    def test_call_without_dry_run(self, post):
        """make_retrigger_request should call requests.post."""
        buildapi_client.make_retrigger_request("repo", "1234567", auth=None, dry_run=False)
        # We expect that make_retrigger_request will call requests.post
        # once with the following arguments
        post.assert_called_once_with(
            '%s/%s/request' % (SELF_SERVE, "repo"),
            headers={'Accept': 'application/json'},
            data={'request_id': '1234567'},
            auth=None)

    @patch('requests.post', return_value=mock_response(POST_RESPONSE, 200))
    def test_call_with_dry_run(self, post):
        """make_retrigger_request should return None when dry_run is True."""
        self.assertEquals(
            buildapi_client.make_retrigger_request(
                "repo", "1234567", auth=None, dry_run=True), None)
        # make_retrigger_request should not call requests.post when dry_run is True
        assert post.call_count == 0

    @patch('requests.post', return_value=mock_response(POST_RESPONSE, 200))
    def test_call_with_different_priority(self, post):
        """make_retrigger_request should call requests.post with the right priority."""
        buildapi_client.make_retrigger_request(
            "repo", "1234567", priority=2, auth=None, dry_run=False)
        post.assert_called_once_with(
            '%s/%s/request' % (SELF_SERVE, "repo"),
            headers={'Accept': 'application/json'},
            data={'count': 1, 'priority': 2, 'request_id': '1234567'},
            auth=None)

    @patch('requests.post', return_value=mock_response(POST_RESPONSE, 200))
    def test_call_with_different_count(self, post):
        """make_retrigger_request should call requests.post with the right count."""
        buildapi_client.make_retrigger_request(
            "repo", "1234567", count=10, auth=None, dry_run=False)
        post.assert_called_once_with(
            '%s/%s/request' % (SELF_SERVE, "repo"),
            headers={'Accept': 'application/json'},
            data={'count': 10, 'priority': 0, 'request_id': '1234567'},
            auth=None)


class TestMakeRetriggerBuildRequest(unittest.TestCase):

    """Test that make_retrigger_build_request makes the right POST requests."""

    @patch('requests.post', return_value=mock_response(POST_RESPONSE, 200))
    def test_call_without_dry_run(self, post):
        """make_retrigger_build_request should call requests.post."""
        buildapi_client.make_retrigger_build_request("repo", "1234567", auth=None, dry_run=False)
        # We expect that make_retrigger_request will call requests.post
        # once with the following arguments
        post.assert_called_once_with(
            '%s/%s/build' % (SELF_SERVE, "repo"),
            headers={'Accept': 'application/json'},
            data={'build_id': '1234567'},
            auth=None)

    @patch('requests.post', return_value=mock_response(POST_RESPONSE, 200))
    def test_call_with_dry_run(self, post):
        """make_retrigger_build_request should return None when dry_run is True."""
        self.assertEquals(
            buildapi_client.make_retrigger_build_request(
                "repo", "1234567", auth=None, dry_run=True), None)
        # make_retrigger_build_request should not call requests.post when dry_run is True
        assert post.call_count == 0

    @patch('requests.post', return_value=mock_response(POST_RESPONSE, 200))
    def test_call_with_different_priority(self, post):
        """make_retrigger_build_request should call requests.post with the right priority."""
        buildapi_client.make_retrigger_build_request(
            "repo", "1234567", priority=2, auth=None, dry_run=False)
        post.assert_called_once_with(
            '%s/%s/build' % (SELF_SERVE, "repo"),
            headers={'Accept': 'application/json'},
            data={'count': 1, 'priority': 2, 'build_id': '1234567'},
            auth=None)

    @patch('requests.post', return_value=mock_response(POST_RESPONSE, 200))
    def test_call_with_different_count(self, post):
        """make_retrigger_build_request should call requests.post with the right count."""
        buildapi_client.make_retrigger_build_request(
            "repo", "1234567", count=10, auth=None, dry_run=False)
        post.assert_called_once_with(
            '%s/%s/build' % (SELF_SERVE, "repo"),
            headers={'Accept': 'application/json'},
            data={'count': 10, 'priority': 0, 'build_id': '1234567'},
            auth=None)


class TestMakeCancelRequest(unittest.TestCase):

    """Test that make_cancel_request makes the right DELETE requests."""

    @patch('requests.delete', return_value=Mock())
    def test_call_without_dry_run(self, delete):
        """make_cancel_request should call requests.delete."""
        buildapi_client.make_cancel_request("repo", "1234567", auth=None, dry_run=False)

        # We expect that make_cancel_request will call requests.delete
        # once with the following arguments
        delete.assert_called_once_with(
            '%s/%s/request/%s' % (SELF_SERVE, "repo", "1234567"),
            auth=None)

    @patch('requests.delete', return_value=Mock())
    def test_call_with_dry_run(self, delete):
        """make_cancel_request should return None when dry_run is True."""
        self.assertEquals(
            buildapi_client.make_cancel_request("repo", "1234567", auth=None, dry_run=True), None)
        # make_cancel_request should not call requests.delete when dry_run is True
        assert delete.call_count == 0


class TestMakeQueryRepositoriesRequest(unittest.TestCase):

    """Test that make_query_repositories_request makes the right GET requests."""

    @patch('requests.get', return_value=Mock())
    def test_call_without_dry_run(self, get):
        """make_query_repositories_request should call requests.get."""
        buildapi_client.make_query_repositories_request(auth=None, dry_run=False)

        # We expect that make_query_repositories_request will call requests.get
        # once with the following arguments
        get.assert_called_once_with(
            "%s/branches?format=json" % SELF_SERVE,
            auth=None)

    @patch('requests.get', return_value=Mock())
    def test_call_with_dry_run(self, get):
        """make_cancel_request should return None when dry_run is True."""
        self.assertEquals(
            buildapi_client.make_query_repositories_request(auth=None, dry_run=True), None)
        # make_query_repositories_request should not call requests.get when dry_run is True
        assert get.call_count == 0
