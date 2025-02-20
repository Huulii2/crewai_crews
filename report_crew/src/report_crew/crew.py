from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from report_crew.tools.report_parser import parse_report
from report_crew.tools.chroma_db_tool import store_in_chromadb
from report_crew.tools.save_summary_tool import save_summary_as_markdown
from crewai import LLM
import os
from dotenv import load_dotenv
from crewai import LLM
from report_crew.models import CyberThreatIntel


# load_dotenv()
# OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
# llm = LLM(
#     model="openrouter/google/gemini-exp-1206:free",
#     base_url="https://openrouter.ai/api/v1",
#     api_key=OPENROUTER_API_KEY
# )

@CrewBase
class ReportCrew():
	"""ReportCrew crew"""

	agents_config = 'config/agents.yaml'
	tasks_config = 'config/tasks.yaml'
 
####################
# Agents

	@agent
	def data_ingestion_agent(self) -> Agent:
		return Agent(
			config=self.agents_config['data_ingestion_agent'],
			verbose=True,
			tools=[parse_report],
			max_retry_limit=5,
			# llm=llm
		)

	@agent
	def cybersecurity_analysis_agent(self) -> Agent:
		return Agent(
			config=self.agents_config['cybersecurity_analysis_agent'],
			verbose=True,
			max_retry_limit=5,
			# llm=llm
		)
	@agent
	def database_manager_agent(self) -> Agent:
		return Agent(
			config=self.agents_config['database_manager_agent'],
			verbose=True,
			max_retry_limit=5,
			# llm=llm
		)
  
	@agent
	def summary_generator(self) -> Agent:
		return Agent(
			config=self.agents_config['summary_generator'],
			verbose=True,
			max_retry_limit=5,
			# llm=llm
		)
  
####################
# Tasks

	@task
	def ingest_report_task(self) -> Task:
		return Task(
			config=self.tasks_config['ingest_report_task'],
		)

	@task
	def extract_threats_task(self) -> Task:
		return Task(
			config=self.tasks_config['extract_threats_task'],
			output_pydantic=CyberThreatIntel
		)
	@task
	def store_threats_task(self) -> Task:
		return Task(
			config=self.tasks_config['store_threats_task'],
			tools=[store_in_chromadb]
		)

	@task
	def generate_summary_task(self) -> Task:
		return Task(
			config=self.tasks_config['generate_summary_task'],
			tools=[save_summary_as_markdown],
			execute=lambda threats_data: save_summary_as_markdown(threats_data),  # ✅ Pass raw dictionary
			expected_output="A Markdown summary file containing key threats."
		)


####################
# Crew

	@crew
	def crew(self) -> Crew:
		"""Creates the ReportCrew crew"""

		return Crew(
			agents=self.agents, # Automatically created by the @agent decorator
			tasks=self.tasks, # Automatically created by the @task decorator
			process=Process.sequential,
			verbose=True,
			# max_rpm=2,
			# process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
		)
