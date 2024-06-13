# coding: utf8

from enum import Enum
from flask import current_app


def config():
    return current_app.config["CONFIG"]


def logger():
    return current_app.logger


class StorageBackend(Enum):
    FILESYSTEM = 0
    POSTGRESQL = 1

    @staticmethod
    def type() -> "StorageBackend":
        if config().qgisserver_projects_psql_service:
            return StorageBackend.POSTGRESQL
        return StorageBackend.FILESYSTEM


def qgisserver_base_url(project: str, psql_schema: str) -> str:
    url = f"{config().qgisserver_url}"
    if StorageBackend.type() == StorageBackend.FILESYSTEM:
        url = f"{url}/{project}?"
    elif StorageBackend.type() == StorageBackend.POSTGRESQL:
        service = config().qgisserver_projects_psql_service
        url = f"{url}?MAP=postgresql:?service={service}%26schema={psql_schema}%26project={project}&"
    return url
