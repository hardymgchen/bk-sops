# -*- coding: utf-8 -*-
import logging

from django.core.management import BaseCommand
from django.db import transaction
from django_celery_beat.models import (
    IntervalSchedule,
    CrontabSchedule,
    PeriodicTasks,
    PeriodicTask,
)

from blueapps.contrib.bk_commands.management.handlers.migrate_from_djcelery_handler import (
    execute,
    DjIntervalSchedule,
    DjCrontabSchedule,
    DjPeriodicTask,
    DjPeriodicTasks,
)

logger = logging.getLogger("blueapps")


class Command(BaseCommand):
    ALL_MIGRATED_DB_TABLE = (IntervalSchedule, CrontabSchedule, PeriodicTasks, PeriodicTask)
    NEW_NO_TIMEZONE_DB_TABLE = (IntervalSchedule, PeriodicTasks, PeriodicTask)
    OLD_DB_TABLE = (DjIntervalSchedule, DjPeriodicTasks, DjPeriodicTask)

    def add_arguments(self, parser):
        parser.add_argument("-tz", help="指定旧版djcelery运行的时区")

    @transaction.atomic
    def handle(self, *args, **options):
        tz = "UTC"  # pylint: disable=invalid-name
        if options["tz"]:
            tz = options["tz"]  # pylint: disable=invalid-name
        # 检查目标数据库是否有数据
        if not self.check_db_has_data():
            return
        # 迁移带时区的表
        execute(CrontabSchedule, DjCrontabSchedule, tz)
        # 迁移不带时区的表
        for new_table, old_table in zip(self.NEW_NO_TIMEZONE_DB_TABLE, self.OLD_DB_TABLE):
            execute(new_table, old_table)

    def check_db_has_data(self):
        for db in self.ALL_MIGRATED_DB_TABLE:
            if db.objects.exists():
                logger.warning(
                    "The target database {} already has data and cannot be migrated".format(db._meta.model_name)
                )
                return False
        return True
