from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

# If you want to run a snippet of code before or after the crew starts, 
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

@CrewBase
class IsReportWorthProcessing():
	"""IsReportWorthProcessing crew"""

	agents_config = 'config/agents.yaml'
	tasks_config = 'config/tasks.yaml'

	@agent
	def evaluator_agent(self) -> Agent:
		return Agent(
			config=self.agents_config['evaluator_agent'],
			verbose=True,
			# llm=llm
		)

	@task
	def evaluation_task(self) -> Task:
		return Task(
			config=self.tasks_config['evaluation_task'],
		)

	@crew
	def crew(self) -> Crew:
		"""Creates the IsReportWorthProcessing crew"""
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
