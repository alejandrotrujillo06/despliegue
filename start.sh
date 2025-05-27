#!/bin/bash
gunicorn app:app.server --bind 0.0.0.0:10000