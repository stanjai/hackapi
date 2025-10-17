# autointegrator.py
import os
import re
import json
import textwrap
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from difflib import unified_diff

SUPPORTED = {
    "Senso",
    "Airia",
    "OpenAI",
    "TrueFoundry",
    "ElevenLabs",
    "Intercom",
    "Snowflake",
    "Lightfield",
    "Redpanda",
    "Sentry",
    "StackAI",
    "Apify",
}

# --------------------------
# Data structures
# --------------------------
@dataclass
class FileChange:
    path: str
    original: Optional[str]  # None for new file
    updated: str

@dataclass
class IntegrationPlan:
    changes: List[FileChange] = field(default_factory=list)
    pip_dependencies: List[str] = field(default_factory=list)
    env_placeholders: Dict[str, str] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)

    def to_unified_diff(self) -> str:
        parts: List[str] = []
        for ch in self.changes:
            old = ch.original or ""
            new = ch.updated
            diff = unified_diff(
                old.splitlines(keepends=True),
                new.splitlines(keepends=True),
                fromfile=f"a/{ch.path}" if ch.original is not None else "/dev/null",
                tofile=f"b/{ch.path}",
                lineterm=""
            )
            parts.append("".join(diff))
        return "\n\n".join(parts)

# --------------------------
# Repo abstraction
# --------------------------
@dataclass
class RepoSnapshot:
    files: Dict[str, str]  # path -> content

    @staticmethod
    def from_single_entrypoint(path: str, content: str) -> "RepoSnapshot":
        return RepoSnapshot(files={path: content})

    def read(self, path: str) -> Optional[str]:
        return self.files.get(path)

    def exists(self, path: str) -> bool:
        return path in self.files

    def with_change(self, path: str, new_content: str) -> "RepoSnapshot":
        new = dict(self.files)
        new[path] = new_content
        return RepoSnapshot(files=new)

# --------------------------
# Adapter base
# --------------------------
class Adapter:
    name: str

    def plan(self, repo: RepoSnapshot) -> IntegrationPlan:
        raise NotImplementedError

# --------------------------
# Utilities for code surgery
# --------------------------
IMPORT_SENTINEL_RE = re.compile(r"^(import |from )", re.MULTILINE)

def ensure_imports(existing: str, import_lines: List[str]) -> str:
    if not import_lines:
        return existing
    # Insert imports after any initial shebang or encoding lines and before first import if possible
    lines = existing.splitlines()
    insertion_idx = 0
    for i, line in enumerate(lines[:10]):  # look near the top
        if IMPORT_SENTINEL_RE.match(line):
            insertion_idx = i
            break
        if line.strip().startswith('"""') or line.strip().startswith("'''"):
            # skip module docstring
            # find its end
            quote = line.strip()[:3]
            j = i + 1
            while j < len(lines) and quote not in lines[j]:
                j += 1
            insertion_idx = j + 1
            break
        insertion_idx = i + 1
    imports_block = "\n".join(import_lines).rstrip() + "\n"
    new_lines = lines[:insertion_idx] + [imports_block] + lines[insertion_idx:]
    return "\n".join(new_lines)

def insert_into_function(existing: str, func_name: str, body_lines: List[str]) -> str:
    """
    Append body_lines inside the function's body, before its final return if present.
    Fallback to creating the function if it does not exist.
    """
    pattern = re.compile(rf"def\s+{func_name}\s*\([^)]*\)\s*:\s*\n", re.MULTILINE)
    m = pattern.search(existing)
    block = textwrap.indent("\n".join(body_lines).rstrip() + "\n", "    ")
    if not m:
        # Create the function at end of file
        return existing.rstrip() + f"\n\ndef {func_name}():\n{block}\n"
    # Find indentation block end
    start = m.end()
    # Find the next top-level def or if __name__ == "__main__"
    top_level = re.compile(r"^\S", re.MULTILINE)
    n = top_level.search(existing, start)
    end = n.start() if n else len(existing)
    func_body = existing[start:end]
    # Try to place before a "return" near the end, else append
    return_pos = func_body.rfind("\n    return")
    if return_pos != -1:
        insertion_point = start + return_pos
        new_text = existing[:insertion_point] + "\n" + block + existing[insertion_point:]
    else:
        new_text = existing[:end] + block + existing[end:]
    return new_text

def ensure_main_invocation(existing: str, func_name: str) -> str:
    main_guard = "if __name__ == \"__main__\":"
    if main_guard in existing:
        # Try to ensure the function is called somewhere under the guard
        if func_name in existing:
            return existing
        # naive insertion under guard
        pattern = re.compile(r"if\s+__name__\s*==\s*['\"]__main__['\"]\s*:\s*\n")
        m = pattern.search(existing)
        if not m:
            return existing + f"\n\nif __name__ == \"__main__\":\n    {func_name}()\n"
        idx = m.end()
        return existing[:idx] + f"    {func_name}()\n" + existing[idx:]
    return existing + f"\n\nif __name__ == \"__main__\":\n    {func_name}()\n"

def mk_dir_init(pkg_path: str) -> Tuple[str, str]:
    return (f"{pkg_path}/__init__.py", "# integrations package\n")

# --------------------------
# Concrete adapters
# --------------------------
class SentryAdapter(Adapter):
    name = "Sentry"

    def plan(self, repo: RepoSnapshot) -> IntegrationPlan:
        plan = IntegrationPlan()
        plan.pip_dependencies += ["sentry-sdk"]
        plan.env_placeholders.update({
            "SENTRY_DSN": "https://<key>@<org>.ingest.sentry.io/<project>"
        })
        # file
        path = "integrations/sentry_setup.py"
        content = textwrap.dedent("""
            import os
            import sentry_sdk

            def init_sentry() -> None:
                dsn = os.getenv("SENTRY_DSN")
                if not dsn:
                    # proceed without Sentry if not set
                    return
                sentry_sdk.init(
                    dsn=dsn,
                    traces_sample_rate=1.0
                )

            def capture_exception(exc: Exception) -> None:
                try:
                    import sentry_sdk
                    sentry_sdk.capture_exception(exc)
                except Exception:
                    pass
        """).strip() + "\n"
        plan.changes.append(FileChange(path=path, original=repo.read(path), updated=content))
        plan.notes.append("Sentry initialized at runtime if SENTRY_DSN is set.")
        return plan

class RedpandaAdapter(Adapter):
    name = "Redpanda"

    def plan(self, repo: RepoSnapshot) -> IntegrationPlan:
        plan = IntegrationPlan()
        plan.pip_dependencies += ["confluent-kafka"]
        plan.env_placeholders.update({
            "REDPANDA_BROKERS": "localhost:9092",
            "REDPANDA_TOPIC": "events.demo"
        })
        path = "integrations/redpanda_io.py"
        content = textwrap.dedent("""
            import os
            import json
            from typing import Iterable, List
            from confluent_kafka import Producer, Consumer

            def _brokers() -> str:
                return os.getenv("REDPANDA_BROKERS", "localhost:9092")

            def _topic() -> str:
                return os.getenv("REDPANDA_TOPIC", "events.demo")

            def produce_records(records: Iterable[dict]) -> None:
                p = Producer({"bootstrap.servers": _brokers()})
                topic = _topic()
                for r in records:
                    p.produce(topic, json.dumps(r).encode("utf-8"))
                p.flush()

            def consume_records(max_messages: int = 100, timeout: float = 2.0) -> List[dict]:
                c = Consumer({
                    "bootstrap.servers": _brokers(),
                    "group.id": "demo-consumer",
                    "auto.offset.reset": "earliest"
                })
                c.subscribe([_topic()])
                out: List[dict] = []
                for _ in range(max_messages):
                    msg = c.poll(timeout)
                    if msg is None:
                        break
                    if msg.error():
                        continue
                    try:
                        out.append(json.loads(msg.value().decode("utf-8")))
                    except Exception:
                        pass
                c.close()
                return out
        """).strip() + "\n"
        plan.changes.append(FileChange(path=path, original=repo.read(path), updated=content))
        return plan

class SnowflakeAdapter(Adapter):
    name = "Snowflake"

    def plan(self, repo: RepoSnapshot) -> IntegrationPlan:
        plan = IntegrationPlan()
        plan.pip_dependencies += ["snowflake-connector-python"]
        plan.env_placeholders.update({
            "SNOWFLAKE_USER": "user",
            "SNOWFLAKE_PASSWORD": "password",
            "SNOWFLAKE_ACCOUNT": "account.region",
            "SNOWFLAKE_WAREHOUSE": "COMPUTE_WH",
            "SNOWFLAKE_DATABASE": "DEMO_DB",
            "SNOWFLAKE_SCHEMA": "PUBLIC",
        })
        path = "integrations/snowflake_io.py"
        content = textwrap.dedent("""
            import os
            from typing import List, Tuple
            import snowflake.connector

            def _conn():
                return snowflake.connector.connect(
                    user=os.environ["SNOWFLAKE_USER"],
                    password=os.environ["SNOWFLAKE_PASSWORD"],
                    account=os.environ["SNOWFLAKE_ACCOUNT"],
                    warehouse=os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH"),
                    database=os.getenv("SNOWFLAKE_DATABASE", "DEMO_DB"),
                    schema=os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC"),
                )

            def run_simple_query(sql: str = "SELECT CURRENT_TIMESTAMP();") -> List[Tuple]:
                with _conn() as conn:
                    with conn.cursor() as cur:
                        cur.execute(sql)
                        return cur.fetchall()
        """).strip() + "\n"
        plan.changes.append(FileChange(path=path, original=repo.read(path), updated=content))
        return plan

class OpenAIAdapter(Adapter):
    name = "OpenAI"

    def plan(self, repo: RepoSnapshot) -> IntegrationPlan:
        plan = IntegrationPlan()
        plan.pip_dependencies += ["openai>=1.0.0"]
        plan.env_placeholders.update({
            "OPENAI_API_KEY": "<your key>"
        })
        path = "integrations/openai_utils.py"
        content = textwrap.dedent("""
            import os
            from typing import List
            from openai import OpenAI

            _client = None

            def _get_client() -> OpenAI:
                global _client
                if _client is None:
                    _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                return _client

            def embed_and_summarize(texts: List[str], model_embed: str = "text-embedding-3-small", model_chat: str = "gpt-5") -> str:
                client = _get_client()
                # embeddings
                _ = client.embeddings.create(model=model_embed, input=texts)
                # summary
                completion = client.chat.completions.create(
                    model=model_chat,
                    messages=[
                        {"role": "system", "content": "You are a concise summarizer."},
                        {"role": "user", "content": "\\n\\n".join(texts)}
                    ],
                    temperature=0.2,
                    max_tokens=300
                )
                return completion.choices[0].message.content.strip()
        """).strip() + "\n"
        plan.changes.append(FileChange(path=path, original=repo.read(path), updated=content))
        return plan

# --------------------------
# Safe stubs for the rest
# --------------------------
def stub_module(name: str, repo: RepoSnapshot, doc: str) -> FileChange:
    code = f'''"""
{name} integration stub.
{doc}
Replace placeholders with the vendor SDK or HTTPS endpoints when ready.
"""
import os
from typing import Any, Dict

def {name.lower()}_configure(**kwargs) -> Dict[str, Any]:
    return {{"ok": True, "kwargs": kwargs}}

def {name.lower()}_run(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {{"ok": True, "echo": payload}}
'''
    path = f"integrations/{name.lower()}_client.py"
    return FileChange(path=path, original=repo.read(path), updated=code)

STUB_DOCS = {
    "Senso": "Send basic events. Expect base URL and API key in environment.",
    "Airia": "Run analysis over a dataset or stream. Expect token based auth.",
    "TrueFoundry": "Call a deployed model endpoint. Expect model URL and key.",
    "ElevenLabs": "Convert text to speech. Expect voice id and API key.",
    "Intercom": "Find contact and send message. Expect access token.",
    "Lightfield": "Image processing like crop or filter over a file path.",
    "StackAI": "Trigger a workflow by id and fetch result.",
    "Apify": "Start a web scraping actor and poll for dataset when finished.",
}

STUB_ENV = {
    "Senso": {"SENSO_API_KEY": "<key>", "SENSO_BASE_URL": "https://api.senso.example"},
    "Airia": {"AIRIA_TOKEN": "<token>", "AIRIA_BASE_URL": "https://api.airia.example"},
    "TrueFoundry": {"TRUEFOUNDRY_ENDPOINT": "https://...", "TRUEFOUNDRY_TOKEN": "<token>"},
    "ElevenLabs": {"ELEVEN_API_KEY": "<key>", "ELEVEN_VOICE_ID": "Rachel"},
    "Intercom": {"INTERCOM_TOKEN": "<token>"},
    "Lightfield": {},
    "StackAI": {"STACKAI_API_KEY": "<key>", "STACKAI_WORKFLOW_ID": "<id>"},
    "Apify": {"APIFY_TOKEN": "<token>", "APIFY_ACTOR_ID": "<actor-id>"},
}

STUB_PIP = {
    "Senso": [],
    "Airia": [],
    "TrueFoundry": [],
    "ElevenLabs": ["elevenlabs"],  # you can swap for HTTP later if you prefer
    "Intercom": ["intercom-client"],
    "Lightfield": ["Pillow"],
    "StackAI": [],
    "Apify": ["apify-client"],
}

# --------------------------
# Orchestration file generator
# --------------------------
def build_orchestration_file(selected: List[str]) -> str:
    lines = [
        "import logging",
        "from typing import Any, Dict, List",
        "",
        "from integrations.openai_utils import embed_and_summarize  # optional",
        "from integrations.redpanda_io import produce_records, consume_records  # optional",
        "from integrations.sentry_setup import init_sentry, capture_exception  # optional",
        "from integrations.snowflake_io import run_simple_query  # optional",
    ]
    for name in selected:
        if name in STUB_DOCS:
            lines.append(f"from integrations.{name.lower()}_client import {name.lower()}_configure, {name.lower()}_run")
    lines += [
        "",
        "log = logging.getLogger(__name__)",
        "",
        "def run_integrations_demo() -> Dict[str, Any]:",
        "    results: Dict[str, Any] = {}",
        "    try:",
        "        init_sentry()",
        "    except Exception:",
        "        pass",
        "    log.info('Running integration demo pipeline')",
        "    try:",
        "        # Snowflake example",
        "        try:",
        "            results['snowflake_now'] = run_simple_query()[0][0]",
        "        except Exception as e:",
        "            log.warning('Snowflake unavailable: %s', e)",
        "",
        "        # Apify or Senso producers can feed Redpanda",
        "        sample_records = [",
        "            {'id': 1, 'text': 'hello world'},",
        "            {'id': 2, 'text': 'stream event'},",
        "        ]",
        "        try:",
        "            produce_records(sample_records)",
        "            consumed = consume_records(max_messages=10, timeout=1.0)",
        "            results['redpanda_count'] = len(consumed)",
        "        except Exception as e:",
        "            log.warning('Redpanda unavailable: %s', e)",
        "",
        "        # OpenAI summary over consumed data",
        "        try:",
        "            texts = [str(r) for r in results.get('redpanda_records', [])] or ['no data']",
        "            results['summary'] = embed_and_summarize(texts[:5])",
        "        except Exception as e:",
        "            log.warning('OpenAI unavailable: %s', e)",
        "",
        "        # Stubs execute as no-ops until you wire real endpoints",
        "        try:",
        "            for name in " + repr([n for n in selected if n in STUB_DOCS]) + ":",
        "                cfg = globals()[f'{name.lower()}_configure']()",
        "                out = globals()[f'{name.lower()}_run']({'hello': 'world'})",
        "                results[name] = {'cfg': cfg, 'out': out}",
        "        except Exception as e:",
        "            log.warning('Stub failure: %s', e)",
        "",
        "        return results",
        "    except Exception as e:",
        "        try:",
        "            capture_exception(e)",
        "        except Exception:",
        "            pass",
        "        raise",
        "",
        "if __name__ == '__main__':",
        "    logging.basicConfig(level=logging.INFO)",
        "    print(run_integrations_demo())",
    ]
    return "\n".join(lines) + "\n"

# --------------------------
# Integration engine
# --------------------------
ADAPTERS: Dict[str, Adapter] = {
    "Sentry": SentryAdapter(),
    "Redpanda": RedpandaAdapter(),
    "Snowflake": SnowflakeAdapter(),
    "OpenAI": OpenAIAdapter(),
}

def generate_integration_changes(
    apis_to_use: List[str],
    entrypoint_path: str,
    entrypoint_code: str
) -> IntegrationPlan:
    unknown = [a for a in apis_to_use if a not in SUPPORTED]
    if unknown:
        raise ValueError(f"Unknown software requested: {unknown}")

    repo = RepoSnapshot.from_single_entrypoint(entrypoint_path, entrypoint_code)
    plan = IntegrationPlan()

    # Ensure integrations package and orchestration runner
    pkg_init_path, pkg_init_content = mk_dir_init("integrations")
    plan.changes.append(FileChange(path=pkg_init_path, original=repo.read(pkg_init_path), updated=pkg_init_content))

    # Adapters with real code
    for name in apis_to_use:
        if name in ADAPTERS:
            sub = ADAPTERS[name].plan(repo)
            plan.changes.extend(sub.changes)
            plan.pip_dependencies.extend(sub.pip_dependencies)
            plan.env_placeholders.update(sub.env_placeholders)
            plan.notes.extend(sub.notes)

    # Stubs for the rest
    for name in apis_to_use:
        if name not in ADAPTERS:
            plan.changes.append(stub_module(name, repo, STUB_DOCS[name]))
            plan.pip_dependencies.extend(STUB_PIP.get(name, []))
            plan.env_placeholders.update(STUB_ENV.get(name, {}))

    # Orchestration demo file
    runner_path = "integrations/run_integrations.py"
    runner_code = build_orchestration_file(apis_to_use)
    plan.changes.append(FileChange(path=runner_path, original=repo.read(runner_path), updated=runner_code))

    # Patch entrypoint to import and call orchestration if a run function exists
    ep_original = repo.read(entrypoint_path) or ""
    ep_updated = ensure_imports(ep_original, ["from integrations.run_integrations import run_integrations_demo"])
    ep_updated = insert_into_function(ep_updated, "run_integrated_pipeline", ["_ = run_integrations_demo()"])
    ep_updated = ensure_main_invocation(ep_updated, "run_integrated_pipeline")
    plan.changes.append(FileChange(path=entrypoint_path, original=ep_original, updated=ep_updated))

    # Deduplicate deps
    plan.pip_dependencies = sorted(list({d for d in plan.pip_dependencies if d}))

    return plan

# --------------------------
# Example CLI-ish usage
# --------------------------
if __name__ == "__main__":
    apis = ["Apify", "Redpanda", "Airia", "Snowflake", "ElevenLabs", "Sentry", "OpenAI"]
    entry_path = "app.py"
    entry_code = """
import json
import os
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_integrated_pipeline():
    logging.info("Starting integrated data pipeline...")
    # New logic will be added here
    logging.info("Pipeline executed successfully.")
"""

    plan = generate_integration_changes(apis, entry_path, entry_code)

    print("# requirements.txt")
    print("\n".join(plan.pip_dependencies))
    print("\n# .env.example")
    for k, v in plan.env_placeholders.items():
        print(f"{k}={v}")
    print("\n# Diffs")
    print(plan.to_unified_diff())
    print("\n# Notes")
    for n in plan.notes:
        print("-", n)
