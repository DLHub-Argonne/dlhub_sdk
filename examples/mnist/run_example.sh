#! /bin/bash
set -e

python make_model.py
python describe_model.py
python make_pipeline.py