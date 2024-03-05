# coding: utf8

import click
import requests
from tabulate import tabulate


@click.command()
@click.argument("url")
def run(url):
    url = f"{url}/api/instances"
    data = requests.get(url)
    j = data.json()

    print(tabulate(j, headers="keys"))
