import logging
import os
import time
from pathlib import Path
from threading import Thread
from typing import Optional

from flask import Flask, request

from ibeam.src.two_fa_handlers.two_fa_handler import TwoFaHandler

_LOGGER = logging.getLogger("ibeam." + Path(__file__).stem)

_HTTP_CALLBACK_DURATION = int(os.environ.get("IBEAM_HTTP_CALLBACK_DURATION", 300))
"""Duration for the http callback 2FA handler."""
_HTTP_CALLBACK_PORT = int(os.environ.get("IBEAM_HTTP_CALLBACK_PORT", 8088))
"""Specifies the port for the HTTP Callback TFA handler."""


class HttpCallbackTwoFaHandler(TwoFaHandler):
    def __init__(self, *args, **kwargs):
        self.security_code = None
        self.expiration_time = None
        self.duration = _HTTP_CALLBACK_DURATION
        super().__init__(*args, **kwargs)

        self.app = Flask(__name__)
        self.app.add_url_rule(
            "/security_code",
            "security_code",
            self.receive_security_code,
            methods=["PUT"],
        )
        Thread(
            target=self.run_app,
        ).start()
        _LOGGER.info(f"HttpCallbackTwoFaHandler started on {self.app.url_map}")

    def run_app(self):
        self.app.run(host='0.0.0.0', port=_HTTP_CALLBACK_PORT, use_reloader=False)

    def receive_security_code(self):
        self.security_code = request.form.get('code')
        self.expiration_time = time.time() + self.duration
        _LOGGER.info(f"Received security code: {self.security_code}")
        return "", 204

    def get_two_fa_code(self, driver) -> Optional[str]:
        if self.expiration_time is not None and time.time() < self.expiration_time:
            _LOGGER.info(f"Returning security code: {self.security_code}")
            return self.security_code
        else:
            _LOGGER.info("Security code expired")
            self.security_code = None
            self.expiration_time = None
            return None
