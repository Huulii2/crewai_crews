from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from cyberthreat_article_process.tools.report_processing.chroma_db_tool import store_in_chromadb
from cyberthreat_article_process.tools.report_processing.save_summary_tool import save_summary_as_markdown

from cyberthreat_article_process.schema.models import CyberThreatIntel

@CrewBase
class ReportProcessing():
	"""ReportProcessing crew"""

	agents_config = 'config/agents.yaml'
	tasks_config = 'config/tasks.yaml'

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

	@crew
	def crew(self) -> Crew:
		"""Creates the ReportProcessing crew"""
		# To learn how to add knowledge sources to your crew, check out the documentation:
		# https://docs.crewai.com/concepts/knowledge#what-is-knowledge

		return Crew(
			agents=self.agents, # Automatically created by the @agent decorator
			tasks=self.tasks, # Automatically created by the @task decorator
			process=Process.sequential,
			verbose=True,
			max_rpm=1,
			# process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
		)
