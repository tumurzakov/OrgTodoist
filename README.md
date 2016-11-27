# OrgTodoist

Sync OrgMode file with Todoist active tasks

* Sync new tasks from Todoist to Org file
* Complete tasks in Todoist if task is `DONE` in Org file

## Install

Put your Todoist token and path to OrgMode file into `config.py` and add `run.sh` to your crontab.

## Notes

* `SCHEDULED` dated must be in `<2016-11-28>` format, otherwise it will be overwrited with empty string
