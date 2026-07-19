# East Bay Automation Railway Services

## Scheduler

Command:

python -u -m automation_engine.scheduler

Purpose:
- creates jobs
- monitors schedules
- queues automation work


## Worker

Command:

python -u -m automation_engine.worker

Purpose:
- consumes jobs
- executes tasks
- updates job status


## Agent

Command:

python -u -m automation_engine.agent

Purpose:
- monitors system
- analyzes failures
- stores memory


All services require:

DATABASE_URL
