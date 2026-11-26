"""Tests for sdlc_gates.py. Run: python3 -m unittest hooks/test_sdlc_gates.py -v"""
import json, subprocess, sys, tempfile, unittest
from datetime import datetime, timedelta
from pathlib import Path

HOOK = Path(__file__).with_name("sdlc_gates.py")


def run_hook(tool, cwd, **tool_input):
    r = subprocess.run([sys.executable, "-I", str(HOOK)], capture_output=True, text=True,
                       input=json.dumps({"tool_name": tool, "cwd": str(cwd), "tool_input": tool_input}))
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)["hookSpecificOutput"]["permissionDecision"] if r.stdout.strip() else "allow"


def iso(**delta):
    return (datetime.now().astimezone() + timedelta(**delta)).isoformat(timespec="seconds")


class GateTest(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.addCleanup(self._t.cleanup)
        self.root = Path(self._t.name).resolve() / "proj"
        for d in ("api-x/migrations", "app-y/src", "docs/adr"):
            (self.root / d).mkdir(parents=True)
        (self.root / "AGENTS.md").write_text("Zero-Skip Gates")
        (self.root / "app-y/src/a.py").write_text("x=1")

    def freeze(self, text):
        (self.root / ".sdlc-freeze").write_text(text)

    def write(self, rel, tool="Write"):
        return run_hook(tool, self.root, file_path=str(self.root / rel))

    def bash(self, cmd, cwd=None):
        return run_hook("Bash", cwd or self.root, command=cmd)


class AdrGate(GateTest):
    def test_new_code_without_adr_asks(self):
        self.assertEqual(self.write("api-x/main.py"), "ask")

    def test_non_code_file_allowed(self):
        self.assertEqual(self.write("api-x/README.md"), "allow")

    def test_scaffolded_dir_allowed(self):
        self.assertEqual(self.write("app-y/src/b.py"), "allow")

    def test_edit_existing_allowed(self):
        self.assertEqual(self.write("app-y/src/a.py", "Edit"), "allow")

    def test_adr_present_allowed(self):
        (self.root / "docs/adr/0001.md").write_text("- **Estado:** Aceptada")
        self.assertEqual(self.write("api-x/main.py"), "allow")

    def test_unaccepted_adr_asks(self):
        for text in ("# adr", "- **Estado:** En validación", "Estado: Descartada"):
            (self.root / "docs/adr/0001.md").write_text(text)
            with self.subTest(text): self.assertEqual(self.write("api-x/main.py"), "ask")

    def test_outside_project_allowed(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(run_hook("Write", d, file_path=f"{d}/api-z/m.py"), "allow")


class Levels(GateTest):
    HTTP = "api-x/src/p/adapters/inbound/http/r.py"
    SQLITE = "api-x/src/p/adapters/outbound/sqlite/r.py"
    PG = "api-x/src/p/adapters/outbound/postgres/r.py"
    UI = "app-y/src/b.py"

    def setUp(self):
        super().setUp()
        (self.root / "docs/adr/0001.md").write_text("Estado: Aceptada")  # isolate from the ADR gate

    def level(self, text):
        (self.root / ".sdlc-state.json").write_text(text)

    def test_later_levels_ask(self):
        self.level('{"level": 2}')
        for rel in (self.SQLITE, self.PG, self.UI):
            with self.subTest(rel): self.assertEqual(self.write(rel), "ask")
        for rel in (self.HTTP, "api-x/src/p/domain/rule.py", "app-y/README.md"):
            with self.subTest(rel): self.assertEqual(self.write(rel), "allow")

    def test_reached_level_allowed(self):
        self.level('{"level": 3}')
        self.assertEqual(self.write(self.SQLITE), "allow")
        self.assertEqual(self.write(self.PG), "ask")

    def test_missing_or_broken_state_allows(self):
        self.assertEqual(self.write(self.PG), "allow")
        for text in ("garbage", "{}", "[]", '{"level": null}'):
            self.level(text)
            with self.subTest(text): self.assertEqual(self.write(self.PG), "allow")


class PureBusiness(GateTest):
    def put(self, rel, text, tool="Write"):
        key = "content" if tool == "Write" else "new_string"
        return run_hook(tool, self.root, file_path=str(self.root / rel), **{key: text})

    def test_tech_in_business_artifacts_asks(self):
        cases = [("docs/negocio/RF-01.md", "El sistema usa FastAPI"),
                 ("docs/requisitos/rf.md", "Exponer POST /api/pedidos"),
                 ("docs/dmn/br-01.md", "campo VARCHAR(50)"),
                 ("flujo.bpmn", "<task name='Guardar en PostgreSQL'/>"),
                 ("docs/RNF-02.md", "Desplegar con Docker"),
                 ("docs/bpmn/to-be.mmd", "A --> B[Llamar GET /users]")]
        for rel, text in cases:
            with self.subTest(rel): self.assertEqual(self.put(rel, text), "ask")

    def test_pure_business_text_allowed(self):
        for rel in ("docs/negocio/RF-01.md", "reglas.dmn"):
            with self.subTest(rel):
                self.assertEqual(self.put(rel, "El cliente puede reaccionar al pedido; fecha, texto y total."), "allow")

    def test_non_business_files_may_mention_tech(self):
        for rel in ("docs/arquitectura/stack.md", "docs/adr/0001.md", "README.md", "api-x/notes.md"):
            with self.subTest(rel): self.assertEqual(self.put(rel, "Usamos FastAPI y PostgreSQL"), "allow")

    def test_edit_only_scans_new_text(self):
        rel = "docs/negocio/RF-01.md"
        (self.root / "docs/negocio").mkdir(parents=True)
        (self.root / rel).write_text("legacy FastAPI mention")
        self.assertEqual(self.put(rel, "texto limpio", "Edit"), "allow")
        self.assertEqual(self.put(rel, "ahora Django", "Edit"), "ask")

    def test_multiedit(self):
        r = run_hook("MultiEdit", self.root, file_path=str(self.root / "docs/negocio/RF-01.md"),
                     edits=[{"new_string": "ok"}, {"new_string": "usa Redis"}])
        self.assertEqual(r, "ask")


class Freeze(GateTest):
    ASK = ["git push origin main", "git  push", "cd x && git push", "bash -c 'docker compose up'",
           "git -C . push", "git --no-pager push", "git -c user.name=x push",
           "docker compose up -d", "docker compose -f x.yml up", "docker compose --profile dev up -d",
           "docker-compose up", "docker-compose -f x.yml up", "docker push img",
           "terraform apply", "alembic upgrade head", "kubectl apply -f x.yaml"]
    ALLOW = ["ls -la", "git status", "git log --oneline", "echo git pushing", "git -C . status",
             "docker ps", "docker run -v a:b alpine", "docker compose -f x.yml ps", "docker compose logs up"]

    def test_commands_during_freeze(self):
        self.freeze(f"event_start: {iso(hours=10)}\n")
        for c in self.ASK:
            with self.subTest(c): self.assertEqual(self.bash(c), "ask")
        for c in self.ALLOW:
            with self.subTest(c): self.assertEqual(self.bash(c), "allow")

    def test_python_wrapped_command(self):
        self.freeze(f"event_start: {iso(hours=1)}\n")
        self.assertEqual(self.bash("python3 -c 'import os;os.system(\"git push\")'"), "ask")

    def test_migration_file_asks_only_in_freeze(self):
        (self.root / "docs/adr/0001.md").write_text("Estado: Aceptada")  # isolate from the ADR gate
        self.assertEqual(self.write("api-x/migrations/001.sql"), "allow")
        self.freeze(f"event_start: {iso(hours=5)}\n")
        self.assertEqual(self.write("api-x/migrations/001.sql"), "ask")

    def test_no_freeze_allows_push(self):
        self.assertEqual(self.bash("git push"), "allow")

    def test_event_far_away(self):
        self.freeze(f"event_start: {iso(days=3)}\n")
        self.assertEqual(self.bash("git push"), "allow")

    def test_event_running(self):
        self.freeze(f"event_start: {iso(hours=-2)}\n")
        self.assertEqual(self.bash("git push"), "ask")

    def test_event_over_default_12h(self):
        self.freeze(f"event_start: {iso(hours=-20)}\n")
        self.assertEqual(self.bash("git push"), "allow")

    def test_explicit_event_end(self):
        self.freeze(f"event_start: {iso(hours=-3)}\nevent_end: {iso(hours=-1)}\n")
        self.assertEqual(self.bash("git push"), "allow")

    def test_outside_project_allowed(self):
        self.freeze(f"event_start: {iso(hours=1)}\n")
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(self.bash("git push", cwd=d), "allow")


class Increment(GateTest):
    def setUp(self):
        super().setUp()
        (self.root / ".sdlc/active").mkdir(parents=True)

    def state(self, level=2, project_type="internal", gates=(), **extra):
        (self.root / ".sdlc/state.json").write_text(json.dumps(
            {"level": level, "project_type": project_type, "gates": {g: True for g in gates}, **extra}))

    def run_raw(self, tool, **inp):
        r = subprocess.run([sys.executable, "-I", str(HOOK)], capture_output=True, text=True,
                           input=json.dumps({"tool_name": tool, "cwd": str(self.root), "tool_input": inp}))
        if r.returncode == 2:
            return "block"
        assert r.returncode == 0, r.stderr
        return "ask" if r.stdout.strip() else "allow"

    def edit(self, rel):
        return self.run_raw("Edit", file_path=str(self.root / rel), new_string="x")

    def ready(self):
        (self.root / ".sdlc/active/01-stories.md").write_text("HU-01")
        (self.root / "docs/adr/0001.md").write_text("Estado: Aceptada")

    def test_without_state_nothing_new(self):
        self.assertEqual(self.run_raw("Bash", command="git commit -m x"), "allow")
        self.assertEqual(self.edit("app-y/src/a.py"), "allow")

    def test_code_needs_stories_and_adr_by_level(self):
        self.state()
        self.assertEqual(self.edit("api-x/src/a.py"), "block")
        self.ready()
        self.state(gates=["phase_1_2_stories"])
        self.assertEqual(self.edit("api-x/src/a.py"), "block")
        self.state(level=1, gates=["phase_1_2_stories"])
        self.assertEqual(self.edit("api-x/src/a.py"), "allow")
        self.state(level=5, gates=["phase_1_2_stories", "phase_3_adr_approved"])
        self.assertEqual(self.edit("api-x/src/a.py"), "allow")

    def test_new_nested_folder_is_still_gated(self):
        self.state()
        self.assertEqual(self.edit("api-x/src/new/deep/m.py"), "block")

    def test_client_without_approved_proposal(self):
        self.state(project_type="client")
        self.assertEqual(self.edit("README.md"), "block")
        self.assertEqual(self.edit(".sdlc/00-idea-brief.md"), "allow")
        self.assertEqual(self.edit(".sdlc/proposal-a.md"), "allow")

    def test_state_changes_ask(self):
        self.state(project_type="client")
        self.assertEqual(self.edit(".sdlc/state.json"), "ask")

    def test_commit_gate(self):
        self.state()
        for c in ("git commit -m x", "git -C . push"):
            with self.subTest(c): self.assertEqual(self.run_raw("Bash", command=c), "block")
        self.assertEqual(self.run_raw("Bash", command="git status"), "allow")
        self.state(gates=["phase_4_5_tests_passed"])
        self.assertEqual(self.run_raw("Bash", command="git commit -m x"), "allow")
        self.state(gates=["phase_4_5_tests_passed"], pending_doc_sync=True)
        self.assertEqual(self.run_raw("Bash", command="git commit -m x"), "block")

    def test_freeze_until(self):
        self.state(freeze_until=iso(hours=2))
        self.assertEqual(self.run_raw("Bash", command="terraform apply"), "block")
        self.assertEqual(self.run_raw("Bash", command="ls productos"), "allow")
        self.state(freeze_until=iso(hours=-2))
        self.assertEqual(self.run_raw("Bash", command="terraform apply"), "allow")

    def test_invalid_state_asks(self):
        (self.root / ".sdlc/state.json").write_text("{")
        self.assertEqual(self.edit("README.md"), "ask")


class Robustness(GateTest):
    def test_malformed_freeze_allows(self):
        self.freeze("event_start: garbage\n")
        self.assertEqual(self.bash("git push"), "allow")

    def test_invalid_json_stdin(self):
        r = subprocess.run([sys.executable, "-I", str(HOOK)], input="not json", capture_output=True, text=True)
        self.assertEqual((r.returncode, r.stdout), (0, ""))


if __name__ == "__main__":
    unittest.main()
