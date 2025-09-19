#!/bin/bash

export PYTHONPATH='../orange'
nice -n 19 python run_ga_style.py >> STYLE_GA_LOG 2>&1 &

exit 0
