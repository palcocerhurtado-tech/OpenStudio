# Instalación de ADV ARCHON en tu Mac

## 1. Copia los archivos nuevos

```bash
cd ~/code/ADV-Archon

# Reemplaza los archivos del proyecto con los nuevos
cp -r path/to/adv-archon/src/adv_archon/* src/adv_archon/
cp path/to/adv-archon/pyproject.toml .
```

O más fácil — copia toda la carpeta `adv-archon/` del repo y luego:

```bash
# Desde la carpeta que contiene adv-archon/
rsync -av adv-archon/src/adv_archon/ ~/code/ADV-Archon/src/adv_archon/
cp adv-archon/pyproject.toml ~/code/ADV-Archon/pyproject.toml
```

## 2. Instala dependencias

```bash
cd ~/code/ADV-Archon
uv pip install -e ".[cloud]"   # incluye Gemini
# o solo local:
uv pip install -e .
```

## 3. Instala globalmente

```bash
uv tool install ~/code/ADV-Archon --force
```

## 4. Configura

```bash
mkdir -p ~/.adv-archon
cp adv-archon/.env.example ~/.adv-archon/.env
# Edita ~/.adv-archon/.env con tus claves
```

## 5. Verifica

```bash
adv-archon --help
adv --help
adv   # arranca el REPL
```

## Requisitos previos

- Ollama instalado y corriendo: `ollama serve`
- Modelo descargado: `ollama pull llama3.1:8b`
- Python 3.10+
- uv instalado

## Comandos disponibles en el REPL

| Comando | Descripción |
|---------|-------------|
| `/help` | Ver todos los comandos |
| `/mode local\|cloud` | Cambiar motor LLM |
| `/profile work\|personal\|research\|coding` | Cambiar perfil |
| `/dashboard` | Panel con calendario, tareas y coste |
| `/recall <query>` | Buscar en memoria |
| `/remember <texto>` | Guardar recuerdo |
| `/run <cmd>` | Ejecutar comando shell |
| `/web <búsqueda>` | Buscar en internet |
| `/read <archivo>` | Leer archivo |
| `/auto on\|off` | Modo automático |
| `/weekly` | Revisión semanal |
| `/people [query]` | Personas en memoria |
| `/projects` | Proyectos activos |
| `/cost` | Coste de la sesión |
| `/exit` | Salir |
