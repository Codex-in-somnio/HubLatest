#!/bin/bash

sphinx-build -b markdown . readme
cp readme/index.md ../README.md
