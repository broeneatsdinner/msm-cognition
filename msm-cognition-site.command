#!/usr/bin/env bash
# --------------------------------------
# --    msm-cognition-site.command    --
# --------------------------------------
# description: Double-click in Finder to browse the repository for two hours
#
# Finder opens this in Terminal and runs bin/site, which serves the repo on
# 127.0.0.1 and opens it in the browser. The Terminal window shows each saved
# click and stays open until the site stops: after two hours, or when you
# press Ctrl-C or close the window.
cd "$(dirname "$0")" && exec bin/site "$@"
