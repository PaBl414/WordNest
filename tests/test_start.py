"""Startup argument validation must not open a server or create a database."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent


class StartupTests(unittest.TestCase):
    def run_start(self, *args):
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory) / 'data'
            result = subprocess.run(
                [sys.executable, str(ROOT / 'start.py'), *args],
                cwd=directory, env={**os.environ, 'WORDNEST_DATA': str(data)},
                capture_output=True, timeout=15,
            )
            self.assertFalse(data.exists())
            return result

    def test_check_from_another_directory(self):
        result = self.run_start('--check')
        built = (ROOT / 'frontend' / 'dist' / 'index.html').is_file() and (ROOT / 'frontend' / 'dist' / 'assets').is_dir()
        import importlib.util
        ready = built and all(importlib.util.find_spec(name) for name in ('fastapi', 'uvicorn', 'httpx'))
        self.assertEqual(result.returncode, 0 if ready else 1)
        self.assertIn(b'WordNest' if ready else b'Instalacja:', result.stdout)
        self.assertNotIn(b'Traceback', result.stderr)

    def test_invalid_ports(self):
        for port in ('0', '-1', '65536'):
            with self.subTest(port=port):
                result = self.run_start('--port', port)
                self.assertEqual(result.returncode, 2)
                self.assertIn(b'Port musi', result.stderr)

    def test_lan_parameters_are_paired(self):
        self.assertEqual(self.run_start('--lan-ip', '192.168.1.10').returncode, 2)

    def test_malformed_lan_has_no_traceback(self):
        for address, network in [('bad', '192.168.1.0/24'), ('192.168.1.10', 'bad')]:
            result = self.run_start('--lan-ip', address, '--lan-cidr', network)
            self.assertEqual(result.returncode, 2)
            self.assertNotIn(b'Traceback', result.stderr)

    def test_non_lan_and_reserved_addresses_are_rejected(self):
        for address, network in [('127.0.0.1','127.0.0.0/24'), ('169.254.1.5','169.254.1.0/24'), ('192.168.1.0','192.168.1.0/24'), ('192.168.1.255','192.168.1.0/24'), ('8.8.8.8','8.8.8.0/24')]:
            with self.subTest(address=address):
                self.assertEqual(self.run_start('--lan-ip', address, '--lan-cidr', network).returncode, 2)
