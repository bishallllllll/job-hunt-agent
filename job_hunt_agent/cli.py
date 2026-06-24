import argparse
import sys
from job_hunt_agent.search import search_jobs

def main():
    parser = argparse.ArgumentParser(description="Job Hunt Agent CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Search subcommand
    search_parser = subparsers.add_parser("search", help="Search jobs and calculate fit scores")
    search_parser.add_argument("-q", "--query", default="", help="Search query")
    search_parser.add_argument("-l", "--location", default="", help="Location filter")
    search_parser.add_argument("--include-scams", action="store_true", help="Include flagged scams in results")

    # If no arguments provided, show help
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    if args.command == "search":
        jobs = search_jobs(args.query, args.location, include_scams=args.include_scams)
        if not jobs:
            print("No jobs found matching the criteria.")
            return

        print(f"\nFound {len(jobs)} jobs:")
        print("-" * 80)
        for job in jobs:
            scam_str = " [SCAM]" if job.get("is_scam") else ""
            print(f"ID: {job.get('job_id')} | {job.get('position')} | {job.get('company')} | {job.get('location')}{scam_str}")
            print(f"Salary: {job.get('salary')} | Source: {job.get('source')} | Fit Score: {job.get('fit_score')}/10")
            print(f"Description: {job.get('description')[:120]}...")
            print("-" * 80)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
