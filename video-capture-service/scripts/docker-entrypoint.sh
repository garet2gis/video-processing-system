#!/bin/bash

poetry run python capture_parallel.py

wait -n

exit $?