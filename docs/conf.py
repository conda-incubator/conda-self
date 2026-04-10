"""Sphinx configuration for conda-self documentation."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(".."))

project = html_title = "conda-self"
copyright = "2025, conda community"
author = "conda-self contributors"

extensions = [
    "myst_parser",
    "sphinx_copybutton",
    "sphinx_design",
]

myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "fieldlist",
    "tasklist",
]

html_theme = "conda_sphinx_theme"

html_theme_options = {
    "icon_links": [
        {
            "name": "GitHub",
            "url": "https://github.com/conda-incubator/conda-self",
            "icon": "fa-brands fa-square-github",
            "type": "fontawesome",
        },
    ],
}

html_context = {
    "github_user": "conda-incubator",
    "github_repo": "conda-self",
    "github_version": "main",
    "doc_path": "docs",
}

html_static_path = ["_static"]
html_extra_path = ["../demos"]
html_css_files = ["css/custom.css"]

html_baseurl = "https://conda-incubator.github.io/conda-self/"

exclude_patterns = ["_build"]
