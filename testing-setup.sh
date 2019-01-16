#!/usr/bin/env bash

if [ ! -e "./virtualenv/bin/pip" ]
then
    python3 -m venv virtualenv
fi

./virtualenv/bin/pip install -r requirements.txt
