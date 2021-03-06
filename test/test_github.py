import json
import re
import unittest
import warnings

import responses

import base

warnings.simplefilter('ignore')

commit_data = """
{
  "ref": "refs/heads/master",
  "after": "a96dbcb0e566ba8330b2b24ce0f31ed53a29e0ff",
  "before": "4a666d1d66e5db362742acee3c6fed4ca0b77a97",
  "created": false,
  "deleted": false,
  "forced": false,
  "compare": "https://github.com/test-user/test-hooks/compare/4a666d1d66e5...a96dbcb0e566",
  "commits": [
    {
      "id": "a96dbcb0e566ba8330b2b24ce0f31ed53a29e0ff",
      "distinct": true,
      "message": "a commit message",
      "timestamp": "2014-06-11T18:39:09-04:00",
      "url": "https://github.com/test-user/test-hooks/commit/a96dbcb0e566ba8330b2b24ce0f31ed53a29e0ff",
      "author": {
        "name": "Some User",
        "email": "blah@gmail.com",
        "username": "blah"
      },
      "committer": {
        "name": "Some User",
        "email": "blah@gmail.com",
        "username": "blah"
      },
      "added": [

      ],
      "removed": [

      ],
      "modified": [
        "1"
      ]
    }
  ],
  "head_commit": {
    "id": "a96dbcb0e566ba8330b2b24ce0f31ed53a29e0ff",
    "distinct": true,
    "message": "4",
    "timestamp": "2014-06-11T18:39:09-04:00",
    "url": "https://github.com/test-user/test-hooks/commit/a96dbcb0e566ba8330b2b24ce0f31ed53a29e0ff",
    "author": {
      "name": "A user",
      "email": "someone@trythis.com",
      "username": "blah"
    },
    "committer": {
      "name": "A user",
      "email": "someone@trythis.com",
      "username": "blah"
    },
    "added": [

    ],
    "removed": [

    ],
    "modified": [
      "1"
    ]
  },
  "repository": {
    "id": 20746319,
    "name": "test-hooks",
    "url": "https://github.com/test-user/test-hooks",
    "description": "testing webhooks",
    "watchers": 0,
    "stargazers": 0,
    "forks": 0,
    "fork": false,
    "size": 0,
    "owner": {
      "name": "test-user",
      "email": "blah@gmail.com"
    },
    "private": false,
    "open_issues": 0,
    "has_issues": true,
    "has_downloads": true,
    "has_wiki": true,
    "created_at": 1402525177,
    "pushed_at": 1402526351,
    "master_branch": "master"
  },
  "pusher": {
    "name": "blah",
    "email": "blah@gmail.com"
  }
}
"""

issue_opened_data = """
{
  "action": "opened",
  "issue": {
    "url": "https://api.github.com/repos/jsbronder/fzsl/issues/2",
    "labels_url": "https://api.github.com/repos/jsbronder/fzsl/issues/2/labels{/name}",
    "comments_url": "https://api.github.com/repos/jsbronder/fzsl/issues/2/comments",
    "events_url": "https://api.github.com/repos/jsbronder/fzsl/issues/2/events",
    "html_url": "https://github.com/jsbronder/fzsl/issues/2",
    "id": 43301282,
    "number": 2,
    "title": "issue-title",
    "user": {
      "login": "jsbronder",
      "id": 65322
    },
    "state": "open",
    "locked": false,
    "assignee": null,
    "milestone": null,
    "comments": 0,
    "created_at": "2014-09-20T05:20:52Z",
    "updated_at": "2014-09-20T05:20:52Z",
    "closed_at": null,
    "body": ""
  },
  "repository": {
    "id": 24253229,
    "name": "test-hooks",
    "full_name": "test-user/test-hooks",
    "owner": {
      "login": "test-user"
    },
    "private": false,
    "html_url": "https://github.com/test-user/test-hooks",
    "description": "testing webhooks",
    "forks": 0,
    "open_issues": 2,
    "watchers": 0,
    "default_branch": "master"
  },
  "sender": {
    "login": "jsbronder"
  }
}
"""

class GithubTester(unittest.TestCase):
    """
    Test the github plugin without webhook configuration.
    """
    def setUp(self):
        config = {
            'repos': {
                'test-user/test-hooks': {
                    base.TEST_CHANNEL: ['push', 'issues']
                },
            },
        }
        self._plugin = base.load_plugin('github.py', 'Github', config=config)
        self._plugin.shorten = lambda x : '<shorturl>'
        self._proto = base.TestProto([self._plugin])

    @base.net_test
    def test_query_real(self):
        m = self._plugin.status
        self.assertIsNotNone(re.search('^[0-9-]{10}T[0-9:]{8}Z:  \[[a-z]*\]', m))

    @responses.activate
    def test_query(self):
        status = {
                'status': 'good',
                'body': 'Everything operation normally',
                'created_on': '2000-01-01T01:02:03Z'}
        base.create_json_response('.*github\.com.*', status)

        m = self._plugin.status
        self.assertEqual(m, '%s:  [%s]' % (status['created_on'], status['status']))

    @responses.activate
    def test_msg(self):
        status = {
                'status': 'good',
                'body': 'Everything operation normally',
                'created_on': '2000-01-01T01:02:03Z'}
        base.create_json_response('.*github.com.*', status)

        self._proto.privmsg('tester', base.TEST_CHANNEL, '!github')
        self.assertEqual(1, len(self._proto.msgs))
        self.assertEqual(self._proto.msgs[0][2], '%s:  [%s]' % (status['created_on'], status['status']))

    def test_webhook_push(self):
        data = json.loads(commit_data)
        self._plugin.handle_push(data)
        self.assertEqual(2, len(self._proto.msgs))
        self.assertIn('pushed 1 commit to', self._proto.msgs[0][2])
        self.assertIn('<shorturl>', self._proto.msgs[1][2])
        self.assertIn('a commit message', self._proto.msgs[1][2])
        self.assertIn('a96dbcb', self._proto.msgs[1][2])

    def test_issue_webhook(self):
        data = json.loads(issue_opened_data)
        self._plugin.handle_issue(data)
        self.assertEqual(1, len(self._proto.msgs))
        self.assertIn(
                'jsbronder opened issue 2: issue-title -- <shorturl>',
                self._proto.msgs[0][2])


def main():
    unittest.main()

if __name__ == '__main__':
    main()
