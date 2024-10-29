from app.agents.llm_node import LLMNode
import json
import requests
from bs4 import BeautifulSoup
from langchain_core.messages import ToolMessage
import concurrent.futures
from app.agents.research_agent.state import get_agent_graph_state
from app.utils.helper_functions import get_content
from app.agents.base_node_output import BaseNodeOutput
import logging
from typing import List, Dict


class WebScraperOutput(BaseNodeOutput):
    results: str


class WebScraperNode(LLMNode):
    name = "WebScraper"

    @staticmethod
    def is_garbled(text):
        # A simple heuristic to detect garbled text: high proportion of non-ASCII characters
        non_ascii_count = sum(1 for char in text if ord(char) > 127)
        return non_ascii_count > len(text) * 0.3

    def scrape_single_url(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")

            texts = soup.stripped_strings
            content = " ".join(texts)

            if self.is_garbled(content):
                content = "error in scraping website, garbled text returned"
            else:
                content = content[:4000]

        except requests.HTTPError as e:
            if e.response.status_code == 403:
                content = f"error in scraping website, 403 Forbidden for url: {url}"
            else:
                content = f"error in scraping website, {str(e)}"

        except requests.RequestException as e:
            content = f"error in scraping website, {str(e)}"

        return {"source": url, "content": content}

    async def ainvoke(self, state):
        selector_output = get_content(
            get_agent_graph_state(state=state, state_key="selector_latest")
        )
        logging.info(f"WebScraper 🌐: Selector output: {selector_output}")
        selected_urls = selector_output["selected_urls"]

        # Use ThreadPoolExecutor for parallel scraping
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(self.scrape_single_url, url) for url in selected_urls
            ]
            results = []
            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())

        output = WebScraperOutput(
            summary=f"🌐 Scraped {len(results)} URLs",
            results=json.dumps(results),
        )

        self.update_state("scraper_response", output, is_pydantic=True)
        logging.info(f"WebScraper 🌐: Scraped {len(results)} URLs: {results}")
        return self.state
