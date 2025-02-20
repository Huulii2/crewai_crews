#!/usr/bin/env python
import sys
import warnings

from datetime import datetime

from report_crew.crew import ReportCrew
import os
from dotenv import load_dotenv

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

load_dotenv()
NEWSDATA_API_KEY = os.getenv("NEWSDATA_API_KEY")

def run():
    """
    Run the crew.
    """
    inputs = {
        # 'report_source': f'https://newsdata.io/api/1/news?apikey={NEWSDATA_API_KEY}&category=technology&language=en&q=cybersecurity',
        'report_source': 'https://www.darkreading.com/cloud-security/citrix-patches-zero-day-recording-manager-bugs',
        # 'report_source': r'C:\melo\cyex\web_scraper\report_crew\input\darkreading_com_cloud_security_citrix_patches_zero_day_recording_manager_bugs.pdf',
    }
    
    try:
        ReportCrew().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        "topic": "AI LLMs"
    }
    try:
        ReportCrew().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        ReportCrew().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        "topic": "AI LLMs"
    }
    try:
        ReportCrew().crew().test(n_iterations=int(sys.argv[1]), openai_model_name=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")
