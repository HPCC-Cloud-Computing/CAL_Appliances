"""
WSGI config for mcos project.

It exposes the WSGI callable as a module-level variable named ``application``.
"""
from mcos import wsgi

wsgi.setup_system_and_start_server()