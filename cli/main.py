import argparse
import json
import signal
import sys


def handle_sigint(sig, frame):
    print("\nSimulation paused and saved.")
    # Dump recovery state
    state = {"status": "paused", "message": "Interrupted by user"}
    with open("recovery_state.json", "w") as f:
        json.dump(state, f)
    sys.exit(0)


def main():
    # Register SIGINT handler
    signal.signal(signal.SIGINT, handle_sigint)

    parser = argparse.ArgumentParser(
        description="OURE CLI - Orbital Uncertainty & Risk Engine"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # 'propagate' subcommand
    parser_prop = subparsers.add_parser("propagate", help="Propagate an orbit")
    parser_prop.add_argument(
        "--input-file", type=str, required=True, help="Path to input file"
    )
    parser_prop.add_argument(
        "--days", type=int, required=True, help="Number of days to propagate"
    )
    parser_prop.add_argument(
        "--step-size", type=float, required=True, help="Step size in seconds"
    )

    # 'risk-check' subcommand
    parser_risk = subparsers.add_parser(
        "risk-check", help="Perform risk conjunction check"
    )
    parser_risk.add_argument(
        "--target-id", type=str, required=True, help="Target satellite ID"
    )
    parser_risk.add_argument(
        "--threshold", type=float, required=True, help="Distance threshold"
    )
    parser_risk.add_argument(
        "--output-json", type=str, required=True, help="Output JSON file path"
    )

    args = parser.parse_args()

    if args.command == "propagate":
        print(
            f"Propagating {args.input_file} for {args.days} days with step size {args.step_size}"
        )
    elif args.command == "risk-check":
        print(
            f"Risk check for {args.target_id} with threshold {args.threshold} to {args.output_json}"
        )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
