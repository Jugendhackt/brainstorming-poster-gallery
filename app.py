#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import dataclasses
import pathlib
import urllib.request

import commonmark
from flask import Flask, request, abort, render_template

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


def download_poster(url):
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


@app.route("/poster/<path:url>")
def poster(url):
    if ";" in url:
        urls = url.split(";")
    else:
        urls = [url]
    posters = []
    for url in urls:
        content = download_poster(url)
        title, idea, problem, data, missing, people, *rest = process_markdown(content)
        posters.append(
            PosterData(
                title[0],
                "".join(idea),
                "".join(problem),
                "".join(data),
                "".join(missing),
                "".join(people),
                url,
            )
        )
    return render_template("poster.html", posters=posters)
