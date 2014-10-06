"""
Refresh patch_report state.

Intended to be run from a cron-job.

python patch_report/refresh.py <patch-repo-path> <state-file>
"""
import contextlib
import os
import sys

import patch_report


@contextlib.contextmanager
def temp_chdir(dirname):
    orig_path = os.getcwd()
    os.chdir(dirname)
    try:
        yield
    finally:
        os.chdir(orig_path)


def refresh_git(path):
    with temp_chdir(path):
        os.system('git checkout master && git fetch origin && git merge origin/master')


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print >> sys.stderr, "usage: refresh.py <patch-repo-path> <state-file>"
        sys.exit(1)

    path = sys.argv[1]
    if not os.path.exists(path):
        print >> sys.stderr, "error: patch-repo-path doesn't"\
                             " exist '%s'" % path
        sys.exit(1)

    state_file = sys.argv[2]
    if not os.path.exists(path):
        print >> sys.stderr, "error: state-file doesn't exist"\
                             " '%s'" % state_file
        sys.exit(1)

    refresh_git(path)

    pr = patch_report.PatchReport(path)
    pr.refresh()

    state = patch_report.PatchRepoState(state_file)
    state.save(pr)
