from __future__ import annotations

import argparse
from pathlib import Path

from econflow.core import (
    PIPELINES,
    create_project,
    create_ticket,
    ensure_workspace,
    find_workspace,
    load_role_specs,
    project_status,
    run_pipeline,
    run_role,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="econflow", description="Tenure-track economics lab workflow")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Initialize workspace")
    init_parser.add_argument("--root", default=".", help="Target directory")

    new_parser = subparsers.add_parser("new-project", help="Create a new project")
    new_parser.add_argument("title", help="Project title")
    new_parser.add_argument("--slug", help="Project slug")
    new_parser.add_argument("--question", default="", help="Research question")
    new_parser.add_argument("--objective", default="", help="PI idea or objective")

    status_parser = subparsers.add_parser("status", help="Show workspace status")
    status_parser.add_argument("--project", help="Project slug")

    run_parser = subparsers.add_parser("run", help="Generate or execute one role packet")
    run_parser.add_argument("--project", required=True, help="Project slug")
    run_parser.add_argument("--role", required=True, help="Role id")
    run_parser.add_argument("--task", default="", help="Override task")
    run_parser.add_argument("--context", action="append", default=[], help="Extra project-relative file")
    run_parser.add_argument("--execute", action="store_true", help="Call the configured model")

    pipeline_parser = subparsers.add_parser("pipeline", help="Run a preset pipeline")
    pipeline_parser.add_argument("--project", required=True, help="Project slug")
    pipeline_parser.add_argument("--preset", default="faculty-lab", choices=tuple(PIPELINES.keys()))
    pipeline_parser.add_argument("--goal", default="", help="Extra PI instruction")
    pipeline_parser.add_argument("--execute", action="store_true", help="Call the configured model")

    delegate_parser = subparsers.add_parser("delegate", help="Create a task ticket for a PhD or master's RA")
    delegate_parser.add_argument("--project", required=True, help="Project slug")
    delegate_parser.add_argument("--role", required=True, help="Role id")
    delegate_parser.add_argument("--title", required=True, help="Ticket title")
    delegate_parser.add_argument("--description", required=True, help="Task background")
    delegate_parser.add_argument("--assigned-by", default="PI", help="Who assigns the task")
    delegate_parser.add_argument("--inputs", default="", help="Expected inputs")
    delegate_parser.add_argument("--acceptance", default="", help="Acceptance criteria")

    webui_parser = subparsers.add_parser("webui", help="Launch the local WebUI dashboard")
    webui_parser.add_argument("--host", default="127.0.0.1", help="Bind host")
    webui_parser.add_argument("--port", type=int, default=5010, help="Bind port")
    webui_parser.add_argument("--debug", action="store_true", help="Enable Flask debug mode")

    return parser


def print_status(snapshot: dict[str, object]) -> None:
    print(f"Workspace: {snapshot['root']}")
    for project in snapshot["projects"]:
        completed = [role for role, ready in project["deliverables"].items() if ready]
        pending = [role for role, ready in project["deliverables"].items() if not ready]
        print(f"\n[{project['slug']}]")
        print(f"Path: {project['path']}")
        print(f"Open tickets: {project['open_tickets']}")
        if project["latest_run"]:
            print(f"Latest run: {project['latest_run']}")
        print(f"Completed deliverables: {', '.join(completed) if completed else 'none'}")
        print(f"Pending deliverables: {', '.join(pending) if pending else 'none'}")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "init":
        root = Path(args.root).resolve()
        ensure_workspace(root)
        print(f"Initialized workspace at {root}")
        return

    root = find_workspace()

    if args.command == "new-project":
        project_dir = create_project(root, args.title, slug=args.slug, question=args.question, objective=args.objective)
        print(f"Created project: {project_dir.name}")
        print(f"Path: {project_dir}")
        return

    if args.command == "status":
        print_status(project_status(root, args.project))
        return

    if args.command == "run":
        if args.role not in load_role_specs(root):
            raise SystemExit(f"Unknown role: {args.role}")
        result = run_role(
            root,
            project_slug=args.project,
            role_id=args.role,
            task=args.task,
            extra_context=args.context,
            execute=args.execute,
        )
        print(f"Run directory: {result.run_dir}")
        print(f"Prompt: {result.prompt_path}")
        if args.execute:
            print(f"Response: {result.response_path}")
            print(f"Deliverable: {result.deliverable_path}")
        else:
            print("Generated prompt only.")
        return

    if args.command == "pipeline":
        results = run_pipeline(root, args.project, args.preset, goal=args.goal, execute=args.execute)
        print(f"Pipeline steps: {len(results)}")
        for result in results:
            print(f"- {result.role_id}: {result.prompt_path}")
        if args.execute:
            print("Deliverables updated.")
        else:
            print("Prompts generated only.")
        return

    if args.command == "delegate":
        if args.role not in load_role_specs(root):
            raise SystemExit(f"Unknown role: {args.role}")
        ticket_path = create_ticket(
            root,
            project_slug=args.project,
            role_id=args.role,
            title=args.title,
            description=args.description,
            assigned_by=args.assigned_by,
            inputs=args.inputs,
            acceptance=args.acceptance,
        )
        print(f"Ticket created: {ticket_path}")
        return

    if args.command == "webui":
        from econflow.webui import launch_webui

        launch_webui(root, host=args.host, port=args.port, debug=args.debug)
        return


if __name__ == "__main__":
    main()
