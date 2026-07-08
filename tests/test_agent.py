from src.agent import Agent


def test_read_file_returns_file_content(tmp_path):
	file_path = tmp_path / "sample.txt"
	file_path.write_text("hello world")

	assert Agent.read_file(file_path) == "hello world"


def test_agent_creates_a_groq_client():
	agent = Agent()

	assert agent.client is not None
