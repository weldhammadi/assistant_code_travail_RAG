from pathlib import Path

import config


def test_base_dir_points_to_repo_root():
	assert isinstance(config.BASE_DIR, Path)
	assert (config.BASE_DIR / "config.py").exists()


def test_moderator_system_prompt_path_exists():
	assert config.MODERATOR_SYSTEM_PROMPT_PATH.exists()


def test_model_constants_are_non_empty_strings():
	assert isinstance(config.EMBEDDING_MODEL, str) and config.EMBEDDING_MODEL
	assert isinstance(config.LLM_MODEL, str) and config.LLM_MODEL
	assert isinstance(config.MODERATOR_MODEL, str) and config.MODERATOR_MODEL
