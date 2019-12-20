#!/bin/bash

sphinx-build -E -b markdown . readme
cp readme/index.md ../README.md
