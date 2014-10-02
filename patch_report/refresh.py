"""
Refresh patch_report state.

Intended to be run from a cron-job.

python patch_report/refresh.py <patch-repo-path>
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
    if len(sys.argv) < 2:
        print >> sys.stderr, "usage: refresh.py <patch-repo-path>"
        sys.exit(1)

    path = sys.argv[1]
    if not os.path.exists(path):
        print >> sys.stderr, "error: patch-repo-path doesn't"\
                             " exist '%s'" % path
        sys.exit(1)

    filename = patch_report.get_state_file()
    refresh_git(path)
    patch_set = patch_report.PatchSet.refresh_and_write_to_file(filename, path)
