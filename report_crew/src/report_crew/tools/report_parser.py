from crewai.tools import tool
import requests
import pdfplumber
from bs4 import BeautifulSoup
import json

@tool
def parse_report(report_source: str, source_type: str) -> str:
    """
    Extracts text from a cybersecurity report.
    - report_source: URL (for HTML/API) or file path (for PDF)
    - source_type: "pdf", "html", or "api"
    
    Returns: Cleaned text content or structured JSON (for APIs).
    """
    if source_type == "pdf":
        try:
            with pdfplumber.open(report_source) as pdf:
                text = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())
            return text.strip() if text else "No text found in PDF."
        except Exception as e:
            return f"Error reading PDF: {str(e)}"

    elif source_type == "html":
        try:
            response = requests.get(report_source, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Remove unnecessary elements (ads, navigation, footers, etc.)
            for tag in soup(["script", "style", "header", "footer", "nav", "aside"]):
                tag.decompose()

            # Extract readable text content
            text = soup.get_text(separator="\n", strip=True)
            return text if text else "No readable content found on webpage."
        except Exception as e:
            return f"Error scraping webpage: {str(e)}"

    elif source_type == "api":
        try:
            response = requests.get(report_source, timeout=10)
            response.raise_for_status()

            # If the response is JSON, return it in formatted string
            if "application/json" in response.headers.get("Content-Type", ""):
                return json.dumps(response.json(), indent=2)

            return f"API response is not JSON: {response.text[:500]}"
        except Exception as e:
            return f"Error fetching API data: {str(e)}"

    return "Invalid source type. Please specify 'pdf', 'html', or 'api'."

