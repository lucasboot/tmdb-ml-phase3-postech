"""Make the ``web`` directory a Python package.

This allows modules inside ``web/app`` to be imported using the
``web.app`` namespace, which is required for the Vercel entrypoint to
load the Flask application.
"""

