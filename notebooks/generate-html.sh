#!/usr/bin/bash
# install pandoc with:
# `brew install pandoc`, or `mamba install pandoc` (see https://pandoc.org/installing.html)
# 

# download styles
# these should be included with the html pages.
# Note that the html pages now used the main heasarc theme
if [ ! -d styles/ ]; then
    echo downloading styles
    mkdir styles
    cd styles
    wget -q https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/default.min.css
    wget -q https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js
    wget -q https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/python.min.js
    cd ..
fi

pandoc ../README.md -o index.html --template=template.html --metadata title="HEASoftpy: The python interface to HEASoft"
pandoc getting-started.md -o getting-started.html --template=template.html --metadata title="Getting Started with Heasoftpy"
pandoc nicer-example.md -o nicer-example.html --template=template.html --metadata title="Heasoftpy Tutorial: NICER Data Example"
pandoc nustar-example.md -o nustar-example.html --template=template.html --metadata title="Heasoftpy Tutorial: NuSTAR Data Example"
