#!/bin/bash
venv_dir=$1
shift
source "$venv_dir/bin/activate"

# Set the DJANGO_SETTINGS_MODULE environment variable
export DJANGO_SETTINGS_MODULE="cloudlines.settings"

"$@"

