#!/bin/bash

http-server . --cors -c-1 -p 8000 &
poetry run python stream_parallel.py

wait -n

exit $?