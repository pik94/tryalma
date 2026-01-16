import logging

import structlog
from structlog.dev import RichTracebackFormatter
from structlog.typing import EventDict

from service.settings import AppSettings


def _drop_color_message_key(_, __, event_dict: EventDict) -> EventDict:
    event_dict.pop('color_message', None)
    return event_dict


def prepare_logger(app_settings: AppSettings):
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.CallsiteParameterAdder(
            parameters={
                structlog.processors.CallsiteParameter.FUNC_NAME,
            }
        ),
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.stdlib.ExtraAdder(),
        _drop_color_message_key,
        structlog.processors.TimeStamper(fmt='iso'),
        structlog.processors.StackInfoRenderer(),
    ]
    current_renderer: structlog.types.Processor
    if app_settings.console_formatter:
        exception_formatter = RichTracebackFormatter(show_locals=False)
        current_renderer = structlog.dev.ConsoleRenderer(colors=True, exception_formatter=exception_formatter)
    else:
        current_renderer = structlog.processors.JSONRenderer()
        shared_processors.append(structlog.processors.format_exc_info)

    structlog.configure(
        processors=shared_processors + [structlog.stdlib.ProcessorFormatter.wrap_for_formatter],  # type: ignore
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,  # type: ignore
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            current_renderer,
        ],
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.DEBUG if app_settings.debug else logging.INFO)

    structlog.get_logger(__name__).info('Logging initialized')
