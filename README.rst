============
patch-report
============

Dashboard for RAX Patches

Features
========

* Provides stats at a glance
* Handles multiple projects
* Integrates with Redmine to track issue status
* Quickly see which patches are proposed upstream

Installation
============

* Configure by copying ``etc/patch_report.cfg.sample`` to ``/etc`` and tweaking it
* Install crontab using ``etc/crontab.sample`` as a guide
* Run the server ``bin/serve gunicorn``


Code Upgrades
=============

* Since the pickle format (used to exchange data) is tied to a particular
  version of patch-report, when upgrading the code, it's important that you
  clear them out. To do this, use the ``bin/clear-cache`` command.


Architecture
============

The app consists of two parts, the *frontend* and the *backend*.

The frontend is a web server that serves up data collected by the backend.

The backend are a set of *refresh* scripts run by cron that perform the remote
API calls to collect data do some additional roll-up processing.

The interchange format between the frontend and the backend is a pickle file.

The pickle files used to send data to the frontend also act as a data cache.

**NOTE: the pickle files are ephemeral, you can delete them, and they will be
regenerated on the next run of cron**

::

                                        +--------------+  +--------------+
    +-----+                             |              |  |              |
    |     |                             |  Patch Repo  |  |    GitHub    |
    |  F  |          +---------+        |              |  |              |
    |  r  |          |         |        +--------------+  +--------------+
    |  o  |  Pickle  |         |    Local Disk  |                ||
    |  n  | <------  | Backend | <--------------+                ||
    |  t  |          |         |                     HTTP        ||
    |  e  |          |         | <==============++===============++
    |  n  |          +---------+                ||               ||
    |  d  |               |             +--------------+  +--------------+
    |     |           +------+          |              |  |              |
    +-----+           | cron |          |    Redmine   |  |    Gerrit    |
                      +------+          |              |  |              |
                                        +--------------+  +--------------+


Cache Refresh
=============

The patch repos are refreshed every 5 minutes.

Redmine issues, Gerrit changes, and GitHub repos are refreshed once a day.
