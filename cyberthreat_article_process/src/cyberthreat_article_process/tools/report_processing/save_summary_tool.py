import datetime
import os
from crewai.tools import tool

@tool
def save_summary_as_markdown(threats_data: dict) -> str:
    """
    Generates a Markdown summary of KnownThreats & EmergingThreats and saves it as a file.

    Returns:
        str: Confirmation message with the saved file path.
    """

    # Ensure threats_data is a dictionary
    if not isinstance(threats_data, dict):
        return "❌ Error: Expected a dictionary as input."

    # Extract threats safely
    known_threats = threats_data.get("known_threats", [])
    emerging_threats = threats_data.get("emerging_threats", [])

    if not known_threats and not emerging_threats:
        return "❌ Error: Missing 'known_threats' and 'emerging_threats' fields."

    # Generate a formatted timestamp with hour, min, sec
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # Create Markdown content
    markdown_content = f"# 🛡️ Cybersecurity Threat Summary ({timestamp})\n\n"

    if known_threats:
        markdown_content += "## 🔥 Known Threats\n"
        for threat in known_threats[:3]:  # Limit to top 3 threats
            markdown_content += f"- **{threat.get('name', 'Unknown Threat')}** ({threat.get('threat_type', 'N/A')}): {threat.get('description', 'No description available')}\n"

    if emerging_threats:
        markdown_content += "\n## 🚨 Emerging Threats\n"
        for threat in emerging_threats[:3]:  # Limit to top 3 threats
            markdown_content += f"- **{threat.get('threat_type', 'N/A')}**: {threat.get('description', 'No description available')}\n"

    markdown_content += f"\n*Generated on {timestamp}*"

    # Define the filename and directory
    directory = "output"
    filename = os.path.join(directory, f"{timestamp}.md")

    # Ensure directory exists
    os.makedirs(directory, exist_ok=True)

    # Write the Markdown content to the file
    try:
        with open(filename, "a", encoding="utf-8") as file:
            file.write(markdown_content)
            file.write("\n\n")

        return f"✅ Summary saved: {filename}"

    except Exception as e:
        return f"❌ Error writing file: {str(e)}"
