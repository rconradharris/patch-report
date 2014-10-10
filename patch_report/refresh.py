"""
Refresh patch_report state.

Intended to be run from a cron-job.

python patch_report/refresh.py
"""
import patch_report


if __name__ == '__main__':
    patch_report.refresh_patch_series()
