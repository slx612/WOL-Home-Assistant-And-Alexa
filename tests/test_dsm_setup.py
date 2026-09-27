"""DSM setup authorization and package UI tests."""

import importlib
import subprocess
import unittest
from unittest.mock import patch


class DsmAuthenticationTests(unittest.TestCase):
    def auth(self, cookie="id=valid", remote_addr="192.168.100.10", server_addr="192.168.100.167"):
        module = importlib.import_module("dsm_package.payload.dsm_runtime.setup_auth")
        return module.authenticate_admin(cookie, remote_addr, server_addr)

    def test_missing_cookie_is_rejected_without_subprocess(self):
        with patch("subprocess.run") as run:
            self.assertFalse(self.auth(cookie=""))
        run.assert_not_called()

    def test_expired_session_is_rejected(self):
        with patch("subprocess.run", return_value=subprocess.CompletedProcess([], 0, "", "")) as run:
            self.assertFalse(self.auth())
        self.assertEqual(run.call_count, 1)

    def test_non_admin_is_rejected(self):
        calls = [
            subprocess.CompletedProcess([], 0, "sergio\n", ""),
            subprocess.CompletedProcess([], 0, "users\n", ""),
        ]
        with patch("subprocess.run", side_effect=calls):
            self.assertFalse(self.auth())

    def test_admin_is_accepted(self):
        calls = [
            subprocess.CompletedProcess([], 0, "sergio\n", ""),
            subprocess.CompletedProcess([], 0, "users administrators\n", ""),
        ]
        with patch("subprocess.run", side_effect=calls) as run:
            self.assertTrue(self.auth())
        self.assertEqual(run.call_args_list[0].args[0], ["/usr/syno/synoman/webman/modules/authenticate.cgi"])
        self.assertEqual(run.call_args_list[0].kwargs["env"]["HTTP_COOKIE"], "id=valid")
        self.assertEqual(run.call_args_list[1].args[0], ["id", "-nG", "sergio"])

    def test_subprocess_failure_fails_closed(self):
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("authenticate.cgi", 3)):
            self.assertFalse(self.auth())


if __name__ == "__main__":
    unittest.main()
