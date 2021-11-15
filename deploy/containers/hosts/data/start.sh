#!/bin/bash

echo "Starting apache service..."
apachectl start

echo "Starting jenkins service..."
rcjenkins start
