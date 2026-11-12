"""PowerShell: python -m backend.tools.manage --help"""

import argparse
from getpass import getpass
import json
from pathlib import Path

from backend.app.api import create_app
from backend.app.api_models import Role
from backend.app.provisioning import provision_user, register_reviewed_policy
from backend.app.models import Policy


def main():
    parser = argparse.ArgumentParser(description="Offline local account/policy provisioning; no credentials on command line.")
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create-user")
    create.add_argument("--tenant", required=True)
    create.add_argument("--username", required=True)
    create.add_argument("--role", choices=[r.value for r in Role], required=True)
    sub.add_parser("init-demo", help="Prompt for independent passwords for four roles in each of two fictional tenants")
    users = sub.add_parser("list-users")
    users.add_argument("--tenant", required=True)
    policy = sub.add_parser("register-policy", help="Offline reviewed version registration; never automatically activates")
    policy.add_argument("--file", required=True)
    policy.add_argument("--author", required=True)
    policy.add_argument("--reviewer", required=True)
    policy.add_argument("--review-reference", required=True)
    args = parser.parse_args()
    app = create_app()
    service = app.state.service
    repository = service.repository
    try:
        if args.command in {"create-user", "init-demo"}:
            accounts = [(args.tenant, args.username, args.role)] if args.command == "create-user" else [
                (tenant, role.value.lower(), role.value) for tenant in ("demo-a", "demo-b") for role in Role]
            for tenant, username, role in accounts:
                with repository.transaction() as tx:
                    exists = tx.get("users", tenant_id=tenant, username=username)
                if exists:
                    print(json.dumps({"tenant": tenant, "username": username, "status": "exists; unchanged"}))
                    continue
                print(f"Creating {tenant}/{username} ({role}); use an independent password of at least 12 characters.")
                password = getpass("Password (hidden): ")
                if password != getpass("Repeat password (hidden): "):
                    raise ValueError("Passwords did not match; no account was created for this entry.")
                print(json.dumps(provision_user(repository, tenant, username, role, password)))
        elif args.command == "list-users":
            with repository.transaction() as tx:
                print(json.dumps([{k: u[k] for k in ("id", "username", "role", "active")} for u in tx.find("users", tenant_id=args.tenant)], indent=2))
        else:
            candidate = Policy.model_validate_json(Path(args.file).read_text(encoding="utf-8"))
            author = service.login(candidate.tenant_id, args.author, getpass("Author password (hidden): "))["access_token"]
            reviewer = None
            try:
                reviewer = service.login(candidate.tenant_id, args.reviewer, getpass("Independent reviewer password (hidden): "))["access_token"]
                print(json.dumps(register_reviewed_policy(service, author, reviewer, candidate, args.review_reference)))
            finally:
                service.logout(author)
                if reviewer:
                    service.logout(reviewer)
    except Exception as exc:
        # Do not print untrusted validation inputs or credentials.
        print("Operator action failed. Check configuration, account role, independent review and input schema.")
        raise SystemExit(1) from None
    finally:
        repository.close()


if __name__ == "__main__":
    main()
