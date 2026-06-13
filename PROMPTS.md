## 🛠️ Fase 1: Diagnóstico y Diseño de Arquitectura

### 📋 Prompt 1 & 2: Análisis del Monolito e Identificación de Requisitos para CAG
*   **El objetivo era**: Comprender la estructura de archivos existente del backend (RAG base, servidor nativo) y del frontend para diagnosticar en qué partes se perdía el contexto de usuario entre llamadas y qué componentes eran necesarios agregar para CAG.
*   **El prompt que usé fue**:
    > "Analiza esta estructura de proyecto monolítico con RAG. Necesito entender:
    > 1. Cómo fluye una petición del usuario hasta la respuesta.
    > 2. Dónde se hace la recuperación documental (RAG).
    > 3. Qué archivos son el núcleo del backend.
    > 4. Qué dependencias maneja el frontend.
    > Dado este código del backend, identifica específicamente qué falta para implementar CAG: ¿Dónde se pierde el contexto entre llamadas? ¿Qué estructura de datos necesito para persistir contexto? ¿Qué endpoints debo agregar?"
*   **La respuesta fue**: La IA identificó que la pérdida de contexto ocurre debido a que la función `answer_question` en `assistant.py` es totalmente sin estado. Recomendó la creación de un servicio `ContextStore` que persista pares clave/valor con timestamps por usuario y sugirió añadir endpoints para guardar y consultar dicho contexto en `server.py`.
*   **Mi decisión humana fue**: Aprobar la persistencia efímera en memoria RAM para evitar dependencias complejas como bases de datos externas (Redis o SQLite), manteniendo el diseño lo más simple y portable posible para el examen.
*   **Los cambios que hice fueron**: Ninguno en código, se crearon los mapas mentales y el documento de planificación.
*   **La verificación que apliqué fue**: Revisión visual manual de los diagramas y código base en el repositorio.

---

### 📋 Prompt 3: Diseño Técnico de la Arquitectura CAG
*   **El objetivo era**: Diseñar formalmente los componentes de software del módulo CAG, sus responsabilidades y su relación con el flujo RAG ya existente.
*   **El prompt que usé fue**:
    > "Diseña la arquitectura del módulo CAG para este proyecto. Necesito:
    > 1. Diagrama de componentes en texto (no código)
    > 2. Qué responsabilidad tiene cada componente
    > 3. Cómo interactúa CAG con el RAG existente
    > 4. Dónde persisto el contexto (memoria en RAM, Redis, SQLite — recomienda el más simple para este alcance)"
*   **La respuesta fue**: Un diseño modular donde `ContextStore` actúa de almacén persistente en memoria RAM protegido por bloqueos de hilo (`threading.Lock`). El asistente RAG usaría este almacén antes de la generación para adaptar las respuestas.
*   **Mi decisión humana fue**: Escribir este diseño en un documento dedicado de arquitectura en markdown dentro de la carpeta de features para consulta futura de todo el equipo de desarrollo.
*   **Los cambios que hice fueron**:
    *   Creación del archivo [**`tests/features/cag_architecture.md`**].
*   **La verificación que apliqué fue**: Inspección del documento de arquitectura.

---

## 🥒 Fase 2: Definición de Escenarios de Comportamiento (BDD)

### 📋 Prompt 4: Redacción de Escenarios Gherkin
*   **El objetivo era**: Escribir escenarios BDD estructurados (Given/When/Then) en formato Gherkin que definan el comportamiento esperado del módulo CAG (guardar contexto, recuperar histórico de turnos, aislamiento por usuario y expiración).
*   **El prompt que usé fue**:
    > "Necesito escribir escenarios BDD en formato Gherkin para un módulo CAG (Context-Augmented Generation) que:
    > - Guarda contexto de conversaciones anteriores del usuario.
    > - Recupera ese contexto en llamadas posteriores.
    > - Usa ese contexto para enriquecer las respuestas del LLM.
    > - Expira o limpia contexto viejo.
    > Escribe entre 4 y 6 escenarios Feature/Scenario con Given/When/Then. El sistema usa Python en el backend."
*   **La respuesta fue**: Proporcionó 4 escenarios BDD detallados en español enfocados en las funcionalidades críticas de almacenamiento, aislamiento, recuperación cronológica y caducidad temporal.
*   **Mi decisión humana fue**: Adoptar los escenarios propuestos y almacenarlos en un archivo de feature en la carpeta de tests para guiar el desarrollo de pruebas posteriores.
*   **Los cambios que hice fueron**:
    *   Creación del archivo [**`tests/features/cag.feature`**].
*   **La verificación que apliqué fue**: Revisión de sintaxis Gherkin válida.

---

## 🧪 Fase 3: Estrategia de Pruebas Primero (TDD)

### 📋 Prompt 5: Pruebas Unitarias para ContextStore (Fase Roja)
*   **El objetivo era**: Escribir pruebas unitarias exhaustivas usando `pytest` para la interfaz de `ContextStore` antes de que existiera cualquier línea de código del componente (siguiendo metodología TDD).
*   **El prompt que usé fue**:
    > "Basado en el diseño de módulo CAG que está en cag_architecture.md dentro de features, escribe pruebas unitarias en pytest para:
    > 1. Guardar contexto de un usuario.
    > 2. Recuperar contexto existente.
    > 3. Recuperar contexto cuando no existe (caso vacío).
    > 4. Limpiar contexto expirado.
    > Las pruebas deben fallar ahora porque aún no existe la implementación. Usa mocks donde sea necesario. No implementes el módulo todavía."
*   **La respuesta fue**: Creación de una suite con clases de prueba para cada uno de los cuatro escenarios, empleando mocks (`unittest.mock`) para modelar llamadas concurrentes e inyección del contexto en el asistente.
*   **Mi decisión humana fue**: Aceptar las pruebas e integrarlas en el árbol del proyecto bajo `tests/unit/`.
*   **Los cambios que hice fueron**:
    *   Creación del archivo [**`tests/unit/test_context_store.py`**]
*   **La verificación que apliqué fue**: Ejecutar las pruebas unitarias y comprobar que fallaban en su totalidad con errores de importación/implementación (Fase Roja de TDD).

---

## 💻 Fase 4: Implementación del Almacén y la Integración RAG+CAG

### 📋 Prompt 6: Creación de la clase `ContextStore` (Fase Verde)
*   **El objetivo era**: Desarrollar la lógica de Python para `ContextStore` que superase con éxito las pruebas unitarias definidas anteriormente.
*   **El prompt que usé fue**:
    > "Implementa la clase ContextStore en Python que:
    > - Guarda contexto por user_id como lista de turnos {role, content, timestamp}
    > - Recupera los últimos N turnos de un usuario
    > - Limpia entradas más viejas que X minutos
    > - Usa diccionario en memoria
    > Implementa solo esta clase, sin tocar el resto del proyecto."
*   **La respuesta fue**: Escribió la implementación de la clase utilizando un diccionario estructurado por `user_id` e hilos sincronizados mediante exclusión mutua (`threading.Lock`), manejando marcas de tiempo `datetime.now()` internas para la expiración.
*   **Mi decisión humana fue**: Integrar el código en `backend/context_store.py` y mantener la API simple basada en métodos públicos `save`, `list_for_user`, `clear` y `clean_expired`.
*   **Los cambios que hice fueron**:
    *   Escritura del archivo [**`backend/context_store.py`**].
*   **La verificación que apliqué fue**: Ejecutar un script de prueba de humo local manual en Python verificando que la manipulación del diccionario fuera exitosa.

---

### 📋 Prompt 7: Integración de CAG en el Endpoint Principal de Preguntas
*   **El objetivo era**: Conectar el almacén de contexto dinámico `ContextStore` con el flujo del endpoint principal de preguntas (`/api/ask`) del backend para adaptar las respuestas usando la información recuperada y guardar cada nueva interacción.
*   **El prompt que usé fue**:
    > "Tengo este endpoint de backend que está en la carpeta backend/server.py que usa RAG: Necesito modificarlo para que:
    > 1. Reciba un user_id
    > 2. Recupere el contexto previo del usuario desde ContextStore
    > 3. Incluya ese contexto en el prompt enviado al LLM
    > 4. Guarde la nueva interacción en ContextStore después de responder
    > Modifica solo este endpoint. No cambies otros archivos. Muéstrame el before y after del código."
*   **La respuesta fue**: Modificación en el bloque `do_POST` de `/api/ask` dentro de `server.py` para leer el historial usando `list_for_user`, concatenar las instrucciones de contexto y agregarlas al texto de la respuesta devuelta simulando la adaptación contextual, registrando finalmente la pregunta y la respuesta como claves en el almacén.
*   **Mi decisión humana fue**: Aprobar la implementación para cumplir con el examen, post-procesando el retorno del asistente simulado.
*   **Los cambios que hice fueron**:
    *   Modificación de [**`backend/server.py`**] (endpoint `/api/ask`).
*   **La verificación que apliqué fue**: Ejecutar las pruebas de contrato oficiales `./test.sh` y ver que pasaban sin fallas.

---

## 🌐 Fase 5: Ampliación de la API y Conexión con Interfaz de Usuario

### 📋 Prompt 8: Implementación de endpoints REST y DELETE
*   **El objetivo era**: Añadir flexibilidad a la API proveyendo endpoints limpios basados en parámetros de ruta (`GET /context/{user_id}` y `DELETE /context/{user_id}`) e implementar sus pruebas de integración correspondientes de forma previa.
*   **El prompt que usé fue**:
    > "Agrega un endpoint GET /context/{user_id} al backend que devuelva el historial de contexto de ese usuario en JSON. Incluye también el endpoint DELETE /context/{user_id} para limpiarlo. Escribe primero las pruebas de integración para estos endpoints, luego la implementación."
*   **La respuesta fue**:
    1. Agregó las dos pruebas de integración a `tests/validation/test_cag_contract.py` con una función helper para llamadas `DELETE`.
    2. Creó el enrutamiento por segmentos y la función `do_DELETE` en `server.py`.
    3. Habilitó el verbo `DELETE` en la configuración CORS del backend.
*   **Mi decisión humana fue**:
    *   Detener manualmente el servidor backend que corría la versión antigua en memoria y reiniciarlo para evitar el error `Failed to fetch` producido por llamadas `DELETE` no enrutadas en el proceso anterior.
*   **Los cambios que hice fueron**:
    *   Modificaciones en `tests/validation/test_cag_contract.py` y `backend/server.py`.
*   **La verificación que apliqué fue**: Correr `./test.sh` (los 5 tests integrados pasaron en su totalidad) y validar manualmente mediante llamadas `curl` en la terminal.

---

### 📋 Prompt 9: Integración del Panel Lateral y Limpieza en el Frontend
*   **El objetivo era**: Habilitar en el cliente web la capacidad de enviar el ID de usuario activo en las consultas, reflejar en tiempo real su historial de contexto dinámico en la barra lateral e incorporar un botón para limpiar los datos que invoque el endpoint `DELETE`.
*   **El prompt que usé fue**:
    > "El frontend actual necesita:
    > 1. Enviar un user_id junto con cada consulta.
    > 2. Mostrar opcionalmente el historial de contexto en un panel lateral simple.
    > 3. Tener un botón para limpiar el contexto.
    > Muéstrame los cambios mínimos necesarios. Prioriza que funcione sobre que sea visualmente perfecto."
*   **La respuesta fue**: Diseños HTML mínimos para añadir un botón con estilos CSS básicos en `index.html` e implementar en `app.js` un event listener que detecte pulsaciones del botón, llame a `DELETE /context/{user_id}` y limpie la pantalla.
*   **Mi decisión humana fue**: Aplicar los cambios, agregar un escuchador de evento de entrada (`input`) sobre el campo del identificador de usuario para refrescar proactivamente el panel lateral en cuanto se digita un nombre distinto de usuario.
*   **Los cambios que hice fueron**:
    *   Modificación de [**`frontend/index.html`**] y [**`frontend/app.js`**].
*   **La verificación que apliqué fue**: Navegación en vivo sobre la UI, logrando chatear, ver los registros agregarse en formato JSON en tiempo real a la derecha, cambiar de usuario viendo aislamiento y usar con éxito el botón para vaciar el contexto.
