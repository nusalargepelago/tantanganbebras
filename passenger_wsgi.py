"""WSGI entry point for cPanel / Phusion Passenger.

Passenger imports `application` from this file instead of running
`app.run`; there is no port to bind and no waitress process.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.create_app import create_app

application = create_app()
