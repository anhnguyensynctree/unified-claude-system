#!/usr/bin/env python3
"""
oms-work — execute pre-cleared OMS tasks with worktree isolation.

Usage:
  oms-work.py <project-slug>              # run first ready task
  oms-work.py <project-slug> --all        # run all ready tasks
  oms-work.py <project-slug> --dry-run    # show plan without executing
  oms-work.py <project-slug> TASK-NNN     # run specific task

Each task gets its own git worktree (branch: oms-work/task-nnn).
Pass → auto-merge to main + remove worktree.
Fail → leave worktree open for review + notify Discord.
Always posts final task status to Discord (CLI or Discord trigger).
"""
from __future__ import annotations
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / '.claude' / 'bin'))
import oms_discord as discord  # noqa: E402  # type: ignore[import]

from oms_work.config import (  # noqa: E402
    CONFIG, TASK_TIMEOUT_S,
)
from oms_work.queue import (  # noqa: E402
    parse_queue, find_ready, find_all_ready, update_status,
    flag_downstream_tasks,
)
from oms_work.worktree import (  # noqa: E402
    create_worktree, commit_worktree, remove_worktree, merge_to_main,
)
from oms_work.metrics import (  # noqa: E402
    _is_rate_limited, write_task_metrics, _write_pending_resume,
)
from oms_work.llm import run_claude, run_llm_route, resolve_model  # noqa: E402
from oms_work.prompts import (  # noqa: E402
    _split_artifacts, exec_prompt, test_prompt, impl_prompt,
)
from oms_work.agent import (  # noqa: E402
    _agent_loop, _format_error_feedback, _build_agent_prompt,
    _parse_actions, _extract_and_write_files, _extract_pytest_failures,
)
from oms_work.validate import (  # noqa: E402
    validate_step, log_spec_failure, _parse_scenarios,
    _check_scenario_coverage, _parse_qa_verdicts,
    _run_verify_commands, _run_quality_checks,
    _verify_research_output, _check_artifact_match,
)
from oms_work.browse import _is_ui_task, _run_browse_check  # noqa: E402

def execute_task(task: dict, project_path: Path,
                 channel_id: str, threads_file: Path,
                 queue_path: Path, dry_run: bool, slug: str = '') -> tuple[bool, str]:
    print(f'\n[oms-work] ▶ {task["id"]} — {task["title"]}', flush=True)
    if dry_run:
        print(f'[oms-work]   DRY RUN: {task["spec"]}')
        return True, 'dry-run'

    if not task.get('model_hint'):
        notes = 'CTO-STOP: Model-hint missing — task was not properly elaborated. Re-run elaboration.'
        discord.notify_task(channel_id, threads_file, task['milestone'],
                            task['id'], task['title'], False, notes)
        return False, notes

    # Signal task start in Discord thread
    model, is_external = resolve_model(task)
    mode = 'TDD' if _split_artifacts(task['artifacts'])[0] and task['type'] == 'impl' else task['type']
    discord.notify_task(channel_id, threads_file, task['milestone'],
                        task['id'], task['title'], None,
                        f'{model} ({mode})')

    wt, branch = create_worktree(project_path, task['id'])
    task_cost = 0.0
    # validator_log: (name, passed_first_attempt, passed_final)
    validator_log: list[tuple[str, bool, bool]] = []
    validator_details: dict[str, str] = {}  # name → full reason string
    task_notes = ''
    task_fail_at: str | None = None
    original_hint = task.get('model_hint', '') or ''
    used_model = original_hint  # tracks actual model used (may change on escalation)
    MAX_RETRIES = 2       # retry with same model
    MAX_ESCALATIONS = 1   # retry with stronger model
    try:
        model, is_external = resolve_model(task)
        used_model = model
        print(f'[oms-work]   model: {model} ({"external" if is_external else "subscription"})', flush=True)

        # ── TDD Execution loop (RED → GREEN → verify → browse) ──
        error_feedback = ''
        work_out = ''
        exec_passed = False
        tdd_red_result = ''
        tdd_green_result = ''
        scenario_coverage_str = ''
        total_attempts = MAX_RETRIES + MAX_ESCALATIONS + 1
        test_arts, impl_arts = _split_artifacts(task['artifacts'])
        use_tdd = bool(test_arts) and task['type'] == 'impl'

        # Impl tasks without test files = elaboration failure
        if task['type'] == 'impl' and not test_arts:
            print(f'[oms-work]   WARN: impl task has no test files in Artifacts — running single-shot (lower quality)', flush=True)

        if use_tdd:
            print(f'[oms-work]   TDD mode: {len(test_arts)} test file(s), {len(impl_arts)} impl file(s)', flush=True)
        elif task['type'] == 'research':
            print(f'[oms-work]   research mode', flush=True)
        else:
            print(f'[oms-work]   single-shot mode (no test files)', flush=True)

        final_attempt = 0
        for attempt in range(total_attempts):
            final_attempt = attempt
            if attempt > 0:
                label = f'retry {attempt}' if attempt <= MAX_RETRIES else f'escalation {attempt - MAX_RETRIES}'
                print(f'[oms-work]   attempt {attempt + 1}/{total_attempts} ({label})', flush=True)
                subprocess.run(['git', 'checkout', '.'], cwd=wt, capture_output=True)
                subprocess.run(['git', 'clean', '-fd'], cwd=wt, capture_output=True)

            # Choose model (escalate on later attempts)
            current_model = model
            current_external = is_external
            if attempt > MAX_RETRIES and is_external:
                escalation_chain = ['qwen', 'gpt-oss', 'nemotron']
                for esc in escalation_chain:
                    if esc != model:
                        current_model = esc
                        break
                print(f'[oms-work]   escalated to {current_model}', flush=True)
            used_model = current_model

            def _run_model(prompt: str) -> tuple[str, int]:
                nonlocal task_cost
                summary, code, cost = _agent_loop(
                    task, wt, current_model, current_external, prompt)
                task_cost += cost
                return summary, code

            if use_tdd:
                # ── PHASE 1: RED — generate tests ──
                print(f'[oms-work]   RED: generating tests...', flush=True)
                t_prompt = test_prompt(task, wt)
                if error_feedback:
                    t_prompt += _format_error_feedback(error_feedback, 'test')
                test_out, code = _run_model(t_prompt)
                if code != 0:
                    error_feedback = f'Test generation failed (exit {code})'
                    continue

                # Quality check on test files (relaxed rules)
                tq_ok, tq_issues = _run_quality_checks(wt, test_arts, is_test=True)
                if not tq_ok:
                    error_feedback = f'Test quality issues: {"; ".join(tq_issues)}'
                    continue

                # RED verification: tests SHOULD FAIL without implementation
                if task.get('verify'):
                    v_ok, v_summary = _run_verify_commands(task['verify'], wt)
                    if v_ok:
                        tdd_red_result = 'WARN: tests passed without implementation (may be tautological)'
                        print(f'[oms-work]   RED: {tdd_red_result}', flush=True)
                        # Not a hard fail — some tests (e.g. config existence) may legitimately pass
                    else:
                        tdd_red_result = f'RED OK: tests fail as expected ({v_summary[:80]})'
                        print(f'[oms-work]   RED: tests fail as expected ✓', flush=True)

                # ── PHASE 2: GREEN — generate implementation ──
                print(f'[oms-work]   GREEN: generating implementation...', flush=True)
                i_prompt = impl_prompt(task, wt)
                if error_feedback and 'test' not in error_feedback.lower():
                    i_prompt += _format_error_feedback(error_feedback, 'impl')
                work_out, code = _run_model(i_prompt)
                if code != 0:
                    error_feedback = f'Implementation generation failed (exit {code})'
                    continue

            else:
                # ── Single-shot mode (research, scaffold, no-test tasks) ──
                prompt = exec_prompt(task, wt)
                if error_feedback:
                    prompt += _format_error_feedback(error_feedback, 'all')
                work_out, code = _run_model(prompt)
                if code != 0:
                    if _is_rate_limited('') and slug:
                        _write_pending_resume(slug, channel_id)
                        remove_worktree(project_path, task['id'])
                        return False, 'RATE-LIMITED: auto-resume scheduled'
                    error_feedback = f'LLM execution failed (exit {code})'
                    continue

            # ── Common checks (both TDD and single-shot) ──

            # Hallucination check (skip for research)
            if task['type'] != 'research':
                gs = subprocess.run(['git', 'status', '--porcelain'],
                                    capture_output=True, text=True, cwd=wt)
                if not gs.stdout.strip():
                    error_feedback = 'No files were written to disk. You MUST create all required artifacts.'
                    continue

            # Artifact name enforcement — check expected files were actually written
            if task['type'] != 'research':
                am_ok, am_issues = _check_artifact_match(wt, task['artifacts'], task['type'])
                if not am_ok:
                    error_feedback = f'Missing artifacts: {"; ".join(am_issues)}. You MUST create ALL files listed in Artifacts.'
                    print(f'[oms-work]   artifact match: FAIL — {error_feedback[:120]}', flush=True)
                    continue

            # Quality checks on impl files (strict rules)
            check_arts = impl_arts if use_tdd else task['artifacts']
            q_ok, q_issues = _run_quality_checks(wt, check_arts, is_test=False)
            if not q_ok:
                error_feedback = f'Quality issues: {"; ".join(q_issues)}'
                print(f'[oms-work]   quality: FAIL — {error_feedback[:120]}', flush=True)
                continue

            # Research output verification
            if task['type'] == 'research':
                r_ok, r_issues = _verify_research_output(wt, task['id'])
                if not r_ok:
                    error_feedback = f'Research quality: {"; ".join(r_issues)}'
                    print(f'[oms-work]   research quality: FAIL — {error_feedback[:120]}', flush=True)
                    continue

            # Stage files
            subprocess.run(['git', 'add', '-A'], cwd=wt, capture_output=True)

            # GREEN verification: tests MUST PASS with implementation
            if task.get('verify'):
                v_ok, v_summary = _run_verify_commands(task['verify'], wt)
                print(f'[oms-work]   {"GREEN" if use_tdd else "verify"}: {"PASS" if v_ok else "FAIL"}', flush=True)
                if not v_ok:
                    error_feedback = f'Test failures:\n{v_summary}'
                    tdd_green_result = f'GREEN FAIL: {v_summary[:100]}'
                    continue
                tdd_green_result = 'GREEN OK: all tests pass'

            # Scenario coverage check — gaps feed into QA validation as blocking context
            scenario_coverage_str = ''
            if task.get('scenarios'):
                parsed_scenarios = _parse_scenarios(task['scenarios'])
                if parsed_scenarios:
                    test_paths = [wt / a for a in test_arts if (wt / a).exists()]
                    cov_ok, cov_gaps = _check_scenario_coverage(parsed_scenarios, test_paths)
                    scenario_coverage_str = 'all covered' if cov_ok else f'GAPS: {"; ".join(cov_gaps[:3])}'
                    if not cov_ok:
                        print(f'[oms-work]   scenario coverage gaps (will inform QA): {"; ".join(cov_gaps[:3])}', flush=True)

            # Browse check (UI tasks)
            if _is_ui_task(task):
                b_ok, b_issues = _run_browse_check(task, wt, project_path)
                if not b_ok:
                    error_feedback = f'Visual issues: {"; ".join(b_issues)}'
                    print(f'[oms-work]   browse: FAIL — {error_feedback[:120]}', flush=True)
                    continue

            exec_passed = True
            break

        # Compute retry/escalation counts for metrics
        _retry_count = min(final_attempt, MAX_RETRIES)
        _escalation_count = max(0, final_attempt - MAX_RETRIES)

        if not exec_passed:
            remove_worktree(project_path, task['id'])
            notes = f'CTO-STOP: failed after {total_attempts} attempts — {error_feedback[:200]}'
            task_fail_at = 'execution'
            write_task_metrics(queue_path, project_path, task['id'], task_cost, [],
                               passed=False, slug=slug, title=task['title'],
                               milestone=task['milestone'], task_type=task['type'],
                               fail_at=task_fail_at, notes=notes, validator_details={},
                               model_used=used_model, model_hint=original_hint,
                               retry_count=_retry_count,
                               escalation_count=_escalation_count)
            discord.notify_task(channel_id, threads_file, task['milestone'],
                                task['id'], task['title'], False, notes)
            return False, notes

        summary = work_out[:300].replace('\n', ' ').strip()
        task_notes = summary
        # Track results for validators
        tdd_info = ''
        if use_tdd:
            tdd_info = f'TDD: {tdd_red_result} | {tdd_green_result}'
        last_verify = tdd_green_result if use_tdd else 'PASS'
        last_quality = 'PASS (all checks passed)'
        print(f'[oms-work]   exec: {summary[:120]}', flush=True)
        if tdd_info:
            print(f'[oms-work]   {tdd_info}', flush=True)

        # ── Validation chain ──
        research_retried = False
        for validator in task['validation']:
            passed, reason, val_cost = validate_step(
                validator, task, summary, wt,
                verify_result=last_verify, quality_result=last_quality,
                scenario_coverage=scenario_coverage_str)
            task_cost += val_cost
            first_pass = passed
            print(f'[oms-work]   {"✓" if passed else "✗"} {validator}: {reason[:100]}', flush=True)

            # QA must address every scenario — retry once if lazy approval
            if passed and validator == 'qa' and task.get('scenarios'):
                verdicts_ok, verdicts_reason = _parse_qa_verdicts(reason, len(task['scenarios']))
                if not verdicts_ok:
                    print(f'[oms-work]   QA lazy approval ({verdicts_reason}) — retrying with explicit note', flush=True)
                    retry_note = (f'Your response only addressed {verdicts_reason}. '
                                  f'You MUST evaluate all {len(task["scenarios"])} scenarios individually.')
                    passed, reason, val_cost2 = validate_step(
                        validator, task, summary + f'\n\nNOTE: {retry_note}', wt,
                        verify_result=last_verify, quality_result=last_quality,
                        scenario_coverage=scenario_coverage_str)
                    task_cost += val_cost2

            # QA with scenario coverage gaps — retry with gaps as explicit context
            if passed and validator == 'qa' and scenario_coverage_str.startswith('GAPS:'):
                print(f'[oms-work]   QA passed but scenario coverage has gaps — retrying with gap context', flush=True)
                gap_note = (f'WARNING: The following scenarios are NOT covered by tests: {scenario_coverage_str}. '
                            f'Re-evaluate: does the code actually satisfy these uncovered scenarios? '
                            f'If not, FAIL the task.')
                passed, reason, val_cost2 = validate_step(
                    validator, task, summary + f'\n\nNOTE: {gap_note}', wt,
                    verify_result=last_verify, quality_result=last_quality,
                    scenario_coverage=scenario_coverage_str)
                task_cost += val_cost2
                print(f'[oms-work]   {"✓" if passed else "✗"} QA (gap-aware retry): {reason[:100]}', flush=True)

            if not passed:
                if (validator == 'cro' and task['type'] == 'research'
                        and not research_retried):
                    research_retried = True
                    # Include failure diagnostics in retry prompt
                    print('[oms-work]   research quality insufficient — retrying with qwen (free)', flush=True)
                    retry_prompt = exec_prompt(task, wt)
                    retry_prompt += (
                        f'\n\n## IMPORTANT: Prior Attempt Rejected\n'
                        f'Your previous research output was rejected by the CRO validator.\n'
                        f'Rejection reason: {reason[:300]}\n'
                        f'Address these specific concerns in your revised output.\n'
                    )
                    work_out, code, retry_cost = _agent_loop(task, wt, 'qwen', True, retry_prompt)
                    # If free model also fails, escalate to sonnet
                    if code != 0 or not work_out.strip():
                        print('[oms-work]   qwen retry failed — escalating to sonnet', flush=True)
                        work_out, code, retry_cost = _agent_loop(
                            task, wt, 'claude-sonnet-4-6', False, retry_prompt)
                    task_cost += retry_cost
                    if code == 0:
                        summary = work_out[:300].replace('\n', ' ').strip()
                        passed, reason, val_cost = validate_step(
                            validator, task, summary, wt,
                            verify_result=last_verify, quality_result=last_quality,
                            scenario_coverage=scenario_coverage_str)
                        task_cost += val_cost
                        print(f'[oms-work]   {"✓" if passed else "✗"} {validator} (sonnet retry): {reason[:100]}', flush=True)
                if not passed:
                    validator_log.append((validator, False, False))
                    validator_details[validator] = reason
                    task_fail_at = validator
                    task_notes = f'FAIL ({validator}): {reason[:200]}'
                    log_spec_failure(task, validator, reason)
                    write_task_metrics(queue_path, project_path, task['id'], task_cost, validator_log,
                                       passed=False, slug=slug, title=task['title'],
                                       milestone=task['milestone'], task_type=task['type'],
                                       fail_at=task_fail_at, notes=task_notes,
                                       validator_details=validator_details,
                                       model_used=used_model, model_hint=original_hint,
                                       retry_count=_retry_count,
                                       escalation_count=_escalation_count)
                    stop_type = 'CTO-STOP' if validator == 'cto' else 'FAIL'
                    notes = f'{stop_type} ({validator}): {reason[:200]} | branch: {branch}'
                    discord.notify_task(channel_id, threads_file, task['milestone'],
                                        task['id'], task['title'], False, notes)
                    return False, notes
            validator_log.append((validator, first_pass, passed))
            validator_details[validator] = reason

        # Note: verify commands already ran at the GREEN/verify stage above (line ~229).
        # No code changes between verify and this point (validation is read-only).
        # Redundant re-run removed 2026-04-07 — see audit: Layer 2 gap #4.

        commit_worktree(wt, task['id'], task['title'])
        remove_worktree(project_path, task['id'])

        task_notes = summary
        write_task_metrics(queue_path, project_path, task['id'], task_cost, validator_log,
                           passed=True, slug=slug, title=task['title'],
                           milestone=task['milestone'], task_type=task['type'],
                           fail_at=None, notes=task_notes,
                           validator_details=validator_details,
                           model_used=used_model, model_hint=original_hint,
                           retry_count=_retry_count,
                           escalation_count=_escalation_count)
        _, merge_notes = merge_to_main(project_path, branch, task['id'], task['title'])

        # Post-merge smoke check — re-run test commands on main to catch merge conflicts
        test_cmds = ('pytest', 'vitest', 'jest', 'pnpm test', 'npm test')
        verify_tests = [cmd for cmd in task.get('verify', [])
                        if any(tc in cmd for tc in test_cmds)]
        if verify_tests:
            for cmd in verify_tests:
                vr = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                                    cwd=project_path, timeout=120)
                if vr.returncode != 0:
                    print(f'[oms-work]   POST-MERGE FAIL: `{cmd[:60]}` fails on main', flush=True)
                    task_notes += f' | post-merge-fail: {cmd[:40]}'
                    break
                else:
                    print(f'[oms-work]   post-merge verify OK: `{cmd[:60]}`', flush=True)

        notes = f'{summary[:180]} | {merge_notes} | cost: ${task_cost:.4f}'
        print(f'[oms-work]   cost: ${task_cost:.4f}', flush=True)
        discord.notify_task(channel_id, threads_file, task['milestone'],
                            task['id'], task['title'], True, notes)
        flag_downstream_tasks(queue_path, project_path, task, channel_id)
        return True, notes

    except Exception as e:
        remove_worktree(project_path, task['id'])
        task_fail_at = 'exception'
        task_notes = f'CTO-STOP: exception — {e}'
        write_task_metrics(queue_path, project_path, task['id'], task_cost, validator_log,
                           passed=False, slug=slug, title=task['title'],
                           milestone=task['milestone'], task_type=task['type'],
                           fail_at=task_fail_at, notes=task_notes,
                           validator_details=validator_details,
                           model_used=used_model, model_hint=original_hint,
                           retry_count=0, escalation_count=0)
        notes = task_notes
        discord.notify_task(channel_id, threads_file, task['milestone'],
                            task['id'], task['title'], False, notes)
        return False, notes


# ── Milestone gate ───────────────────────────────────────────────────────────


def detect_e2e(project_path: Path) -> tuple[str, Path] | tuple[None, None]:
    """Return (e2e_cmd, cwd) where cwd is the directory containing playwright.config.ts.
    Searches project root first, then common monorepo sub-packages (apps/*/,  packages/*/).
    Returns (None, None) if playwright is not configured anywhere."""
    candidates: list[Path] = [project_path]
    # Monorepo sub-packages — check apps/* and packages/*
    for subdir in ('apps', 'packages'):
        parent = project_path / subdir
        if parent.is_dir():
            candidates.extend(sorted(parent.iterdir()))

    for cwd in candidates:
        if not cwd.is_dir():
            continue
        if (cwd / 'playwright.config.ts').exists() or (cwd / 'playwright.config.js').exists():
            # Determine package manager from lock file (check cwd then root)
            if (cwd / 'pnpm-lock.yaml').exists() or (project_path / 'pnpm-lock.yaml').exists():
                return 'pnpm exec playwright test', cwd
            if (cwd / 'bun.lockb').exists() or (project_path / 'bun.lockb').exists():
                return 'bunx playwright test', cwd
            return 'npx playwright test', cwd
    return None, None




def _auto_queue_gate_fix(queue_path: Path, done_tasks: list[dict],
                         channel_id: str, threads_file: Path,
                         failures: list[str] | None = None,
                         verify_cmds: list[str] | None = None) -> None:
    """Auto-create a fix task when milestone gate fails.
    Includes actual failure details so the LLM knows exactly what to fix."""
    milestone = done_tasks[0].get('milestone', 'current') if done_tasks else 'current'
    text = queue_path.read_text(errors='replace')
    existing_ids = re.findall(r'TASK-(\d+)', text)
    next_num = max((int(n) for n in existing_ids), default=0) + 1
    fix_id = f'TASK-{next_num:03d}'

    # Build failure context for the spec
    failure_details = ''
    if failures:
        failure_details = ' Failures: ' + ' | '.join(f[:150] for f in failures[:5])

    # Use the actual verify commands that failed
    verify_str = ' | '.join(verify_cmds[:5]) if verify_cmds else 'run all project tests'

    fix_task = (
        f'\n\n## {fix_id} — Fix milestone gate failures\n'
        f'- **Status:** queued\n'
        f'- **Feature:** gate-fix\n'
        f'- **Milestone:** {milestone}\n'
        f'- **Department:** qa\n'
        f'- **Type:** impl\n'
        f'- **Infra-critical:** false\n'
        f'- **Spec:** The system SHALL pass all Verify commands and E2E tests on the main branch. '
        f'Fix the specific failures from the milestone gate.{failure_details}\n'
        f'- **Scenarios:** GIVEN the main branch after milestone merge '
        f'WHEN all Verify commands are run THEN exit code 0 for every command '
        f'| GIVEN the E2E suite WHEN playwright test runs THEN all specs pass\n'
        f'- **Artifacts:** (files identified by test failures) | tests/gate-fix.test.ts\n'
        f'- **Produces:** passing test suite on main\n'
        f'- **Verify:** {verify_str}\n'
        f'- **Context:** none\n'
        f'- **Activated:** qa-engineer\n'
        f'- **Validation:** dev → qa → cto\n'
        f'- **Depends:** none\n'
        f'- **File-count:** 3\n'
        f'- **Model-hint:** qwen-coder\n'
    )
    with open(queue_path, 'a') as f:
        f.write(fix_task)
    print(f'[oms-work] Auto-queued {fix_id} — fix milestone gate failures', flush=True)

    if channel_id:
        milestone_str = milestone if milestone else 'current'
        discord.notify_task(channel_id, threads_file, milestone_str,
                            fix_id, 'Fix milestone gate failures', False, 'queued (auto-created)')


def _queue_e2e_setup_task(project_path: Path, milestone: str) -> None:
    """Append a playwright E2E setup task to cleared-queue.md if not already present."""
    queue_path = project_path / '.claude' / 'cleared-queue.md'
    if not queue_path.exists():
        return
    content = queue_path.read_text()
    if 'TASK-e2e-setup' in content or 'playwright' in content.lower():
        return  # already queued or configured
    task_block = (
        '\n## TASK-e2e-setup — Setup Playwright E2E testing\n'
        '- **Status:** queued\n'
        f'- **Milestone:** {milestone}\n'
        '- **Type:** impl\n'
        '- **Spec:** The project SHALL have a Playwright E2E suite with specs covering all '
        'user-facing flows, each with 5 test categories and page.screenshot() calls.\n'
        '- **Artifacts:** playwright.config.ts | e2e/\n'
        '- **Verify:** pnpm exec playwright test\n'
        '- **Validation:** dev → qa → em\n'
        '- **Model-hint:** sonnet\n'
        '- **Depends:** none\n'
    )
    queue_path.write_text(content + task_block)
    print('[oms-work] Added TASK-e2e-setup to queue', flush=True)


def run_milestone_gate(done_tasks: list[dict], project_path: Path,
                       channel_id: str, threads_file: Path) -> tuple[bool, list[str], list[str]]:
    """Run all Verify commands + full E2E suite on main. Called after --all completes."""
    verify_cmds: list[str] = []
    seen: set[str] = set()
    milestones: set[str] = set()
    for task in done_tasks:
        if task.get('milestone'):
            milestones.add(task['milestone'])
        for cmd in task.get('verify', []):
            if cmd not in seen:
                verify_cmds.append(cmd)
                seen.add(cmd)

    e2e_cmd, e2e_cwd = detect_e2e(project_path)
    # e2e_cwd is the directory containing playwright.config.ts (may be a sub-package like apps/web/)
    # Fall back to project_path if not detected (keeps verify_cmds running correctly)
    e2e_cwd = e2e_cwd or project_path

    # Hard-fail if E2E is not found for a project with UI artifacts.
    # Previously this silently queued a setup task and continued — that masked the M3 gate being
    # a no-op (old detect_e2e_cmd only looked at repo root; playwright.config.ts was in apps/web/).
    if not e2e_cmd:
        ui_tasks = [t for t in done_tasks
                    if any(ext in ' '.join(t.get('artifacts', []))
                           for ext in ('.tsx', '.jsx', '.html', '.css', 'page.', 'route.'))]
        if ui_tasks:
            # HARD FAIL — milestone gate must not pass without E2E on a UI project
            msg = ('⛔ **Milestone gate BLOCKED** — playwright not found.\n'
                   'E2E is required for UI milestones. Check that `playwright.config.ts` exists '
                   'under the project root or a sub-package (apps/*, packages/*).\n'
                   'Fix: ensure playwright is installed and `detect_e2e()` can locate the config.')
            thread_id = discord.get_or_create_thread(channel_id, threads_file,
                                                     next(iter(milestones), 'current'))
            if thread_id:
                discord.post_to_thread(thread_id, msg)
            print('[oms-work] ⛔ BLOCKED — playwright not found; milestone gate cannot pass without E2E',
                  flush=True)
            return False, ['playwright not found — E2E required for UI milestone'], verify_cmds

    if not verify_cmds and not e2e_cmd:
        print('[oms-work] Milestone gate: no verify commands or E2E — skip (non-UI milestone)', flush=True)
        return True, [], []

    milestone = next(iter(milestones)) if len(milestones) == 1 else 'multi-milestone'
    total = len(verify_cmds) + (1 if e2e_cmd else 0)
    print(f'\n[oms-work] ── Milestone gate ({total} check(s) on main) ──', flush=True)
    if e2e_cmd:
        print(f'[oms-work]   E2E cwd: {e2e_cwd}', flush=True)

    failures: list[str] = []

    # 1. Per-task Verify commands (unit tests, lint, type checks)
    for cmd in verify_cmds:
        vr = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                            cwd=project_path, timeout=300)
        ok = vr.returncode == 0
        print(f'[oms-work]   {"✓" if ok else "✗"} verify: {cmd[:70]}', flush=True)
        if not ok:
            tail = (vr.stdout + vr.stderr)[-400:].strip()
            failures.append(f'`{cmd}`: {tail[:200]}')

    # 2. Full E2E suite (if playwright configured)
    e2e_ok = True
    if e2e_cmd:
        # Clear browse per-task screenshots before E2E runs — only Playwright output should remain
        # Use e2e_cwd so we clear the correct qa/screenshots/ (may be apps/web/qa/screenshots/)
        shots_dir = e2e_cwd / 'qa' / 'screenshots'
        if shots_dir.exists():
            for f in shots_dir.glob('*.png'):
                f.unlink(missing_ok=True)
            print(f'[oms-work]   cleared {shots_dir.relative_to(project_path)} (browse task screenshots)', flush=True)

        print(f'[oms-work]   running E2E suite: {e2e_cmd}', flush=True)
        er = subprocess.run(e2e_cmd, shell=True, capture_output=True, text=True,
                            cwd=e2e_cwd, timeout=600)
        e2e_ok = er.returncode == 0
        print(f'[oms-work]   {"✓" if e2e_ok else "✗"} E2E suite', flush=True)
        if not e2e_ok:
            tail = (er.stdout + er.stderr)[-600:].strip()
            failures.append(f'E2E (`{e2e_cmd}`): {tail[:300]}')

    passed = not failures
    icon = '✅' if passed else '⚠️'
    status = ('unit + E2E pass' if e2e_cmd else 'unit checks pass') if passed \
             else f'{len(failures)} check(s) failed on main'
    msg = f'{icon} **Milestone gate** `{milestone}` — {status}'
    if failures:
        msg += '\n' + '\n'.join(f'> {f[:150]}' for f in failures[:3])

    thread_id = discord.get_or_create_thread(channel_id, threads_file, milestone)
    if thread_id:
        discord.post_to_thread(thread_id, msg)
    else:
        discord.post_message(channel_id, msg)

    # Archive + post Playwright screenshots to milestone thread
    if thread_id and e2e_cmd:
        screenshots = _collect_media(e2e_cwd, passed)
        if screenshots:
            # Archive to qa/milestones/[milestone]/ under e2e_cwd (sub-package) as permanent record
            archive_dir = e2e_cwd / 'qa' / 'milestones' / milestone.replace(' ', '-').lower()
            archive_dir.mkdir(parents=True, exist_ok=True)
            for shot in screenshots:
                dest = archive_dir / shot.name
                dest.write_bytes(shot.read_bytes())
            rel = archive_dir.relative_to(project_path)
            print(f'[oms-work]   archived {len(screenshots)} screenshot(s) → {rel}', flush=True)

            # Post all to Discord (batched — no cap)
            label = '🖼 Visual QA' if passed else '⚠️ E2E failure screenshots'
            discord.post_media_batched(thread_id, f'{label} — `{milestone}`', screenshots)

    if not passed:
        print(f'[oms-work] ⚠ Milestone gate FAILED — fix before CEO brief', flush=True)
        for f in failures:
            print(f'[oms-work]   {f[:160]}', flush=True)

    return passed, failures, verify_cmds


def _collect_media(project_path: Path, passed: bool) -> list[Path]:
    """Collect Playwright page.screenshot() output from qa/screenshots/ only.
    Browse per-task screenshots are cleared before E2E runs — only Playwright output remains.
    Falls back to test-results/ on failure."""
    shots_dir = project_path / 'qa' / 'screenshots'
    if shots_dir.exists():
        screenshots = sorted(shots_dir.glob('*.png'), key=lambda p: p.stat().st_mtime)
        if screenshots:
            return screenshots
    # Fallback on failure: playwright test-results artifacts
    if not passed:
        results_dir = project_path / 'test-results'
        if results_dir.exists():
            return sorted(results_dir.glob('**/*.png'), key=lambda p: p.stat().st_mtime)
    return []


# ── Main ──────────────────────────────────────────────────────────────────────



def _cleanup_stale_worktrees(project_path: Path) -> None:
    """Remove worktrees from tasks that are done or cto-stop (stale branches left on disk)."""
    wt_dir = project_path / '.claude' / 'worktrees'
    if not wt_dir.exists():
        return
    cleaned = 0
    for wt in wt_dir.iterdir():
        if wt.is_dir() and wt.name.startswith('task-'):
            # Check if corresponding task is still in-progress
            # If not, the worktree is stale
            age_hours = (import_time() - wt.stat().st_mtime) / 3600
            if age_hours > 24:  # older than 24h = definitely stale
                subprocess.run(['git', 'worktree', 'remove', '--force', str(wt)],
                               capture_output=True, cwd=project_path)
                cleaned += 1
    if cleaned:
        print(f'[oms-work] Cleaned {cleaned} stale worktree(s)', flush=True)


def import_time() -> float:
    import time
    return time.time()


def main() -> None:
    if len(sys.argv) < 2:
        print('Usage: oms-work.py <project-slug> [--all] [--dry-run] [TASK-NNN]', file=sys.stderr)
        sys.exit(1)

    slug      = sys.argv[1]
    # Default to --all when called without specific task (Discord always runs all ready tasks)
    target_id = next((a for a in sys.argv[2:] if a.startswith('TASK-')), None)
    run_all   = '--all' in sys.argv or (not target_id and '--dry-run' not in sys.argv)
    dry_run   = '--dry-run' in sys.argv

    cfg  = json.loads(CONFIG.read_text())
    proj = cfg.get('projects', {}).get(slug)
    if not proj:
        print(f'[oms-work] Unknown project: {slug}', file=sys.stderr)
        sys.exit(1)

    project_path = Path(proj['path'])
    channel_id   = proj.get('channel_id', '')
    threads_file = project_path / '.claude' / 'oms-work-threads.json'
    queue_path   = project_path / '.claude' / 'cleared-queue.md'

    if not queue_path.exists() and TEMPLATE.exists():
        queue_path.write_text(TEMPLATE.read_text())
        print(f'[oms-work] Created queue at {queue_path}')

    # Clean up stale worktrees from previous failed runs
    _cleanup_stale_worktrees(project_path)

    import threading
    from concurrent.futures import ThreadPoolExecutor, as_completed

    MAX_WORKERS = 3  # parallel tasks — balances speed vs OpenRouter rate limits
    merge_lock = threading.Lock()  # serialize git merge + queue file writes
    results: list[tuple[str, str, bool, dict]] = []

    def _run_one_task(task: dict) -> tuple[str, str, bool, dict]:
        """Execute a single task with timeout. Thread-safe except for merge."""
        with merge_lock:
            update_status(queue_path, task['id'], 'in-progress')
        try:
            # Use threading timeout instead of signal (signal doesn't work in threads)
            timer = threading.Timer(TASK_TIMEOUT_S, lambda: None)
            timer.start()
            passed, notes = execute_task(
                task, project_path, channel_id, threads_file, queue_path, dry_run, slug=slug)
            timer.cancel()
        except Exception as exc:
            passed = False
            notes = f'CTO-STOP: exception — {exc}'
            print(f'[oms-work] ⚠ {task["id"]} exception: {exc}', flush=True)
        final = 'done' if passed else 'cto-stop'
        with merge_lock:
            update_status(queue_path, task['id'], final, notes)
        return task['id'], task['title'], passed, task

    while True:
        tasks    = parse_queue(queue_path)
        done_ids = {t['id'] for t in tasks if t['status'] == 'done'}
        ready    = find_all_ready(tasks)
        blocked  = [t for t in tasks if t['status'] == 'queued' and t not in ready]
        print(f'[oms-work] Queue: {len(ready)} ready, {len(blocked)} blocked, '
              f'{len(done_ids)} done', flush=True)

        if target_id:
            task = find_ready(tasks, target_id)
            ready = [task] if task else []

        if not ready:
            break

        # Run ready tasks in parallel (max MAX_WORKERS at a time)
        if len(ready) == 1:
            # Single task — run directly (no thread overhead)
            r = _run_one_task(ready[0])
            results.append(r)
            if not r[2] and not run_all:  # failed + not --all
                break
        else:
            print(f'[oms-work] Launching {min(len(ready), MAX_WORKERS)} parallel worker(s) for {len(ready)} task(s)', flush=True)
            batch_results: list[tuple[str, str, bool, dict]] = []
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
                futures = {pool.submit(_run_one_task, t): t for t in ready}
                for future in as_completed(futures):
                    r = future.result()
                    batch_results.append(r)
                    results.append(r)
            # Check if any failed with rate limit — stop the whole run
            for _, _, p, tk in batch_results:
                if not p and not run_all:
                    break

        if target_id:
            break  # single task mode — done after one
        if not run_all:
            break

    done_r  = [(i, t) for i, t, p, _  in results if p]
    done_tk = [tk      for _, _, p, tk in results if p]
    stops   = [(i, t)  for i, t, p, _  in results if not p]

    # Milestone gate — run all Verify commands on main after --all completes
    gate_passed = True
    if run_all and done_tk:
        gate_passed, gate_failures, gate_verify_cmds = run_milestone_gate(
            done_tk, project_path, channel_id, threads_file)
        if not gate_passed:
            _auto_queue_gate_fix(queue_path, done_tk, channel_id, threads_file,
                                 gate_failures, gate_verify_cmds)

        # Auto-run feedback extraction at milestone gate
        feedback_script = Path.home() / '.claude' / 'bin' / 'oms-feedback.py'
        if feedback_script.exists():
            try:
                fb = subprocess.run(
                    [sys.executable, str(feedback_script)],
                    capture_output=True, text=True, timeout=30)
                if fb.stdout.strip():
                    print(f'[oms-work] feedback: {fb.stdout.strip()[:200]}', flush=True)
            except Exception:
                pass  # feedback extraction is non-blocking

    lines = ['## OMS Work']
    for i, t in done_r:
        lines.append(f'✓ {i} — {t}')
    for i, t in stops:
        lines.append(f'⚑ {i} — {t} [cto-stop]')
    if not results:
        lines.append('No tasks ran.')
    if run_all and done_tk:
        lines.append(f'\nMilestone gate: {"PASS" if gate_passed else "FAIL — fix before CEO brief"}')
    print('\n'.join(lines))
    sys.exit(0)


if __name__ == '__main__':
    main()
