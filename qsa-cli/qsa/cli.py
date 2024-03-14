# coding: utf8

import os
import json
import click
import requests
from tabulate import tabulate

QSA_URL=os.environ.get("QSA_SERVER_URL", "http://localhost:5000/")


@click.group()
def cli():
    pass


@cli.command()
def instances():
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
def instance(id):
    url = f"{QSA_URL}/api/instances/{id}"
    data = requests.get(url)

    print(json.dumps(data.json(), indent=2))
