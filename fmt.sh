#!/bin/sh

set -ex

# Prettier
prettier \
  --write \
  src/**/*.html \
  src/**/*.css

# YAPF
yapf \
  --recursive -i \
  --style style.cfg \
  --exclude **/pb/*.py \
  src
