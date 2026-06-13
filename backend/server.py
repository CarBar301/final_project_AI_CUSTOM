import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from backend.assistant import answer_question
from backend.context_store import ContextStore


context_store = ContextStore()


class ExamRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/health":
            self._send_json(200, {"status": "ok"})
            return

        if parsed.path == "/api/context":
            query = parse_qs(parsed.query)
            user_id = query.get("user_id", [""])[0]
            if not user_id:
                self._send_json(400, {"error": "user_id is required"})
                return

            try:
                items = context_store.list_for_user(user_id)
            except NotImplementedError as error:
                self._send_json(501, {"error": str(error)})
                return

            self._send_json(200, {"user_id": user_id, "context": items})
            return

        self._send_json(404, {"error": "not found"})

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path == "/api/ask":
            payload = self._read_json()
            user_id = payload.get("user_id")
            question = payload.get("question")

            if not user_id or not question:
                self._send_json(400, {"error": "user_id and question are required"})
                return

            # 1. Recuperar contexto previo del usuario desde ContextStore
            contexts = context_store.list_for_user(user_id)
            context_keys = [c["key"] for c in contexts]

            # 2. Generar respuesta base usando RAG (e incluir contexto en la consulta/respuesta)
            response = answer_question(user_id, question)

            # 3. Incluir el contexto para adaptar/enriquecer la respuesta final
            if contexts:
                instructions = " y ".join(str(c["value"]) for c in contexts)
                response["answer"] = f"Adaptado a ({instructions}): {response['answer']}"
                response["context_used"] = context_keys

            # 4. Guardar la nueva interacción en ContextStore después de responder
            context_store.save(user_id, "last_question", question)
            context_store.save(user_id, "last_answer", response["answer"])

            self._send_json(200, response)
            return

        if parsed.path == "/api/context":
            payload = self._read_json()
            user_id = payload.get("user_id")
            key = payload.get("key")
            value = payload.get("value")

            if not user_id or not key or value is None:
                self._send_json(400, {"error": "user_id, key and value are required"})
                return

            try:
                saved = context_store.save(user_id, key, value)
            except NotImplementedError as error:
                self._send_json(501, {"error": str(error)})
                return

            self._send_json(201, {"saved": saved})
            return

        self._send_json(404, {"error": "not found"})

    def _read_json(self):
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw_body = self.rfile.read(length).decode("utf-8")
        return json.loads(raw_body)

    def _send_json(self, status_code, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self._send_json(200, {"status": "ok"})

    def log_message(self, format, *args):
        return


def create_server(host="127.0.0.1", port=8000):
    return ThreadingHTTPServer((host, port), ExamRequestHandler)


if __name__ == "__main__":
    server = create_server()
    print("Backend running at http://127.0.0.1:8000")
    server.serve_forever()
