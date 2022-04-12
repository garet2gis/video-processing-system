#!/bin/bash

http-server . --cors -c-1 -p 8000 &
poetry run python capture.py

wait -n

exit $?