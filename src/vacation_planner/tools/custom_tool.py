"""Google search via serper.dev (replaces crewai_tools.SerperDevTool to keep the image small)."""

import os
from typing import Type

import requests
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class SerperSearchInput(BaseModel):
    search_query: str = Field(..., description="The Google search query to run.")


class SerperSearchTool(BaseTool):
    name: str = "Search the internet"
    description: str = "Searches Google and returns the top results (title, link, snippet)."
    args_schema: Type[BaseModel] = SerperSearchInput

    def _run(self, search_query: str) -> str:
        try:
            resp = requests.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": os.getenv("Serper_API_KEY", "")},
                json={"q": search_query, "num": 5},
                timeout=20,
            )
            resp.raise_for_status()
        except Exception as e:
            return f"Search failed: {e}"
        results = resp.json().get("organic", [])
        return "\n---\n".join(f"{r.get('title')}\n{r.get('link')}\n{r.get('snippet')}" for r in results) or "No results."
