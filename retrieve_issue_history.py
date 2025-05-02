import json
import csv
from datetime import datetime
from jira import JIRA
from pathlib import Path

# Configuration
FILTER_ID = "23459"  # Replace with your filter ID
CONFIG_FILE = "jira_config.json"
STATUS_OUTPUT_FILE = f"jira_statushistory_{FILTER_ID}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
ESTIMATE_OUTPUT_FILE = f"jira_estimate_history_{FILTER_ID}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

def load_config():
    """Load Jira configuration from JSON file."""
    config_path = Path(__file__).parent / CONFIG_FILE
    if not config_path.exists():
        raise FileNotFoundError(f"{CONFIG_FILE} missing")

    with open(config_path) as f:
        return json.load(f)


def connect_to_jira(config):
    """Initialize Jira connection."""
    return JIRA(server=config["jira_server"], basic_auth=(config["jira_email"], config["jira_api_key"]))


def get_issue_history(issue):
    """Retrieve status change history for a single issue."""
    status_histories = []
    estimate_histories = []
    changelog = issue.changelog

    for history in changelog.histories:
        for item in history.items:
            if item.field == "status":
                status_histories.append(
                    {
                        "issue_key": issue.key,
                        "summary": issue.fields.summary,
                        "from_status": item.fromString,
                        "to_status": item.toString,
                        "changed_by": history.author.displayName,
                        "changed_at": history.created,
                    }
                )

            if item.field == "timeoriginalestimate":
                estimate_histories.append(
                    {
                        "issue_key": issue.key,
                        "summary": issue.fields.summary,
                        "from_timeestimate": item.fromString,
                        "to_timeestimate": item.toString,
                        "changed_by": history.author.displayName,
                        "changed_at": history.created,
                    }
                )

    return status_histories, estimate_histories


def main():
    try:
        # Load configuration and connect to Jira
        config = load_config()
        jira = connect_to_jira(config)

        # Get issues from filter
        issues = jira.search_issues(f"filter={FILTER_ID}", maxResults=False, expand="changelog")
        print(f"Found {len(issues)} issues in filter {FILTER_ID}")

        # Collect all status changes
        all_status_histories = []
        all_estimate_histories = []
        for issue in issues:
            print(f"Processing {issue.key}...")
            status_histories, estimate_histories = get_issue_history(issue)
            all_status_histories.extend(status_histories)
            all_estimate_histories.extend(estimate_histories)

        # Write to CSV
        if all_status_histories:
            fieldnames = [
                "issue_key",
                "summary",
                "from_status",
                "to_status",
                "changed_by",
                "changed_at",
            ]

            with open(STATUS_OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(all_status_histories)

        print(f"Successfully exported {len(all_status_histories)} status changes to {STATUS_OUTPUT_FILE}")

        if all_estimate_histories:
            fieldnames = [
                "issue_key",
                "summary",
                "from_timeestimate",
                "to_timeestimate",
                "changed_by",
                "changed_at",
            ]

            with open(ESTIMATE_OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(all_estimate_histories)

        else:
            print("No status changes found in the filtered issues")

    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
