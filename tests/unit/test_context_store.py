"""
Pruebas unitarias del módulo CAG — Context Store
================================================
Basadas en: tests/features/cag_architecture.md
Escenarios: tests/features/cag.feature

ESTADO ESPERADO: Todas las pruebas FALLAN hasta que se implemente
ContextStore en backend/context_store.py.

Interfaz diseñada (aún no implementada):
    ContextStore.save(user_id, key, value) -> bool
    ContextStore.list_for_user(user_id)    -> list[dict]
    ContextStore.clear(user_id)            -> None  (para expiración/limpieza)
"""

import pytest
from unittest.mock import MagicMock, patch

from backend.context_store import ContextStore


# ===========================================================
# Fixtures
# ===========================================================

@pytest.fixture
def store():
    """Instancia limpia de ContextStore para cada test."""
    return ContextStore()


@pytest.fixture
def store_with_data(store):
    """ContextStore pre-cargado con datos de 'ana' y 'luis'."""
    store.save("ana", "preferred_style", "explicaciones con analogias")
    store.save("ana", "project", "usa arquitectura monolitica moderna")
    store.save("luis", "audience", "explicar como principiante")
    return store


# ===========================================================
# 1. Guardar contexto de un usuario
# ===========================================================

class TestSaveContext:
    """Escenario 1 de cag.feature — Guardar un par clave-valor."""

    def test_save_returns_true_on_success(self, store):
        """save() debe retornar True al guardar correctamente."""
        result = store.save("ana", "preferred_style", "explicaciones con analogias")
        assert result is True

    def test_save_accepts_string_value(self, store):
        """save() acepta valores de tipo string."""
        result = store.save("bob", "nivel", "avanzado")
        assert result is True

    def test_save_accepts_any_json_serializable_value(self, store):
        """save() acepta valores numéricos, booleanos y listas."""
        assert store.save("bob", "score", 42) is True
        assert store.save("bob", "active", True) is True
        assert store.save("bob", "tags", ["rag", "cag"]) is True

    def test_save_upsert_replaces_existing_key(self, store):
        """Escenario 6: guardar la misma key dos veces reemplaza el valor (upsert)."""
        store.save("maria", "nivel", "basico")
        store.save("maria", "nivel", "avanzado")

        items = store.list_for_user("maria")
        values = [item["value"] for item in items if item["key"] == "nivel"]

        assert values == ["avanzado"], "El valor anterior 'basico' debe haber sido reemplazado"

    def test_save_does_not_duplicate_keys(self, store):
        """Hacer upsert de la misma key no crea entradas duplicadas."""
        store.save("maria", "nivel", "basico")
        store.save("maria", "nivel", "avanzado")

        items = store.list_for_user("maria")
        keys = [item["key"] for item in items]

        assert keys.count("nivel") == 1, "No debe haber claves duplicadas tras upsert"


# ===========================================================
# 2. Recuperar contexto existente
# ===========================================================

class TestRetrieveExistingContext:
    """Escenario 2 de cag.feature — Recuperar contexto almacenado."""

    def test_list_for_user_returns_list(self, store_with_data):
        """list_for_user() debe retornar una lista."""
        result = store_with_data.list_for_user("ana")
        assert isinstance(result, list)

    def test_list_for_user_returns_all_saved_pairs(self, store_with_data):
        """list_for_user() retorna todos los pares guardados para ese usuario."""
        result = store_with_data.list_for_user("ana")
        assert len(result) == 2

    def test_list_for_user_items_have_key_and_value(self, store_with_data):
        """Cada elemento de la lista tiene exactamente 'key' y 'value'."""
        items = store_with_data.list_for_user("ana")
        for item in items:
            assert "key" in item, "Cada item debe tener campo 'key'"
            assert "value" in item, "Cada item debe tener campo 'value'"

    def test_list_for_user_returns_correct_values(self, store_with_data):
        """El contrato exacto del test_retrieves_context_for_user."""
        items = store_with_data.list_for_user("ana")
        assert {"key": "project", "value": "usa arquitectura monolitica moderna"} in items

    def test_context_isolated_between_users(self, store_with_data):
        """Escenario 4: el contexto de 'ana' no aparece en 'bob'."""
        items = store_with_data.list_for_user("bob")
        assert items == [], "Un usuario sin contexto debe recibir lista vacía"

    def test_luis_only_sees_his_own_context(self, store_with_data):
        """'luis' solo ve sus propias claves, no las de 'ana'."""
        items = store_with_data.list_for_user("luis")
        keys = [item["key"] for item in items]
        assert "audience" in keys
        assert "preferred_style" not in keys
        assert "project" not in keys


# ===========================================================
# 3. Recuperar contexto cuando no existe (caso vacío)
# ===========================================================

class TestRetrieveEmptyContext:
    """Escenario 4 de cag.feature — Usuario sin contexto previo."""

    def test_list_for_unknown_user_returns_empty_list(self, store):
        """list_for_user() con user_id desconocido retorna []."""
        result = store.list_for_user("usuario_que_nunca_existio")
        assert result == []

    def test_list_for_unknown_user_does_not_raise(self, store):
        """list_for_user() no lanza excepción para usuarios nuevos."""
        try:
            store.list_for_user("nuevo_usuario")
        except Exception as exc:
            pytest.fail(f"list_for_user() lanzó excepción inesperada: {exc}")

    def test_list_returns_empty_after_fresh_instantiation(self):
        """Un ContextStore recién creado no tiene datos de nadie."""
        fresh_store = ContextStore()
        assert fresh_store.list_for_user("cualquier_usuario") == []


# ===========================================================
# 4. Limpiar / expirar contexto
# ===========================================================

class TestClearContext:
    """
    Escenario de limpieza — clear(user_id) elimina todo el contexto del usuario.
    Este método AÚN NO existe en context_store.py, por lo que los tests
    fallarán con AttributeError hasta que se implemente.
    """

    def test_clear_removes_all_context_for_user(self, store_with_data):
        """clear(user_id) debe borrar todas las claves del usuario."""
        store_with_data.clear("ana")
        result = store_with_data.list_for_user("ana")
        assert result == [], "Tras clear(), el usuario no debe tener contexto"

    def test_clear_does_not_affect_other_users(self, store_with_data):
        """clear('ana') no debe borrar el contexto de 'luis'."""
        store_with_data.clear("ana")
        items = store_with_data.list_for_user("luis")
        assert len(items) > 0, "El contexto de otros usuarios debe permanecer intacto"

    def test_clear_on_unknown_user_does_not_raise(self, store):
        """clear() sobre un usuario sin contexto no debe lanzar excepción."""
        try:
            store.clear("usuario_sin_contexto")
        except Exception as exc:
            pytest.fail(f"clear() lanzó excepción inesperada: {exc}")

    def test_save_after_clear_works_normally(self, store_with_data):
        """Después de clear(), se puede volver a guardar contexto para ese usuario."""
        store_with_data.clear("ana")
        result = store_with_data.save("ana", "nueva_clave", "nuevo_valor")
        assert result is True
        items = store_with_data.list_for_user("ana")
        assert {"key": "nueva_clave", "value": "nuevo_valor"} in items


# ===========================================================
# 5. Integración con assistant.py (con mocks)
# ===========================================================

class TestAssistantUsesContextStore:
    """
    Verifica que answer_question() consulta el ContextStore.
    Usa mocks para aislar assistant.py de la implementación real.
    Alineado con: test_ask_uses_context_to_influence_later_response
    """

    def test_answer_question_calls_list_for_user(self):
        """answer_question() debe consultar el contexto del usuario."""
        mock_store = MagicMock()
        mock_store.list_for_user.return_value = [
            {"key": "audience", "value": "explicar como principiante"}
        ]

        with patch("backend.assistant.context_store", mock_store):
            from backend.assistant import answer_question
            answer_question("luis", "Que es CAG?")

        mock_store.list_for_user.assert_called_once_with("luis")

    def test_answer_reflects_audience_context(self):
        """La respuesta menciona el contexto de audiencia guardado."""
        mock_store = MagicMock()
        mock_store.list_for_user.return_value = [
            {"key": "audience", "value": "explicar como principiante"}
        ]

        with patch("backend.assistant.context_store", mock_store):
            from backend.assistant import answer_question
            result = answer_question("luis", "Que es CAG?")

        assert "principiante" in result["answer"].lower(), (
            "La respuesta debe mencionar el valor del contexto 'audience'"
        )

    def test_context_used_contains_applied_keys(self):
        """context_used debe listar las claves CAG que influyeron en la respuesta."""
        mock_store = MagicMock()
        mock_store.list_for_user.return_value = [
            {"key": "audience", "value": "explicar como principiante"}
        ]

        with patch("backend.assistant.context_store", mock_store):
            from backend.assistant import answer_question
            result = answer_question("luis", "Que es CAG?")

        assert "audience" in result["context_used"], (
            "context_used debe contener 'audience' cuando ese contexto se usó"
        )

    def test_no_context_returns_empty_context_used(self):
        """Sin contexto guardado, context_used debe ser []."""
        mock_store = MagicMock()
        mock_store.list_for_user.return_value = []

        with patch("backend.assistant.context_store", mock_store):
            from backend.assistant import answer_question
            result = answer_question("base-user", "Que es RAG?")

        assert result["context_used"] == [], (
            "Sin contexto CAG, context_used debe ser lista vacía"
        )
