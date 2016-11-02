#!/usr/bin/env python
"""
This script is designed to trigger jobs through Release Engineering's
buildapi self-serve service.

The API documentation is in here (behind LDAP):
https://secure.pub.build.mozilla.org/buildapi/self-serve

The docs can be found in here:
http://moz-releng-buildapi.readthedocs.org
"""
import json
import logging

import requests

BUG_BOOKMARK = 'https://bugzilla.mozilla.org/enter_bug.cgi?assigned_to=nobody%40mozilla.org&bug_file_loc=http%3A%2F%2F&bug_ignored=0&bug_severity=major&bug_status=NEW&cc=armenzg%40mozilla.com&cf_blocking_fennec=---&cf_fx_iteration=---&cf_fx_points=---&cf_status_firefox49=---&cf_status_firefox50=---&cf_status_firefox51=---&cf_status_firefox52=---&cf_status_firefox_esr45=---&cf_tracking_firefox49=---&cf_tracking_firefox50=---&cf_tracking_firefox51=---&cf_tracking_firefox52=---&cf_tracking_firefox_esr45=---&cf_tracking_firefox_relnote=---&component=Buildduty&contenttypemethod=autodetect&contenttypeselection=text%2Fplain&defined_groups=1&flag_type-4=X&flag_type-481=X&flag_type-607=X&flag_type-674=X&flag_type-720=X&flag_type-721=X&flag_type-737=X&flag_type-800=X&flag_type-803=X&flag_type-905=X&form_name=enter_bug&maketemplate=Remember%20values%20as%20bookmarkable%20template&op_sys=Unspecified&priority=--&product=Release%20Engineering&qa_contact=bugspam.Callek%40gmail.com&rep_platform=Unspecified&short_desc=Buildapi%20is%20down&target_milestone=---&version=unspecified'  # flake8: noqa
HOST_ROOT = 'https://secure.pub.build.mozilla.org/buildapi'
LOG = logging.getLogger('buildapi')
SELF_SERVE = '{}/self-serve'.format(HOST_ROOT)
TCP_TIMEOUT=10

DEFAULT_COUNT_NUM = 1
DEFAULT_PRIORITY = 0


class BuildapiAuthError(Exception):
    pass


class BuildapiDown(Exception):
    pass


def trigger_arbitrary_job(repo_name, builder, revision, auth, files=None, dry_run=False,
                          extra_properties=None):
    """
    Request buildapi to trigger a job for us.

    We return the request or None if dry_run is True.

    Raises BuildapiAuthError if credentials are invalid.
    """
    assert len(revision) == 40, \
        'We do not accept revisions shorter than 40 chars'
    url = _builders_api_url(repo_name, builder, revision)
    payload = _payload(repo_name, revision, files, extra_properties)

    if dry_run:
        LOG.info("Dry-run: We were going to request a job for '{}'".format(builder))
        LOG.info("         with this payload: {}".format(str(payload)))
        LOG.info("         with these files: {}".format(files))
        return None

    # NOTE: A good response returns json with request_id as one of the keys
    req = requests.post(
        url,
        headers={'Accept': 'application/json'},
        data=payload,
        auth=auth,
        timeout=TCP_TIMEOUT,
    )
    if req.status_code == 401:
        raise BuildapiAuthError("Your credentials were invalid. Please try again.")
    elif req.status_code == 503:
        raise BuildapiDown("Please file a bug {}".format(url))

    try:
        req.json()
        return req

    except ValueError:
        LOG.info('repo: {}, builder: {}, revision: {}'.format(repo_name, builder, revision))
        LOG.error("We did not get info from %s (status code: %s)" % (url, req.status_code))
        return None


def make_retrigger_request(repo_name, request_id, auth, count=DEFAULT_COUNT_NUM,
                           priority=DEFAULT_PRIORITY, dry_run=True):
    """
    Retrigger a request using buildapi self-serve. Returns a request.

    Buildapi documentation:
    POST  /self-serve/{branch}/request
    Rebuild `request_id`, which must be passed in as a POST parameter.
    `priority` and `count` are also accepted as optional
    parameters. `count` defaults to 1, and represents the number
    of times this build  will be rebuilt.
    """
    url = '{}/{}/request'.format(SELF_SERVE, repo_name)
    payload = {'request_id': request_id}

    if count != DEFAULT_COUNT_NUM or priority != DEFAULT_PRIORITY:
        payload.update({'count': count,
                        'priority': priority})

    if dry_run:
        LOG.info('We would make a POST request to %s with the payload: %s' % (url, str(payload)))
        return None

    LOG.info("We're going to re-trigger an existing completed job with request_id: %s %i time(s)."
             % (request_id, count))
    req = requests.post(
        url,
        headers={'Accept': 'application/json'},
        data=payload,
        auth=auth
    )
    # TODO: add debug message with job_id URL.
    return req


def make_cancel_request(repo_name, request_id, auth, dry_run=True):
    """
    Cancel a request using buildapi self-serve. Returns a request.

    Buildapi documentation:
    DELETE /self-serve/{branch}/request/{request_id} Cancel the given request
    """
    url = '{}/{}/request/{}'.format(SELF_SERVE, repo_name, request_id)

    if dry_run:
        LOG.info('We would make a DELETE request to %s.' % url)
        return None

    LOG.info("We're going to cancel the job at %s" % url)
    req = requests.delete(url, auth=auth)
    # TODO: add debug message with the canceled job_id URL. Find a way
    # to do that without doing an additional request.
    return req


def make_retrigger_build_request(repo_name, build_id, auth, count=DEFAULT_COUNT_NUM,
                                 priority=DEFAULT_PRIORITY, dry_run=True):
    """
    Retrigger a build using buildapi self-serve. Returns a request.

    Buildapi documentation:
    POST	/self-serve/{branch}/build
    Rebuild `build_id`, which must be passed in as a POST
    `priority` and `count` are also accepted as optional
    parameters. `count` defaults to 1, and represents the number
    of times this build  will be rebuilt.
    """
    url = '{}/{}/build'.format(SELF_SERVE, repo_name)
    payload = {'build_id': build_id}

    if count != DEFAULT_COUNT_NUM or priority != DEFAULT_PRIORITY:
        payload.update({'count': count,
                        'priority': priority})

    if dry_run:
        LOG.info('We would make a POST request to %s with the payload: %s' % (url, str(payload)))
        return None

    LOG.info("We're going to re-trigger an existing completed job with build_id: %s %i time(s)."
             % (build_id, count))
    req = requests.post(
        url,
        headers={'Accept': 'application/json'},
        data=payload,
        auth=auth
    )

    return req


def make_query_repositories_request(auth, dry_run=True):
    url = "%s/branches?format=json" % SELF_SERVE
    LOG.debug("About to fetch %s" % url)
    if dry_run:
        LOG.info('We would make a GET request to %s.' % url)
        return None

    req = requests.get(url, auth=auth, timeout=TCP_TIMEOUT)
    if req.status_code == 401:
        raise BuildapiAuthError("Your credentials were invalid. Please try again.")
    return req.json()


def _builders_api_url(repo_name, builder, revision):
    return r'''%s/%s/builders/%s/%s''' % (
        SELF_SERVE,
        repo_name,
        builder,
        revision
    )


def _jobs_api_url(job_id):
    """This is the URL to a self-serve job request (scheduling, canceling, etc)."""
    return r'''%s/jobs/%s''' % (SELF_SERVE, job_id)


def _payload(repo_name, revision, files=[], extra_properties=None):

    # These properties are needed for Treeherder to display running jobs.
    # Additional properties may be specified by a user.
    props = {
        "branch": repo_name,
        "revision": revision,
    }
    props.update(extra_properties or {})

    payload = {
        'properties': json.dumps(props, sort_keys=True)
    }

    if files and all(files):
        payload['files'] = json.dumps(files)

    return payload


#
# Functions to query
#
def query_jobs_schedule(repo_name, revision, auth):
    """
    Query Buildapi for jobs.
    """
    url = "%s/%s/rev/%s?format=json" % (SELF_SERVE, repo_name, revision)
    LOG.debug("About to fetch %s" % url)
    req = requests.get(url, auth=auth, timeout=TCP_TIMEOUT)

    # If the revision doesn't exist on buildapi, that means there are
    # no buildapi jobs for this revision
    if req.status_code not in [200]:
        return []

    return req.json()


def query_jobs_url(repo_name, revision):
    """Return URL of where a developer can login to see the scheduled jobs for a revision."""
    return "%s/%s/rev/%s" % (SELF_SERVE, repo_name, revision)


def query_pending_jobs(auth, repo_name=None, return_raw=False):
    """Return pending jobs"""
    url = '%s/pending?format=json' % HOST_ROOT
    LOG.debug('About to fetch %s' % url)
    req = requests.get(url, auth=auth, timeout=TCP_TIMEOUT)

    # If the revision doesn't exist on buildapi, that means there are
    # no builapi jobs for this revision
    if req.status_code not in [200]:
        return []

    raw = req.json()

    # If we don't want the data structure to be reduced
    if return_raw:
        return raw

    # If we only want pending jobs of a specific repo
    if repo_name and repo_name in list(raw['pending'].keys()):
        repo_list = [repo_name]
    else:
        repo_list = list(raw['pending'].keys())

    # Data structure to return
    data = {}
    for repo in repo_list:
        data[repo] = {}
        repo_jobs = raw['pending'][repo]
        for revision in repo_jobs.items():
            data[repo][revision[0]] = revision[1]

    return data
