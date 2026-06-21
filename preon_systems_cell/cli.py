from __future__ import annotations

import argparse
import json

from preon_systems_cell.api import create_contract, create_organism, get_organism_detail, list_contracts, submit_signal, validate_genome
from preon_systems_cell.models import CreateContractRequest, CreateOrganismRequest, Genome, IdentityProfile, SubmitSignalRequest
from preon_systems_cell.web import main as run_web_server


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="organism", description="Operate the Preon deterministic organism runtime.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_parser = subparsers.add_parser("create-organism", help="Create a hibernated organism identity.")
    create_parser.add_argument("--name", default="Preon Organism")
    create_parser.add_argument("--purpose", default="Deterministic organism runtime")
    create_parser.add_argument("--goal", action="append", default=[])

    signal_parser = subparsers.add_parser("submit-signal", help="Submit a signal to an organism.")
    signal_parser.add_argument("organism_id")
    signal_parser.add_argument("--type", required=True)
    signal_parser.add_argument("--payload", default="{}")

    inspect_parser = subparsers.add_parser("inspect-organism", help="Inspect organism state.")
    inspect_parser.add_argument("organism_id")

    contract_parser = subparsers.add_parser("create-contract", help="Register a skeletal-layer contract.")
    contract_parser.add_argument("--name", required=True)
    contract_parser.add_argument("--action", action="append", default=[])

    subparsers.add_parser("list-contracts", help="List registered contracts.")

    genome_parser = subparsers.add_parser("validate-genome", help="Validate a genome JSON payload.")
    genome_parser.add_argument("--json", required=True)

    web_parser = subparsers.add_parser("web", help="Run the FastAPI web server.")
    web_parser.add_argument("--host", default="127.0.0.1")
    web_parser.add_argument("--port", type=int, default=8000)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "create-organism":
        organism = create_organism(
            CreateOrganismRequest(identity_profile=IdentityProfile(name=args.name, purpose=args.purpose), goals=args.goal)
        )
        print(json.dumps({"organism": organism.model_dump(mode="json")}, indent=2, sort_keys=True))
        return 0

    if args.command == "submit-signal":
        payload = json.loads(args.payload)
        response = submit_signal(args.organism_id, SubmitSignalRequest(type=args.type, payload=payload))
        if response is None:
            print(json.dumps({"error": "organism not found"}, indent=2, sort_keys=True))
            return 1
        print(json.dumps(response.model_dump(mode="json"), indent=2, sort_keys=True))
        return 0

    if args.command == "inspect-organism":
        detail = get_organism_detail(args.organism_id)
        if detail is None:
            print(json.dumps({"error": "organism not found"}, indent=2, sort_keys=True))
            return 1
        print(json.dumps(detail.model_dump(mode="json"), indent=2, sort_keys=True))
        return 0

    if args.command == "create-contract":
        contract = create_contract(CreateContractRequest(name=args.name, allowed_actions=args.action))
        print(json.dumps({"contract": contract.model_dump(mode="json")}, indent=2, sort_keys=True))
        return 0

    if args.command == "list-contracts":
        print(json.dumps({"contracts": [contract.model_dump(mode="json") for contract in list_contracts()]}, indent=2, sort_keys=True))
        return 0

    if args.command == "validate-genome":
        response = validate_genome(Genome.model_validate(json.loads(args.json)))
        print(json.dumps(response.model_dump(mode="json"), indent=2, sort_keys=True))
        return 0 if response.report.valid else 1

    if args.command == "web":
        run_web_server(host=args.host, port=args.port)
        return 0

    return 2
