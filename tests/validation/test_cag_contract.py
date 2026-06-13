import json
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from backend.server import create_server


class CagContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = create_server(port=0)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def url(self, path):
        return f"http://127.0.0.1:{self.port}{path}"

    def get_json(self, path):
        try:
            with urlopen(self.url(path), timeout=5) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            body = json.loads(error.read().decode("utf-8"))
            error.close()
            return error.code, body

    def post_json(self, path, payload):
        request = Request(
            self.url(path),
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=5) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            body = json.loads(error.read().decode("utf-8"))
            error.close()
            return error.code, body

    def test_saves_context_for_user(self):
        status, body = self.post_json(
            "/api/context",
            {"user_id": "ana", "key": "preferred_style", "value": "explicaciones con analogias"},
        )

        self.assertEqual(status, 201)
        self.assertTrue(body["saved"])

    def test_retrieves_context_for_user(self):
        self.post_json(
            "/api/context",
            {"user_id": "ana", "key": "project", "value": "usa arquitectura monolitica moderna"},
        )

        status, body = self.get_json("/api/context?user_id=ana")

        self.assertEqual(status, 200)
        self.assertEqual(body["user_id"], "ana")
        self.assertIn({"key": "project", "value": "usa arquitectura monolitica moderna"}, body["context"])

    def test_ask_uses_context_to_influence_later_response(self):
        self.post_json(
            "/api/context",
            {"user_id": "luis", "key": "audience", "value": "explicar como principiante"},
        )

        status, body = self.post_json(
            "/api/ask",
            {"user_id": "luis", "question": "Que es CAG?"},
        )

        self.assertEqual(status, 200)
        self.assertIn("principiante", body["answer"].lower())
        self.assertIn("audience", body["context_used"])

    def delete_json(self, path):
        request = Request(
            self.url(path),
            method="DELETE",
        )
        try:
            with urlopen(request, timeout=5) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            body = json.loads(error.read().decode("utf-8"))
            error.close()
            return error.code, body

    def test_get_context_by_path_param(self):
        self.post_json(
            "/api/context",
            {"user_id": "carlos", "key": "skill", "value": "python master"},
        )

        status, body = self.get_json("/context/carlos")
        self.assertEqual(status, 200)
        self.assertEqual(body["user_id"], "carlos")
        self.assertIn({"key": "skill", "value": "python master"}, body["context"])

    def test_delete_context_by_path_param(self):
        self.post_json(
            "/api/context",
            {"user_id": "carlos", "key": "skill", "value": "python master"},
        )

        # Confirm context exists
        status, body = self.get_json("/context/carlos")
        self.assertEqual(status, 200)
        self.assertEqual(len(body["context"]), 1)

        # Clear it
        del_status, del_body = self.delete_json("/context/carlos")
        self.assertEqual(del_status, 200)
        self.assertEqual(del_body["status"], "cleared")

        # Confirm it's empty
        status_after, body_after = self.get_json("/context/carlos")
        self.assertEqual(status_after, 200)
        self.assertEqual(body_after["context"], [])


if __name__ == "__main__":
    unittest.main()
