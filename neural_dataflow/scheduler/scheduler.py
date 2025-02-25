"""
╔═════════════════════════════╗
║ Module: Schedule Module     ║
╚═════════════════════════════╝
"""
import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, "../../.."))
sys.path.insert(0, root_dir)

import asyncio
from datetime import datetime, time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from facss_datastream.neural_dataflow.etl_pipeline.load import DataLoader

class TaskScheduler:
    """
    Scheduled task manager with flexibility for different intervals.
    """
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.start_time = time(1, 0)
        self.end_time = time(23, 0)
        self.data_loader = DataLoader()

        self.periodic_tasks = [
            {'function': self.data_loader.metodo1, 'interval': 7200}
        ]

        self.scheduled_tasks = [
            {'function': self.data_loader.metodo2, 'hour': 7, 'minute': 0},
            {'function': self.data_loader.metodo3, 'hour': 10, 'minute': 40},
            {'function': self.data_loader.metodo4, 'hour': 12, 'minute': 0}
        ]

    def within_schedule(self):
        """
        Checks whether the current time is within the time.
        """
        now = datetime.now().time()
        return self.start_time <= now <= self.end_time

    async def periodic_task_runner(self, task, interval):
        """
        Generic runner for periodic tasks with custom intervals.
        """
        while self.within_schedule():
            await task()
            await asyncio.sleep(interval)

    async def start(self):
        """
        Starts the scheduler and tasks.
        """
        # Configuring periodic tasks with varying intervals
        for task_info in self.periodic_tasks:
            self.scheduler.add_job(
                self.periodic_task_runner,
                'interval',
                seconds=task_info['interval'],
                kwargs={'task': task_info['function'], 'interval': task_info['interval']},
                max_instances=5,
                start_date=datetime.now()
            )

        # Setting up one-off tasks
        for task in self.scheduled_tasks:
            self.scheduler.add_job(
                task['function'],
                'cron',
                hour=task['hour'],
                minute=task['minute'],
                max_instances=5,
                misfire_grace_time=120
            )

        self.scheduler.start()
        await asyncio.Event().wait()
