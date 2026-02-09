"""Tests for the Harbor coding agent example.

Run with: uv run --with pytest python -m pytest tests/test_harbor_coding.py -v
"""

from __future__ import annotations

import asyncio

import pytest

from examples.harbor_coding_agent import (
    ACT_PROMPT,
    CODING_TASKS,
    PLAN_PROMPT,
    REASON_PROMPT,
    CodingEnvironment,
    CodingTask,
    CodingWorkspaceState,
    create_coding_workspace,
)


class TestCodingWorkspaceState:
    """Test the workspace state management."""

    def test_file_exists(self):
        state = CodingWorkspaceState(
            files={"/workspace/src/main.py": "print('hello')"},
            directories={"/workspace", "/workspace/src"},
        )
        assert state.file_exists("/workspace/src/main.py")
        assert not state.file_exists("/workspace/src/other.py")

    def test_dir_exists(self):
        state = CodingWorkspaceState(
            directories={"/workspace", "/workspace/src"},
        )
        assert state.dir_exists("/workspace")
        assert state.dir_exists("/workspace/src")
        assert not state.dir_exists("/workspace/tests")

    def test_normalize_path_absolute(self):
        state = CodingWorkspaceState(cwd="/workspace")
        assert state._normalize_path("/etc/config") == "/etc/config"

    def test_normalize_path_relative(self):
        state = CodingWorkspaceState(cwd="/workspace")
        assert state._normalize_path("src/main.py") == "/workspace/src/main.py"

    def test_get_file_content(self):
        state = CodingWorkspaceState(
            files={"/workspace/README.md": "# Hello"},
        )
        assert state.get_file_content("/workspace/README.md") == "# Hello"
        assert state.get_file_content("/workspace/missing.md") is None

    def test_write_file(self):
        state = CodingWorkspaceState(cwd="/workspace", files={})
        state.write_file("new_file.py", "print('test')")
        assert state.files["/workspace/new_file.py"] == "print('test')"

    def test_list_dir(self):
        state = CodingWorkspaceState(
            files={
                "/workspace/README.md": "# Hello",
                "/workspace/src/main.py": "...",
            },
            directories={"/workspace", "/workspace/src"},
        )
        entries = state.list_dir("/workspace")
        assert "README.md" in entries
        assert "src/" in entries


class TestCodingEnvironment:
    """Test the coding environment."""

    def test_reset(self):
        task = CodingTask(
            goal="Test task",
            verify=lambda s: True,
        )
        env = CodingEnvironment(task)
        obs = env.reset("Test task")

        assert "sandboxed Linux environment" in obs
        assert "Test task" in obs

    def test_ls_command(self):
        task = CodingTask(goal="Test", verify=lambda s: False)
        env = CodingEnvironment(task)
        env.reset("Test")

        obs, done, success = env.step("ls")
        assert "src/" in obs
        assert "tests/" in obs
        assert not done

    def test_cd_command(self):
        task = CodingTask(goal="Test", verify=lambda s: False)
        env = CodingEnvironment(task)
        env.reset("Test")

        obs, done, success = env.step("cd src")
        assert "Changed to /workspace/src" in obs
        assert env._state.cwd == "/workspace/src"

    def test_cat_command(self):
        task = CodingTask(goal="Test", verify=lambda s: False)
        env = CodingEnvironment(task)
        env.reset("Test")

        obs, done, success = env.step("cat src/config.py")
        assert "port" in obs.lower()
        assert "8000" in obs

    def test_grep_command(self):
        task = CodingTask(goal="Test", verify=lambda s: False)
        env = CodingEnvironment(task)
        env.reset("Test")

        obs, done, success = env.step("grep port src/config.py")
        assert "port" in obs.lower()

    def test_find_command(self):
        task = CodingTask(goal="Test", verify=lambda s: False)
        env = CodingEnvironment(task)
        env.reset("Test")

        obs, done, success = env.step("find .py")
        assert "main.py" in obs
        assert "config.py" in obs

    def test_sed_command(self):
        task = CodingTask(goal="Test", verify=lambda s: False)
        env = CodingEnvironment(task)
        env.reset("Test")

        # Change port from 8000 to 3000
        obs, done, success = env.step("sed -i 's/8000/3000/g' src/config.py")
        assert "Modified" in obs

        # Verify the change
        content = env._state.get_file_content("/workspace/src/config.py")
        assert "3000" in content
        assert "8000" not in content

    def test_echo_write_command(self):
        task = CodingTask(goal="Test", verify=lambda s: False)
        env = CodingEnvironment(task)
        env.reset("Test")

        obs, done, success = env.step("echo 'test content' > test.txt")
        assert "Wrote to" in obs

        content = env._state.get_file_content("/workspace/test.txt")
        assert content == "test content"

    def test_command_chaining(self):
        task = CodingTask(goal="Test", verify=lambda s: False)
        env = CodingEnvironment(task)
        env.reset("Test")

        obs, done, success = env.step("cd src && ls")
        assert "main.py" in obs
        assert env._state.cwd == "/workspace/src"

    def test_task_verification_port_fix(self):
        """Test that fixing port configuration verifies correctly."""
        task = CODING_TASKS["training"][1]  # Fix port from 8000 to 3000
        env = CodingEnvironment(task)
        env.reset(task.goal)

        # Before fix - should not verify (port is 8000)
        config_before = env._state.get_file_content("/workspace/src/config.py")
        assert "port: int = 8000" in config_before
        assert not task.verify(env._state)

        # Apply the fix - change 8000 to 3000
        env.step("sed -i 's/= 8000/= 3000/g' src/config.py")

        # After fix - should verify (port is now 3000)
        config_after = env._state.get_file_content("/workspace/src/config.py")
        assert "port: int = 3000" in config_after
        assert task.verify(env._state)

    def test_task_verification_python_files(self):
        """Test listing Python files verifies correctly."""
        task = CODING_TASKS["training"][2]  # List Python files in src
        env = CodingEnvironment(task)
        env.reset(task.goal)

        # Run the command
        env.step("ls src")

        # Should verify
        assert task.verify(env._state)

    def test_max_actions_limit(self):
        """Test that environment ends after max actions."""
        task = CodingTask(goal="Test", verify=lambda s: False)
        env = CodingEnvironment(task)
        env._max_actions = 3
        env.reset("Test")

        env.step("ls")
        env.step("pwd")
        obs, done, success = env.step("ls")

        assert done
        assert not success
        assert "Maximum actions reached" in obs


class TestCodingTasks:
    """Test the task definitions."""

    def test_training_tasks_defined(self):
        assert len(CODING_TASKS["training"]) > 0
        for task in CODING_TASKS["training"]:
            assert task.goal
            assert callable(task.verify)

    def test_evaluation_tasks_defined(self):
        assert len(CODING_TASKS["evaluation"]) > 0
        for task in CODING_TASKS["evaluation"]:
            assert task.goal
            assert callable(task.verify)

    def test_task_categories(self):
        """Verify tasks have appropriate categories."""
        all_tasks = CODING_TASKS["training"] + CODING_TASKS["evaluation"]
        categories = {t.category for t in all_tasks}
        assert "code-analysis" in categories
        assert "debugging" in categories

    def test_task_difficulties(self):
        """Verify tasks have difficulty levels."""
        all_tasks = CODING_TASKS["training"] + CODING_TASKS["evaluation"]
        difficulties = {t.difficulty for t in all_tasks}
        assert "easy" in difficulties
        assert "medium" in difficulties or "hard" in difficulties


class TestPromptTemplates:
    """Test that prompt templates are properly formatted."""

    def test_plan_prompt_has_placeholders(self):
        assert "{goal}" in PLAN_PROMPT
        assert "{examples}" in PLAN_PROMPT

    def test_reason_prompt_has_placeholders(self):
        assert "{goal}" in REASON_PROMPT
        assert "{plan}" in REASON_PROMPT
        assert "{observation}" in REASON_PROMPT
        assert "{examples}" in REASON_PROMPT

    def test_act_prompt_has_placeholders(self):
        assert "{goal}" in ACT_PROMPT
        assert "{plan}" in ACT_PROMPT
        assert "{reasoning}" in ACT_PROMPT


class TestWorkspaceCreation:
    """Test the workspace file structure."""

    def test_create_coding_workspace(self):
        files, directories = create_coding_workspace()

        # Check essential files exist
        assert "/workspace/src/main.py" in files
        assert "/workspace/src/config.py" in files
        assert "/workspace/tests/test_app.py" in files
        assert "/workspace/README.md" in files

        # Check directories
        assert "/workspace" in directories
        assert "/workspace/src" in directories
        assert "/workspace/tests" in directories

    def test_config_has_bug_to_fix(self):
        """Verify the config file has the port bug for fixing."""
        files, _ = create_coding_workspace()
        config_content = files["/workspace/src/config.py"]

        # Should have wrong port (8000) that needs to be fixed to 3000
        assert "port: int = 8000" in config_content
        # Should NOT already have 3000 anywhere (to make test valid)
        assert "= 3000" not in config_content
        # README says it should be 3000
        readme = files["/workspace/README.md"]
        assert "3000" in readme


class TestAgentIntegration:
    """Integration tests for the agent (with mock LLM for speed)."""

    @pytest.fixture
    def mock_llm(self):
        """Create a mock LLM that produces valid commands."""
        from examples.mock_llm import MockLLMProvider
        return MockLLMProvider()

    @pytest.fixture
    def agent(self, mock_llm, tmp_path):
        """Create an agent with mock LLM."""
        from icrl import Agent

        return Agent(
            llm=mock_llm,
            db_path=str(tmp_path / "trajectories"),
            plan_prompt=PLAN_PROMPT,
            reason_prompt=REASON_PROMPT,
            act_prompt=ACT_PROMPT,
            k=2,
            max_steps=5,
        )

    def test_agent_train_creates_trajectory(self, agent):
        """Test that training creates a trajectory."""
        task = CODING_TASKS["training"][2]  # List Python files (easy)
        env = CodingEnvironment(task)

        trajectory = asyncio.run(agent.train(env, task.goal))

        assert trajectory is not None
        assert len(trajectory.steps) > 0
        assert trajectory.goal == task.goal

    def test_agent_run_creates_trajectory(self, agent):
        """Test that inference creates a trajectory."""
        task = CODING_TASKS["evaluation"][0]
        env = CodingEnvironment(task)

        trajectory = asyncio.run(agent.run(env, task.goal))

        assert trajectory is not None
        assert len(trajectory.steps) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
