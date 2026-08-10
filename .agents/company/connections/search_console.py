"""Read-only Google Search Console Connection."""

import os
from urllib.parse import quote
from .base import ConnectionResult, json_request


class SearchConsoleConnection:
    id = "search-console"

    def ready(self):
        return bool(os.getenv("SEARCH_CONSOLE_ACCESS_TOKEN") and os.getenv("SEARCH_CONSOLE_SITE_URL"))

    def query_performance(self, start_date, end_date, dimensions=("query", "page"), *, row_limit=25000,
                          start_row=0, search_type="web", dry_run=True):
        site = os.getenv("SEARCH_CONSOLE_SITE_URL", "sc-domain:spielos.xyz")
        endpoint = f"https://www.googleapis.com/webmasters/v3/sites/{quote(site, safe='')}/searchAnalytics/query"
        body = {"startDate": start_date, "endDate": end_date, "dimensions": list(dimensions),
                "type": search_type, "rowLimit": min(int(row_limit), 25000), "startRow": int(start_row)}
        if dry_run:
            return ConnectionResult(True, self.id, "query_performance", {"dry_run": True, "endpoint": endpoint, "body": body})
        token = os.getenv("SEARCH_CONSOLE_ACCESS_TOKEN")
        if not self.ready():
            return ConnectionResult(False, self.id, "query_performance", error="Set SEARCH_CONSOLE_ACCESS_TOKEN and SEARCH_CONSOLE_SITE_URL")
        try:
            return ConnectionResult(True, self.id, "query_performance",
                                    json_request(endpoint, token=token, body=body))
        except Exception as error:
            return ConnectionResult(False, self.id, "query_performance", error=str(error))
