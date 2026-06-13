# ============================================================
# Feature: CAG — Context-Augmented Generation
# Módulo 3 · Examen Final
# Alineado con: tests/validation/test_cag_contract.py
# ============================================================

Feature: Memoria contextual persistente por usuario (CAG)

  Como asistente inteligente
  Quiero recordar preferencias e historial de cada usuario
  Para que mis respuestas mejoren progresivamente con cada interacción

  Background:
    Given el backend está levantado en http://127.0.0.1:8000
    And la base de conocimiento contiene los documentos del curso


  # ----------------------------------------------------------
  # Escenario 1 — Guardar contexto
  # Cubre: test_saves_context_for_user
  # ----------------------------------------------------------
  Scenario: Guardar un par clave-valor de contexto para un usuario
    Given que el usuario "ana" no tiene contexto previo guardado
    When "ana" envía POST /api/context con key="preferred_style" y value="explicaciones con analogias"
    Then la respuesta HTTP es 201
    And el cuerpo de la respuesta contiene {"saved": true}


  # ----------------------------------------------------------
  # Escenario 2 — Recuperar contexto guardado
  # Cubre: test_retrieves_context_for_user
  # ----------------------------------------------------------
  Scenario: Recuperar el contexto almacenado de un usuario
    Given que "ana" tiene guardado en su contexto key="project" value="usa arquitectura monolitica moderna"
    When se hace GET /api/context?user_id=ana
    Then la respuesta HTTP es 200
    And el cuerpo incluye user_id="ana"
    And el arreglo "context" contiene {"key": "project", "value": "usa arquitectura monolitica moderna"}


  # ----------------------------------------------------------
  # Escenario 3 — Respuesta enriquecida con contexto
  # Cubre: test_ask_uses_context_to_influence_later_response
  # ----------------------------------------------------------
  Scenario: El asistente usa el contexto guardado para adaptar su respuesta
    Given que "luis" tiene guardado en su contexto key="audience" value="explicar como principiante"
    When "luis" envía POST /api/ask con question="Que es CAG?"
    Then la respuesta HTTP es 200
    And el campo "answer" contiene la palabra "principiante"
    And el campo "context_used" contiene la clave "audience"


  # ----------------------------------------------------------
  # Escenario 4 — Aislamiento entre usuarios
  # ----------------------------------------------------------
  Scenario: El contexto de un usuario no contamina el de otro
    Given que "ana" tiene guardado key="tema" value="RAG avanzado"
    And que "bob" no tiene contexto guardado
    When se hace GET /api/context?user_id=bob
    Then la respuesta HTTP es 200
    And el arreglo "context" está vacío


  # ----------------------------------------------------------
  # Escenario 5 — Validación de campos requeridos
  # ----------------------------------------------------------
  Scenario: Rechazar guardado de contexto si faltan campos obligatorios
    Given que el backend está operativo
    When se envía POST /api/context con body={"user_id": "ana"} sin key ni value
    Then la respuesta HTTP es 400
    And el cuerpo contiene un campo "error" con descripción del problema


  # ----------------------------------------------------------
  # Escenario 6 — Sobreescritura de contexto (upsert)
  # ----------------------------------------------------------
  Scenario: Una segunda escritura de la misma clave reemplaza el valor anterior
    Given que "maria" tiene guardado key="nivel" value="basico"
    When "maria" envía POST /api/context con key="nivel" y value="avanzado"
    Then la respuesta HTTP es 201
    And al hacer GET /api/context?user_id=maria
    And el arreglo "context" contiene {"key": "nivel", "value": "avanzado"}
    And el arreglo "context" NO contiene el value "basico" para la clave "nivel"
