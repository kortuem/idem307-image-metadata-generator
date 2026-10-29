"""Offline regressions: no Google calls or real Redis connection."""
import importlib
import io
import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from utils.session_manager import SessionManager

SID = 'a' * 32

class SessionSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp.name)
        self.manager = SessionManager(file_folder=self.folder / 'sessions')

    def tearDown(self):
        self.temp.cleanup()

    def test_round_trip_and_delete(self):
        self.assertTrue(self.manager.save_session(SID, {'caption': 'example'}))
        self.assertEqual(self.manager.load_session(SID), {'caption': 'example'})
        self.assertTrue(self.manager.session_exists(SID))
        self.assertTrue(self.manager.delete_session(SID))
        self.assertFalse(self.manager.session_exists(SID))

    def test_traversal_and_non_string_ids_never_touch_storage(self):
        victim = self.folder / 'victim.json'
        victim.write_text('{"keep": true}')
        for invalid in ('../victim', str(victim)[:-5], '', None, [], {}, 5, 'a'*31):
            with self.subTest(invalid=invalid):
                self.assertFalse(self.manager.save_session(invalid, {}))
                self.assertIsNone(self.manager.load_session(invalid))
                self.assertFalse(self.manager.session_exists(invalid))
                self.assertFalse(self.manager.delete_session(invalid))
                self.assertEqual(json.loads(victim.read_text()), {'keep': True})

    def test_redis_delete_and_failure(self):
        self.manager.storage_type = 'redis'
        self.manager.redis_client = MagicMock()
        self.assertTrue(self.manager.delete_session(SID))
        self.manager.redis_client.delete.assert_called_once_with('session:' + SID)
        self.manager.redis_client.delete.side_effect = RuntimeError('unavailable')
        self.assertFalse(self.manager.delete_session(SID))

    def test_redis_credentials_absent_from_connection_logs(self):
        fake = MagicMock()
        with patch.dict(sys.modules, {'redis': fake}):
            import utils.session_manager as module
            with patch.object(module, 'redis', fake, create=True), patch.object(module, 'REDIS_AVAILABLE', True):
                with self.assertLogs(module.logger, level='INFO') as logs:
                    SessionManager(redis_url='redis://user:credential-sentinel@localhost')
                self.assertNotIn('credential-sentinel', str(logs.output))

class RouteSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        stub = types.ModuleType('utils.caption_generator')
        stub.GeminiCaptionGenerator = MagicMock()
        with patch.dict(os.environ, {'SESSION_FOLDER': cls.temp.name + '/sessions',
                                     'UPLOAD_FOLDER': cls.temp.name + '/uploads'}, clear=True), \
             patch.dict(sys.modules, {'utils.caption_generator': stub}), \
             patch('dotenv.load_dotenv'):
            cls.module = importlib.import_module('app')
        cls.client = cls.module.app.test_client()

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_all_session_post_routes_reject_bad_id_before_work(self):
        for route in ('delete-session', 'export', 'generate', 'generate-single', 'caption'):
            for value in ('../victim', None, [], 123):
                response = self.client.open('/api/' + route, method='PUT' if route == 'caption' else 'POST', json={'session_id': value})
                self.assertEqual(response.status_code, 400, (route, value))
        self.assertEqual(self.client.post('/api/export', json=[]).status_code, 400)
        self.assertEqual(self.client.post('/api/export', json={}).status_code, 400)

    def test_delete_uses_configured_backend_and_preserves_tracker_on_failure(self):
        manager = MagicMock()
        manager.session_exists.return_value = True
        self.module.active_sessions[SID] = 0
        with patch.object(self.module, 'session_manager', manager):
            manager.delete_session.return_value = False
            self.assertEqual(self.client.post('/api/delete-session', json={'session_id': SID}).status_code, 500)
            self.assertIn(SID, self.module.active_sessions)
            manager.delete_session.return_value = True
            self.assertEqual(self.client.post('/api/delete-session', json={'session_id': SID}).status_code, 200)
            self.assertNotIn(SID, self.module.active_sessions)
            manager.delete_session.assert_called_with(SID)

    def test_export_deletes_from_redis_through_manager(self):
        manager = MagicMock()
        manager.load_session.return_value = {'images': {}, 'semantic_context': 'example'}
        manager.delete_session.return_value = True
        with patch.object(self.module, 'session_manager', manager), \
             patch.object(self.module, 'create_training_zip_in_memory', return_value=(True, io.BytesIO(b'zip'), 'Exported')):
            response = self.client.post('/api/export', json={'session_id': SID})
            self.assertEqual(response.status_code, 200)
            manager.delete_session.assert_called_once_with(SID)

class CaptionErrorTests(unittest.TestCase):
    def test_provider_errors_do_not_expose_credentials(self):
        import importlib.util
        sdk = MagicMock()
        google = types.ModuleType('google')
        google.generativeai = sdk
        spec = importlib.util.spec_from_file_location('caption_under_test', Path(__file__).parents[1] / 'utils/caption_generator.py')
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {'google': google, 'google.generativeai': sdk}):
            spec.loader.exec_module(module)
        generator = module.GeminiCaptionGenerator(api_key='credential-sentinel')
        generator.model.generate_content.side_effect = RuntimeError('429 credential-sentinel')
        with patch.object(module.Image, 'open', return_value=MagicMock(format='JPEG')), \
             patch.object(module.time, 'sleep'), \
             self.assertLogs(module.logger, level='INFO') as logs:
            result = generator.generate_caption('example.jpg', 'example')
        self.assertFalse(result[0])
        self.assertNotIn('credential-sentinel', str(result))
        self.assertNotIn('credential-sentinel', str(logs.output))

if __name__ == '__main__':
    unittest.main()
