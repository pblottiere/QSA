# coding: utf8

import os
import json
import time
import click
import requests
from tabulate import tabulate

QSA_URL = os.environ.get("QSA_SERVER_URL", "http://localhost:5000/")


@click.group()
def cli():
    pass


@cli.command()
def ps():
    """
    List QGIS Server instances
    """

    url = f"{QSA_URL}/api/instances"
    data = requests.get(url)

    headers = ["INSTANCE ID", "IP", "STATUS"]
    table = []

    for s in data.json()["servers"]:
        t = []
        t.append(s["id"])
        t.append(s["ip"])
        t.append(f"Binded {s['binded']} seconds ago")

        table.append(t)

    print(tabulate(table, headers=headers))


@cli.command()
@click.argument("id")
def inspect(id):
    """
    Returns metadata about a specific QGIS Server instance
    """

    url = f"{QSA_URL}/api/instances/{id}"
    data = requests.get(url)

    print(json.dumps(data.json(), indent=2))


@cli.command()
@click.argument("id")
def logs(id):
    """
    Returns logs of a specific QGIS Server instance
    """

    url = f"{QSA_URL}/api/instances/{id}/logs"
    data = requests.get(url)

    print(data.json()["logs"])


@cli.command()
@click.argument("id")
def stats(id):
    """
    Returns stats of a specific QGIS Server instance
    """

    while 1:
        url = f"{QSA_URL}/api/instances/{id}/stats"
        data = requests.get(url)

        print(data.json())
        time.sleep(0.25)
