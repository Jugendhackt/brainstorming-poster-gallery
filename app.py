#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import configparser
import dataclasses
import pathlib
import urllib.request

import commonmark
from flask import Flask, request, redirect, abort, render_template

app = Flask("Brainstorming")


@dataclasses.dataclass
class PosterData:
    title: str
    idea: str
    problem: str
    data: str
    missing: str
    people: str
    url: str


def process_markdown(text):
    parser = commonmark.Parser()
    ast = parser.parse(text)
    renderer = commonmark.HtmlRenderer()
    html = renderer.render(ast)
    parts = []

    for line in html.splitlines():
        if line.startswith("<h1>"):
            title = line[4:-5]
            parts.append([title])
        elif line.startswith("<h2>"):
            parts.append([])
        else:
            parts[-1].append(line)
    return parts


def download_pad(url):
    if not url.startswith("https://"):
        url = f"https://{url}/download"
    else:
        url = f"{url}/download"
    r = urllib.request.urlopen(url)
    if r.status != 200:
        abort(404)
    ct_header = r.getheader("content-type", "text/markdown; charset=utf-8")
    if ";" in ct_header:
        content_type, charset_def = ct_header.split(";", 1)
    else:
        content_type, charset_def = ct_header, "charset=utf-8"
    _, charset = charset_def.split("=", 1)
    return r.read().decode(charset)


def generate_posters(urls):
    posters = []
    for url in urls:
        content = download_pad(url)
        title, idea, problem, data, missing, people, *rest = process_markdown(content)
        posters.append(
            PosterData(
                title[0],
                "".join(idea),
                "".join(problem),
                "".join(data),
                "".join(missing),
                "".join(people),
                url.replace("https://", ""),
            )
        )
    return render_template("poster.html", posters=posters)


@app.route("/poster/<path:url>")
def poster(url):
    if ";" in url:
        urls = url.split(";")
    else:
        urls = [url]
    return generate_posters(urls)


def collect_urls(name):
    event_config_file = pathlib.Path("events.ini")
    if not event_config_file.exists():
        abort(404)
    event_config = configparser.ConfigParser()
    event_config.read(event_config_file)
    if not event_config.has_option("events", name):
        abort(404)
    url = event_config.get("events", name)
    content = download_pad(url)
    return [line[2:] for line in content.strip().splitlines() if line.startswith("- ")]


@app.route("/event/<name>")
def event(name):
    return generate_posters(collect_urls(name))


@app.route("/")
@app.route("/index")
@app.route("/poster/")
def index():
    if "url" in request.args:
        url = request.args.get("url").replace("https://", "")
        return redirect(f"poster/{url}", code=307)
    else:
        return render_template("index.html")
