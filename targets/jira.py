import base64
from typing import Any
from urllib.parse import quote

import requests
from loguru import logger
from requests.auth import HTTPBasicAuth

from config import settings


class Jira:
    def __init__(self) -> None:
        self.auth = HTTPBasicAuth(settings.jira_email, settings.jira_token)
        self.api_url = f"{settings.jira_api_endpoint}/rest/api/3"

        auth_message = f"{settings.jira_email}:{settings.jira_token}"
        auth_bytes = auth_message.encode("ascii")
        b64_bytes = base64.b64encode(auth_bytes)
        b64_message = b64_bytes.decode("ascii")
        self.auth_value = f"Basic {b64_message}"
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": self.auth_value,
        }

    def create_issue(self, params: dict[str, Any]) -> dict[str, Any]:
        logger.info("Creating Jira issue")

        create_issue_response = requests.request(
            "POST", f"{self.api_url}/issue", json=params, headers=self.headers
        )

        create_issue_response.raise_for_status()

        logger.info("Issue created successfully")
        return create_issue_response.json()

    def search_issue(self, jql_query: str) -> bool:

        logger.info("Searching Jira issue")

        issue_response = requests.request(
            "GET",
            f"{self.api_url}/search?jql={quote(jql_query, safe='')}",
            headers=self.headers,
        )

        issue_response.raise_for_status()
        return issue_response.json()

    def resolve_issue(self, issue_key: str):
        logger.info(f"Setting new status of issue {issue_key}")

        if not settings.jira_resolve_transition_id:
            # Looking for a default resolve transition id
            logger.info("Jira transition id parameter was not inserted,"
                        " getting the default from the Jira project")

            transitions_response = requests.request(
                "GET",
                f"{self.api_url}/issue/{issue_key}/transitions",
                headers=self.headers
            ).json()
            resolved_transition = next((t["id"] for t in transitions_response["transitions"]
                                        if t['to']['name'] == 'Done'), None)
        else:
            resolved_transition = settings.jira_resolve_transition_id

            if not resolved_transition:
                logger.info("Jira transition to done was not found,"
                            " please enter the jira_resolve_transition_id parameter")

        body = {"transition": {"id": resolved_transition}}
        issue_response = requests.request(
            "POST",
            f"{self.api_url}/issue/{issue_key}/transitions",
            headers=self.headers,
            json=body,
        )

        issue_response.raise_for_status()
        return issue_response
