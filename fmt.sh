#!/bin/sh

set -x

# Prettier
prettier \
  --write \
  src/**/*

# YAPF
yapf \
  --recursive -i \
  --style style.cfg \
  --exclude **/pb/*.py \
  src
