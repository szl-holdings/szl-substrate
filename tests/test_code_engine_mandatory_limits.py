# SPDX-License-Identifier: Apache-2.0
"""Fail-closed tests for the code engine's MANDATORY sandbox rlimits.

Invariant: if any mandatory child rlimit (CPU, AS, CORE, FSIZE, NPROC) cannot be
applied, the code never runs and the sandbox returns its DENY shape with
``execution_attempted=False``. There is no silent "run without limits" path.

Safety of this test module itself:
  * no real process is ever started: ``subprocess.run`` is replaced by
    ``FakeLauncher``, which models CPython's POSIX contract (fork -> preexec_fn in
    the child -> exec) without creating a process, and ``subprocess.Popen`` is
    replaced by a recorder that fails the test if it is ever reached;
  * no real rlimit is ever changed: the ``resource`` module is replaced by the inert
    ``FakeResource``; the one POSIX-only test against the real module only reads;
  * no model endpoint is reachable: ``_model_configured`` is forced False and
    ``_hf_chat`` fails the test if called;
  * the only code strings are inert, hand-written fixtures (``INERT_FIXTURE`` and
    the engine's own deterministic ``_local_code`` template). Nothing is executed.
"""

from __future__ import annotations

import subprocess

import pytest

from szl_substrate import a11oy_code_engine as code_engine

INERT_FIXTURE = "print('inert hand-written fixture')\n"
INF = -1
MANDATORY = ("RLIMIT_CPU", "RLIMIT_AS", "RLIMIT_CORE", "RLIMIT_FSIZE", "RLIMIT_NPROC")
_IDS = {"RLIMIT_CPU": 0, "RLIMIT_FSIZE": 1, "RLIMIT_CORE": 4, "RLIMIT_NPROC": 6, "RLIMIT_AS": 9}
MIB = 1024 * 1024


class FakeResource:
    """Inert stand-in for the POSIX ``resource`` module. Never touches real limits."""

    RLIM_INFINITY = INF

    def __init__(self, *, missing=(), getrlimit_raises=(), setrlimit_raises=(),
                 not_in_effect=(), soft=None, hard=None):
        for name, rid in _IDS.items():
            if name not in missing:
                setattr(self, name, rid)
        self._names = {rid: name for name, rid in _IDS.items()}
        self.limits = {rid: ((soft or {}).get(name, INF), (hard or {}).get(name, INF))
                       for name, rid in _IDS.items()}
        self.getrlimit_raises = set(getrlimit_raises)
        self.setrlimit_raises = set(setrlimit_raises)
        self.not_in_effect = set(not_in_effect)
        self.set_calls = []

    def getrlimit(self, rid):
        name = self._names[rid]
        if name in self.getrlimit_raises:
            raise OSError(22, "simulated getrlimit failure for %s" % name)
        return self.limits[rid]

    def setrlimit(self, rid, limits):
        name = self._names[rid]
        self.set_calls.append((name, tuple(limits)))
        if name in self.setrlimit_raises:
            raise ValueError("simulated setrlimit failure for %s" % name)
        if name in self.not_in_effect:
            return  # reports success but the limit does not take effect
        self.limits[rid] = tuple(limits)

    def applied(self):
        """Names whose setrlimit call actually took effect, in call order."""
        return [n for n, _ in self.set_calls
                if n not in self.setrlimit_raises and n not in self.not_in_effect]


class FakeLauncher:
    """Models CPython's POSIX ``subprocess.run`` contract without creating a process.

    ``calls`` records each fork; ``preexec_fn`` then runs "in the child". If it
    raises, CPython reports ``SubprocessError('Exception occurred in preexec_fn.')``
    and the program is never exec'd. ``execs`` records only the programs that would
    actually have started running."""

    def __init__(self):
        self.calls = []
        self.execs = []
        self.popen_calls = []

    def run(self, args, **kwargs):
        self.calls.append({"args": list(args), **kwargs})
        hook = kwargs.get("preexec_fn")
        if hook is not None:
            try:
                hook()
            except Exception as exc:
                raise subprocess.SubprocessError("Exception occurred in preexec_fn.") from exc
        self.execs.append(list(args))
        return subprocess.CompletedProcess(args, 0, stdout="inert fixture output\n", stderr="")

    def popen(self, *args, **kwargs):
        self.popen_calls.append((args, kwargs))
        raise AssertionError("subprocess.Popen must never be reached in these tests")


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    """No test in this module may reach a model endpoint."""
    monkeypatch.setattr(code_engine, "_model_configured", lambda: False)

    def _no_model(*_a, **_k):
        raise AssertionError("model endpoint must not be called in tests")

    monkeypatch.setattr(code_engine, "_hf_chat", _no_model)


@pytest.fixture(autouse=True)
def launcher(monkeypatch):
    """No test in this module may start a real process."""
    fake = FakeLauncher()
    monkeypatch.setattr(code_engine.subprocess, "run", fake.run)
    monkeypatch.setattr(code_engine.subprocess, "Popen", fake.popen)
    yield fake
    assert fake.popen_calls == []


def _install(monkeypatch, res, *, posix=True):
    monkeypatch.setattr(code_engine, "_IS_POSIX", posix)
    monkeypatch.setattr(code_engine, "_resource", res)
    return res


def _assert_denied(result):
    assert result["ok"] is False
    assert result["execution_attempted"] is False
    assert result["exit"] == -1
    assert result["stdout"] == ""
    assert result["error"].startswith("sandbox unavailable:")
    assert "fail closed" in result["isolation"]


def _signing_sink():
    signed = {}

    def sign(payload):
        signed.update(payload)
        return {"signed": True, "signatures": ["test-signature"]}

    return signed, sign


# --------------------------------------------------------------------------
# Parent-side preflight: the subprocess launcher is never called.
# --------------------------------------------------------------------------
def test_resource_module_missing_denies_before_launch(monkeypatch, launcher):
    _install(monkeypatch, None)

    result = code_engine._sandbox_exec(INERT_FIXTURE)

    _assert_denied(result)
    assert result["error"] == "sandbox unavailable: POSIX resource limits are required"
    assert launcher.calls == []


def test_non_posix_platform_denies_before_launch(monkeypatch, launcher):
    res = _install(monkeypatch, FakeResource(), posix=False)

    result = code_engine._sandbox_exec(INERT_FIXTURE)

    _assert_denied(result)
    assert result["error"] == "sandbox unavailable: POSIX resource limits are required"
    assert launcher.calls == []
    assert res.set_calls == []


@pytest.mark.parametrize("name", MANDATORY)
def test_unsupported_mandatory_rlimit_denies_before_launch(monkeypatch, launcher, name):
    res = _install(monkeypatch, FakeResource(missing=(name,)))

    result = code_engine._sandbox_exec(INERT_FIXTURE)

    _assert_denied(result)
    assert result["error"] == (
        "sandbox unavailable: mandatory rlimit %s is not supported on this platform" % name)
    assert launcher.calls == []
    assert res.set_calls == []


@pytest.mark.parametrize("name", MANDATORY)
def test_unreadable_mandatory_rlimit_denies_before_launch(monkeypatch, launcher, name):
    res = _install(monkeypatch, FakeResource(getrlimit_raises=(name,)))

    result = code_engine._sandbox_exec(INERT_FIXTURE)

    _assert_denied(result)
    assert result["error"] == (
        "sandbox unavailable: mandatory rlimit %s cannot be read (OSError)" % name)
    assert launcher.calls == []
    assert res.set_calls == []


@pytest.mark.parametrize("fn", ["getrlimit", "setrlimit"])
def test_missing_rlimit_function_denies_before_launch(monkeypatch, launcher, fn):
    res = FakeResource()
    setattr(res, fn, None)
    _install(monkeypatch, res)

    result = code_engine._sandbox_exec(INERT_FIXTURE)

    _assert_denied(result)
    assert "resource.%s is unavailable" % fn in result["error"]
    assert launcher.calls == []


def test_missing_rlim_infinity_denies_before_launch(monkeypatch, launcher):
    res = FakeResource()
    res.RLIM_INFINITY = None
    _install(monkeypatch, res)

    result = code_engine._sandbox_exec(INERT_FIXTURE)

    _assert_denied(result)
    assert "RLIM_INFINITY is unavailable" in result["error"]
    assert launcher.calls == []


# --------------------------------------------------------------------------
# Child-side hook: a setrlimit failure aborts the child before exec.
# --------------------------------------------------------------------------
@pytest.mark.parametrize("name", MANDATORY)
def test_setrlimit_raising_never_reaches_exec(monkeypatch, launcher, name):
    res = _install(monkeypatch, FakeResource(setrlimit_raises=(name,)))

    result = code_engine._sandbox_exec(INERT_FIXTURE)

    _assert_denied(result)
    assert result["error"] == code_engine._LIMIT_HOOK_FAILED_ERROR
    # The fork is modelled honestly (one launcher call), but exec never happens.
    assert len(launcher.calls) == 1
    assert launcher.execs == []
    assert res.set_calls[-1][0] == name  # the failing limit was the last one attempted


def test_partial_application_failure_never_reaches_exec(monkeypatch, launcher):
    """CPU, AS and CORE apply, then FSIZE fails: NPROC is never attempted and the
    program never runs with the partial set."""
    res = _install(monkeypatch, FakeResource(setrlimit_raises=("RLIMIT_FSIZE",)))

    result = code_engine._sandbox_exec(INERT_FIXTURE)

    _assert_denied(result)
    assert res.applied() == ["RLIMIT_CPU", "RLIMIT_AS", "RLIMIT_CORE"]
    assert [n for n, _ in res.set_calls] == [
        "RLIMIT_CPU", "RLIMIT_AS", "RLIMIT_CORE", "RLIMIT_FSIZE"]
    assert launcher.execs == []


def test_nproc_failure_is_no_longer_swallowed(monkeypatch, launcher):
    """Regression: RLIMIT_NPROC used to sit in its own swallow-all try/except, so a
    failure there still ran the code with no process limit."""
    res = _install(monkeypatch, FakeResource(setrlimit_raises=("RLIMIT_NPROC",)))

    result = code_engine._sandbox_exec(INERT_FIXTURE)

    _assert_denied(result)
    assert res.applied() == ["RLIMIT_CPU", "RLIMIT_AS", "RLIMIT_CORE", "RLIMIT_FSIZE"]
    assert launcher.execs == []


@pytest.mark.parametrize("name", MANDATORY)
def test_limit_not_in_effect_after_setrlimit_never_reaches_exec(monkeypatch, launcher, name):
    """setrlimit reports success but the read-back shows the limit is not in force."""
    _install(monkeypatch, FakeResource(not_in_effect=(name,)))

    result = code_engine._sandbox_exec(INERT_FIXTURE)

    _assert_denied(result)
    assert result["error"] == code_engine._LIMIT_HOOK_FAILED_ERROR
    assert launcher.execs == []


def test_hook_raises_instead_of_swallowing():
    plan = [(n, _IDS[n], (0, 0)) for n in MANDATORY]

    raising = FakeResource(setrlimit_raises=("RLIMIT_AS",))
    with pytest.raises(ValueError, match="RLIMIT_AS"):
        code_engine._apply_mandatory_rlimits(raising, plan)
    assert raising.applied() == ["RLIMIT_CPU"]

    silent = FakeResource(not_in_effect=("RLIMIT_CORE",))
    with pytest.raises(OSError, match="RLIMIT_CORE is not in effect"):
        code_engine._apply_mandatory_rlimits(silent, plan)


# --------------------------------------------------------------------------
# Success path: every limit applies, then (and only then) the program runs.
# --------------------------------------------------------------------------
def test_all_mandatory_limits_applied_then_launches(monkeypatch, launcher):
    res = _install(monkeypatch, FakeResource())

    result = code_engine._sandbox_exec(INERT_FIXTURE, timeout_s=6, mem_mb=256)

    assert result["ok"] is True
    assert result["execution_attempted"] is True
    assert result["exit"] == 0
    assert result["stdout"] == "inert fixture output\n"
    assert res.set_calls == [
        ("RLIMIT_CPU", (6, 6)),
        ("RLIMIT_AS", (256 * MIB, 256 * MIB)),
        ("RLIMIT_CORE", (0, 0)),
        ("RLIMIT_FSIZE", (0, 0)),
        ("RLIMIT_NPROC", (0, 0)),
    ]
    assert len(launcher.calls) == 1 and len(launcher.execs) == 1
    call = launcher.calls[0]
    assert call["preexec_fn"] is not None
    assert call["args"][1:3] == ["-I", "-S"]
    assert set(call["env"]) == {"PATH", "PYTHONDONTWRITEBYTECODE", "HOME", "no_proxy",
                                "PYTHONUNBUFFERED"}


def test_inherited_limits_are_never_loosened(monkeypatch, launcher):
    """A server already running under tighter limits keeps them in the child: the
    plan takes the stricter value, so setrlimit is always a permitted lowering."""
    res = _install(monkeypatch, FakeResource(
        soft={"RLIMIT_CPU": 1}, hard={"RLIMIT_CPU": 2, "RLIMIT_AS": 128 * MIB}))

    result = code_engine._sandbox_exec(INERT_FIXTURE, timeout_s=6, mem_mb=256)

    assert result["execution_attempted"] is True
    assert dict(res.set_calls)["RLIMIT_CPU"] == (1, 1)
    assert dict(res.set_calls)["RLIMIT_AS"] == (128 * MIB, 128 * MIB)
    assert len(launcher.execs) == 1


@pytest.mark.parametrize("inf", [-1, 2**63 - 1], ids=["negative-infinity", "positive-infinity"])
@pytest.mark.parametrize("soft,hard,expected", [
    (1, 10, 1),              # inherited soft must be an unraisable ceiling
    (1, 2, 1),               # the original inherited-limits regression
    (0, 10, 0),              # zero remains a finite limit, not infinity
    (6, 10, 6),              # inherited soft matches the mandate
    (10, 10, 6),             # mandate is stricter than either inherited value
    (1, None, 1),            # finite soft with unlimited hard
    (None, None, 6),         # both unlimited: use the mandate
    (None, 2, 2),            # defensive: still honor a finite inherited hard
    (2**40, 2**41, 6),       # large finite integers remain finite
])
def test_inherited_cpu_soft_is_a_hard_ceiling(monkeypatch, launcher, inf,
                                              soft, hard, expected):
    soft = inf if soft is None else soft
    hard = inf if hard is None else hard
    res = FakeResource(
        soft={name: inf for name in MANDATORY},
        hard={name: inf for name in MANDATORY})
    res.RLIM_INFINITY = inf
    res.limits[_IDS["RLIMIT_CPU"]] = (soft, hard)
    _install(monkeypatch, res)
    inherited = dict(res.limits)

    planned_res, plan, refusal = code_engine._plan_mandatory_rlimits(6, 256)

    assert refusal is None and planned_res is res
    assert res.limits == inherited and res.set_calls == []
    assert launcher.calls == []  # planning cannot launch even the fake child
    assert dict((name, limits) for name, _, limits in plan)["RLIMIT_CPU"] == (
        expected, expected)

    code_engine._apply_mandatory_rlimits(res, plan)

    assert dict(res.set_calls)["RLIMIT_CPU"] == (expected, expected)
    assert res.applied() == list(MANDATORY)
    assert launcher.calls == []


@pytest.mark.parametrize("name", MANDATORY)
def test_each_mandatory_limit_hard_cap_respects_inherited_soft(monkeypatch, name):
    """CPU and AS tighten to inherited soft; zero mandates stay zero."""
    inherited_soft = {"RLIMIT_CPU": 1, "RLIMIT_AS": 128 * MIB,
                      "RLIMIT_CORE": 7, "RLIMIT_FSIZE": 7, "RLIMIT_NPROC": 7}[name]
    mandate = {"RLIMIT_CPU": 6, "RLIMIT_AS": 256 * MIB,
               "RLIMIT_CORE": 0, "RLIMIT_FSIZE": 0, "RLIMIT_NPROC": 0}[name]
    res = _install(monkeypatch, FakeResource(
        soft={name: inherited_soft}, hard={name: inherited_soft * 2}))

    _, plan, refusal = code_engine._plan_mandatory_rlimits(6, 256)

    assert refusal is None and res.set_calls == []
    limits = dict((n, values) for n, _, values in plan)[name]
    expected = min(mandate, inherited_soft)
    assert limits == (expected, expected)


def test_inherited_soft_ceiling_is_applied_before_fake_exec(monkeypatch, launcher):
    res = _install(monkeypatch, FakeResource(
        soft={"RLIMIT_CPU": 1}, hard={"RLIMIT_CPU": 10}))

    result = code_engine._sandbox_exec(INERT_FIXTURE, timeout_s=6)

    assert result["execution_attempted"] is True
    assert len(launcher.execs) == 1
    assert dict(res.set_calls)["RLIMIT_CPU"] == (1, 1)


def test_inherited_soft_ceiling_readback_rejects_raisable_hard(monkeypatch, launcher):
    class LeavesHardRaisable(FakeResource):
        def setrlimit(self, rid, limits):
            super().setrlimit(rid, limits)
            if rid == self.RLIMIT_CPU:
                self.limits[rid] = (limits[0], 6)

    _install(monkeypatch, LeavesHardRaisable(
        soft={"RLIMIT_CPU": 1}, hard={"RLIMIT_CPU": 10}))

    result = code_engine._sandbox_exec(INERT_FIXTURE, timeout_s=6)

    _assert_denied(result)
    assert result["error"] == code_engine._LIMIT_HOOK_FAILED_ERROR
    assert launcher.execs == []


def test_preflight_with_real_resource_module_is_read_only():
    """On a POSIX host the real preflight plans every mandatory limit and changes
    nothing in the test process (it only calls getrlimit)."""
    resource = pytest.importorskip("resource")
    if not code_engine._IS_POSIX:  # pragma: no cover - platform dependent
        pytest.skip("POSIX only")
    names = [n for n in MANDATORY if hasattr(resource, n)]
    before = {n: resource.getrlimit(getattr(resource, n)) for n in names}

    res, plan, refusal = code_engine._plan_mandatory_rlimits(6, 256)

    after = {n: resource.getrlimit(getattr(resource, n)) for n in names}
    assert after == before
    if len(names) == len(MANDATORY):
        assert refusal is None and res is resource
        assert [p[0] for p in plan] == list(MANDATORY)
    else:  # pragma: no cover - a platform without one of the constants must deny
        assert refusal is not None and plan is None


# --------------------------------------------------------------------------
# governed_turn: code execution goes through the same mandatory-limit gate.
# --------------------------------------------------------------------------
def test_governed_turn_partial_platform_support_is_a_signed_deny(monkeypatch, launcher):
    _install(monkeypatch, FakeResource(missing=("RLIMIT_NPROC",)))
    signed, sign = _signing_sink()

    run = code_engine.governed_turn("code", "calculate fibonacci numbers", sign,
                                    "test-issuer", sandbox=True)

    reason = "sandbox unavailable: mandatory rlimit RLIMIT_NPROC is not supported on this platform"
    assert launcher.calls == []
    assert run["decision"] == "DENY"
    assert run["emitted"] is False
    assert run["execution_admission"] == {
        "allowed": False, "attempted": False, "refused": True, "reason": reason}
    assert run["sandbox"]["execution_attempted"] is False
    assert "No code ran" in run["summary"]
    assert signed["decision"] == "DENY"
    assert signed["sandbox_execution_attempted"] is False
    assert signed["sandbox_refused"] is True
    assert signed["sandbox_error"] == reason
    assert run["receipt_chain"][-1]["body"]["sandbox_refused"] is True
    assert code_engine.verify_run(run)["chain_intact"] is True


def test_governed_turn_hook_failure_is_a_signed_deny(monkeypatch, launcher):
    _install(monkeypatch, FakeResource(setrlimit_raises=("RLIMIT_CPU",)))
    signed, sign = _signing_sink()

    run = code_engine.governed_turn("code", "calculate fibonacci numbers", sign,
                                    "test-issuer", sandbox=True)

    assert launcher.execs == []
    assert run["decision"] == "DENY"
    assert run["emitted"] is False
    assert run["execution_admission"]["attempted"] is False
    assert run["execution_admission"]["reason"] == code_engine._LIMIT_HOOK_FAILED_ERROR
    assert "then ran in the governed sandbox" not in run["summary"]
    assert signed["decision"] == "DENY"
    assert signed["sandbox_execution_attempted"] is False
    assert code_engine.verify_run(run)["chain_intact"] is True


def test_governed_turn_runs_only_after_every_limit_applies(monkeypatch, launcher):
    res = _install(monkeypatch, FakeResource())
    signed, sign = _signing_sink()

    run = code_engine.governed_turn("code", "calculate fibonacci numbers", sign,
                                    "test-issuer", sandbox=True)

    assert run["decision"] == "ALLOW"
    assert run["emitted"] is True
    assert res.applied() == list(MANDATORY)
    assert len(launcher.execs) == 1
    assert run["sandbox"]["execution_attempted"] is True
    assert signed["sandbox_execution_attempted"] is True
    assert signed["sandbox_refused"] is False


def test_governed_turn_without_sandbox_never_launches(monkeypatch, launcher):
    _install(monkeypatch, FakeResource())
    _, sign = _signing_sink()

    run = code_engine.governed_turn("code", "calculate fibonacci numbers", sign,
                                    "test-issuer", sandbox=False)

    assert launcher.calls == []
    assert run["sandbox"] is None
