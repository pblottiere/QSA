# coding: utf8

import os
import json
import time
import click
import requests
from pathlib import Path
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
@click.argument("id", required=False)
def stats(id):
    """
    Returns stats of a specific QGIS Server instance
    """

    ids = []
    if id:
        ids.append(id)
    else:
        url = f"{QSA_URL}/api/instances"
        data = requests.get(url)
        for s in data.json()["servers"]:
            ids.append(s["id"])

    headers = [
        "INSTANCE ID",
        "COUNT",
        "TIME    ",
        "SERVICE",
        "REQUEST",
        "PROJECT",
    ]

    try:
        while 1:
            table = []
            for i in ids:
                url = f"{QSA_URL}/api/instances/{i}/stats"
                task = requests.get(url).json()

                if "error" in task:
                    continue

                t = []
                t.append(i)
                t.append(task["count"])

                if "service" in task:
                    t.append(f"{task['duration']} ms")
                    t.append(task["service"])
                    t.append(task["request"])
                    p = Path(task["project"]).name
                    t.append(p)
                else:
                    t.append("")
                    t.append("")
                    t.append("")
                    t.append("")

                table.append(t)

            s = tabulate(table, headers=headers)
            os.system("cls" if os.name == "nt" else "clear")
            print(s)

            time.sleep(0.25)
    except:
        pass
