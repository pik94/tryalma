Please read the description of this directory:
- api: for all things related to endpoints
- database: for all things related to database
- services: for all things related to adding new services or updating existing ones
- settings: for all things related to settings and reading from environment variables
- tasks: for all things which can be run in backgroud using SchedulerContainer
- utils: for some helpful things
- container.py: the main app container
- scheduler.py: the main scheduler container. 
    When adding a new task, you MUST update SchedulerSettings to enable the task and define some schedule. As a hint, follow env settings for healthcheck. 
    Also, you MUST update main SchedulerService class to add a new background job. Use the same pattern like for adding healtcheck tasks.
- web_app: the module to define web app service.