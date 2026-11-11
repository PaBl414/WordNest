import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import desktop
from wordnest import paths


class DesktopTests(unittest.TestCase):
    def test_bundled_database_is_outside_extracted_resources(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {'LOCALAPPDATA': directory}, clear=True), patch.object(sys, 'frozen', True, create=True):
                self.assertEqual(paths.data_directory(), Path(directory) / 'WordNest' / 'data')
                self.assertFalse(paths.data_directory().is_relative_to(paths.resource_root()))

    def test_source_retains_existing_database_location(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(sys, 'frozen', False, create=True):
            self.assertEqual(paths.data_directory(), paths.resource_root() / 'data')

    def test_explicit_data_directory_is_respected(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {'WORDNEST_DATA': directory}), patch.object(sys, 'frozen', True, create=True):
                self.assertEqual(paths.data_directory(), Path(directory).resolve())

    def test_desktop_is_local_and_keeps_user_files(self):
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / 'existing-progress.txt'
            marker.write_text('keep', encoding='utf-8')
            with patch.dict(os.environ, {'WORDNEST_DATA': directory, 'WORDNEST_LAN_IP': '192.168.1.5', 'WORDNEST_LAN_CIDR': '192.168.1.0/24', 'WORDNEST_DICTIONARY': '1'}):
                self.assertEqual(desktop.configure_environment(), Path(directory).resolve())
                self.assertNotIn('WORDNEST_LAN_IP', os.environ)
                self.assertNotIn('WORDNEST_LAN_CIDR', os.environ)
                self.assertEqual(os.environ['WORDNEST_DICTIONARY'], '0')
                self.assertEqual(marker.read_text(encoding='utf-8'), 'keep')

    def test_failed_server_does_not_open_browser(self):
        from types import SimpleNamespace
        with patch.object(desktop, 'notify'), patch.object(desktop.webbrowser, 'open') as browser:
            with self.assertRaises(RuntimeError):
                desktop.wait_for_server('http://127.0.0.1:1/', SimpleNamespace(started=False), SimpleNamespace(is_alive=lambda: False))
            browser.assert_not_called()
