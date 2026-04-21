"""Phase 3 tests — profiles, memory entities, Obsidian, automations."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Profiles
# ---------------------------------------------------------------------------

class TestProfiles:
    def setup_method(self):
        self.tmp = Path(tempfile.mkdtemp())

    def test_default_profile(self):
        from adv_archon.core.profiles import ProfileManager, PROFILES
        pm = ProfileManager(self.tmp)
        pm.load()
        assert pm.active.name == "default"

    def test_set_profile(self):
        from adv_archon.core.profiles import ProfileManager
        pm = ProfileManager(self.tmp)
        pm.set("work")
        assert pm.active.name == "work"

    def test_persist_profile(self):
        from adv_archon.core.profiles import ProfileManager
        pm1 = ProfileManager(self.tmp)
        pm1.set("coding")
        pm2 = ProfileManager(self.tmp)
        pm2.load()
        assert pm2.active.name == "coding"

    def test_invalid_profile(self):
        from adv_archon.core.profiles import ProfileManager
        pm = ProfileManager(self.tmp)
        with pytest.raises(ValueError, match="Unknown profile"):
            pm.set("nonexistent")

    def test_list_profiles(self):
        from adv_archon.core.profiles import ProfileManager
        pm = ProfileManager(self.tmp)
        profiles = pm.list_all()
        names = [p["name"] for p in profiles]
        assert "work" in names
        assert "personal" in names
        assert "research" in names
        assert "coding" in names

    def test_auto_detect_coding(self):
        from adv_archon.core.profiles import ProfileManager
        pm = ProfileManager(self.tmp)
        # create a fake pyproject.toml to trigger coding profile
        (self.tmp / "pyproject.toml").write_text("[project]\n")
        result = pm.auto_detect(self.tmp)
        assert result is not None
        assert result.name == "coding"

    def test_system_overlay_work(self):
        from adv_archon.core.profiles import ProfileManager
        pm = ProfileManager(self.tmp)
        pm.set("work")
        overlay = pm.system_overlay()
        assert "TRABAJO" in overlay

    def test_system_overlay_default_empty(self):
        from adv_archon.core.profiles import ProfileManager
        pm = ProfileManager(self.tmp)
        assert pm.system_overlay() == ""


# ---------------------------------------------------------------------------
# Memory entities
# ---------------------------------------------------------------------------

class TestMemoryEntities:
    def setup_method(self):
        self.tmp = Path(tempfile.mkdtemp())
        # Reset singleton
        import adv_archon.core.memory_entities as me
        me._store = None

    def _store(self):
        from adv_archon.core.memory_entities import EntityStore
        return EntityStore(self.tmp / "memory.db")

    def test_upsert_and_get_person(self):
        from adv_archon.core.memory_entities import Person
        store = self._store()
        p = Person(name="María García", company="Acme", role="CTO", email="maria@acme.com")
        pid = store.upsert_person(p)
        assert pid > 0
        result = store.get_person("María García")
        assert result is not None
        assert result["company"] == "Acme"
        assert result["role"] == "CTO"

    def test_upsert_person_updates(self):
        from adv_archon.core.memory_entities import Person
        store = self._store()
        store.upsert_person(Person(name="Juan", company="OldCo"))
        store.upsert_person(Person(name="Juan", company="NewCo"))
        result = store.get_person("Juan")
        assert result["company"] == "NewCo"

    def test_search_persons(self):
        from adv_archon.core.memory_entities import Person
        store = self._store()
        store.upsert_person(Person(name="Ana López", company="Startup X"))
        store.upsert_person(Person(name="Pedro", company="Corp Y"))
        results = store.search_persons("startup")
        assert len(results) == 1
        assert results[0]["name"] == "Ana López"

    def test_person_tags(self):
        from adv_archon.core.memory_entities import Person
        store = self._store()
        store.upsert_person(Person(name="Carlos", tags=["cliente", "vip"]))
        result = store.get_person("Carlos")
        assert "cliente" in result["tags"]

    def test_upsert_and_get_project(self):
        from adv_archon.core.memory_entities import Project
        store = self._store()
        p = Project(name="QuantBot", status="active", tech_stack=["Python", "FastAPI"])
        pid = store.upsert_project(p)
        assert pid > 0
        result = store.get_project("QuantBot")
        assert result is not None
        assert "Python" in result["tech_stack"]

    def test_list_active_projects(self):
        from adv_archon.core.memory_entities import Project
        store = self._store()
        store.upsert_project(Project(name="Proj A", status="active"))
        store.upsert_project(Project(name="Proj B", status="archived"))
        results = store.list_projects(status="active")
        names = [p["name"] for p in results]
        assert "Proj A" in names
        assert "Proj B" not in names

    def test_set_and_get_preference(self):
        store = self._store()
        store.set_preference("trabajo", "horario", "9-18")
        val = store.get_preference("trabajo", "horario")
        assert val == "9-18"

    def test_preference_upsert(self):
        store = self._store()
        store.set_preference("trabajo", "idioma", "español")
        store.set_preference("trabajo", "idioma", "inglés")
        val = store.get_preference("trabajo", "idioma")
        assert val == "inglés"

    def test_list_preferences_by_category(self):
        store = self._store()
        store.set_preference("trabajo", "horario", "9-18")
        store.set_preference("personal", "deporte", "ciclismo")
        results = store.list_preferences(category="trabajo")
        assert len(results) == 1
        assert results[0]["key"] == "horario"

    def test_add_and_search_decision(self):
        from adv_archon.core.memory_entities import Decision
        store = self._store()
        d = Decision(
            title="Elegir ORM",
            decision="SQLAlchemy",
            context="Necesitábamos async support",
            project="QuantBot",
        )
        did = store.add_decision(d)
        assert did > 0
        results = store.search_decisions("SQLAlchemy")
        assert len(results) >= 1
        assert results[0]["title"] == "Elegir ORM"

    def test_list_decisions_by_project(self):
        from adv_archon.core.memory_entities import Decision
        store = self._store()
        store.add_decision(Decision(title="D1", decision="X", project="ProjectA"))
        store.add_decision(Decision(title="D2", decision="Y", project="ProjectB"))
        results = store.list_decisions(project="ProjectA")
        assert len(results) == 1
        assert results[0]["title"] == "D1"


# ---------------------------------------------------------------------------
# Tool functions
# ---------------------------------------------------------------------------

class TestEntityToolFunctions:
    def setup_method(self):
        self.tmp = Path(tempfile.mkdtemp())
        import os
        os.environ["ADV_ARCHON_HOME"] = str(self.tmp)
        import adv_archon.core.memory_entities as me
        me._store = None

    def test_remember_and_recall_person(self):
        from adv_archon.core.memory_entities import remember_person, recall_person
        result = remember_person("María", company="Acme", email="m@acme.com")
        assert result["status"] == "guardado"
        found = recall_person("Acme")
        assert len(found) == 1
        assert found[0]["name"] == "María"

    def test_remember_and_recall_project(self):
        from adv_archon.core.memory_entities import remember_project, recall_project
        result = remember_project("MiApp", tech_stack="Django,React", status="active")
        assert result["status"] == "guardado"
        found = recall_project("MiApp")
        assert len(found) == 1
        assert "Django" in found[0]["tech_stack"]

    def test_log_and_recall_decisions(self):
        from adv_archon.core.memory_entities import log_decision, recall_decisions
        result = log_decision(
            title="Base de datos",
            decision="PostgreSQL",
            rationale="Mejor soporte JSONB",
        )
        assert result["status"] == "guardado"
        found = recall_decisions(query="PostgreSQL")
        assert len(found) >= 1

    def test_set_and_list_preferences(self):
        from adv_archon.core.memory_entities import set_preference, list_preferences
        set_preference("trabajo", "horario", "flexible")
        results = list_preferences(category="trabajo")
        assert any(r["key"] == "horario" for r in results)


# ---------------------------------------------------------------------------
# Obsidian connector (filesystem-based, no real vault needed)
# ---------------------------------------------------------------------------

class TestObsidianConnector:
    def setup_method(self):
        self.vault = Path(tempfile.mkdtemp())
        import os
        os.environ["OBSIDIAN_VAULT_PATH"] = str(self.vault)

    def _write_note(self, name: str, content: str) -> Path:
        p = self.vault / f"{name}.md"
        p.write_text(content)
        return p

    def test_search_obsidian_finds_match(self):
        from adv_archon.tools.obsidian import search_obsidian
        self._write_note("ProjectAlpha", "# ProjectAlpha\n\nIdeas sobre machine learning y Python.")
        self._write_note("Notas", "# Notas\n\nCosas aleatorias.")
        results = search_obsidian("machine learning")
        assert len(results) >= 1
        assert results[0]["title"] == "ProjectAlpha"

    def test_search_obsidian_no_match(self):
        from adv_archon.tools.obsidian import search_obsidian
        self._write_note("Test", "# Test\n\nContenido sin relación.")
        results = search_obsidian("quantum computing xyz")
        assert len(results) == 0

    def test_read_obsidian_note(self):
        from adv_archon.tools.obsidian import read_obsidian_note
        self._write_note("MiNota", "# MiNota\n\nContenido de prueba.")
        result = read_obsidian_note("MiNota.md")
        assert "Contenido de prueba" in result

    def test_list_recent_notes(self):
        from adv_archon.tools.obsidian import list_recent_obsidian_notes
        self._write_note("A", "# A\n\nPrimera nota.")
        self._write_note("B", "# B\n\nSegunda nota.")
        results = list_recent_obsidian_notes(limit=5)
        assert len(results) == 2

    def test_create_obsidian_note(self):
        from adv_archon.tools.obsidian import create_obsidian_note, read_obsidian_note
        result = create_obsidian_note("Nueva Nota", "Contenido generado.", tags=["test"])
        assert result["title"] == "Nueva Nota"
        content = read_obsidian_note(result["path"])
        assert "Contenido generado" in content
        assert "test" in content

    def test_create_note_in_subfolder(self):
        from adv_archon.tools.obsidian import create_obsidian_note
        result = create_obsidian_note("Sub Nota", "Contenido.", folder="Work")
        assert "Work/" in result["path"]

    def test_search_by_tag(self):
        from adv_archon.tools.obsidian import search_obsidian_by_tag
        content = "---\ntags: [proyecto, urgente]\n---\n# Proyecto X\n"
        self._write_note("ProyectoX", content)
        results = search_obsidian_by_tag("urgente")
        assert any(r["title"] == "ProyectoX" for r in results)

    def test_get_backlinks(self):
        from adv_archon.tools.obsidian import get_obsidian_backlinks
        self._write_note("A", "# A\n\nEnlaza a [[B]].")
        self._write_note("B", "# B\n\nNota B.")
        self._write_note("C", "# C\n\nTambién enlaza a [[B|nota b]].")
        links = get_obsidian_backlinks("B.md")
        paths = [l["path"] for l in links]
        assert any("A" in p for p in paths)
        assert any("C" in p for p in paths)

    def test_read_nonexistent_note(self):
        from adv_archon.tools.obsidian import read_obsidian_note, ObsidianError
        with pytest.raises(ObsidianError, match="no encontrada"):
            read_obsidian_note("no_existe.md")


# ---------------------------------------------------------------------------
# Automations
# ---------------------------------------------------------------------------

class TestAutomations:
    def setup_method(self):
        self.tmp = Path(tempfile.mkdtemp())
        import os
        os.environ["ADV_ARCHON_HOME"] = str(self.tmp)

    def test_repo_watcher_first_time(self, tmp_path):
        import subprocess
        from adv_archon.core.automations import RepoWatcher
        repo = tmp_path / "repo"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, capture_output=True)
        (repo / "file.txt").write_text("hello")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=repo, capture_output=True)
        watcher = RepoWatcher(self.tmp)
        result = watcher.check(repo)
        assert result["status"] == "primera_vez"

    def test_repo_watcher_no_changes(self, tmp_path):
        import subprocess
        from adv_archon.core.automations import RepoWatcher
        repo = tmp_path / "repo"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, capture_output=True)
        (repo / "file.txt").write_text("hello")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=repo, capture_output=True)
        watcher = RepoWatcher(self.tmp)
        watcher.check(repo)  # first time
        result = watcher.check(repo)  # second time, no new commits
        assert result["status"] == "sin_cambios"

    def test_repo_watcher_detects_changes(self, tmp_path):
        import subprocess
        from adv_archon.core.automations import RepoWatcher
        repo = tmp_path / "repo"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, capture_output=True)
        (repo / "file.txt").write_text("hello")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=repo, capture_output=True)
        watcher = RepoWatcher(self.tmp)
        watcher.check(repo)  # register initial HEAD
        # add new commit
        (repo / "file2.txt").write_text("world")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "add file2"], cwd=repo, capture_output=True)
        result = watcher.check(repo)
        assert result["status"] == "cambios"
        assert any("add file2" in c for c in result.get("commits", []))
