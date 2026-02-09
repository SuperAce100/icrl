"""Offline walkthrough of database, retrieval, curation, and validation APIs.

This example is deterministic and requires no API keys.

It demonstrates:
- TrajectoryDatabase add/get/search/search_steps/get_all/remove
- record_retrieval and get_curation_metadata
- TrajectoryRetriever retrieve_for_plan/retrieve_for_step/record_episode_result
- CurationManager utility scoring and pruning
- HashEmbedder usage
- extract_code_artifacts + CodePersistenceValidator
- TrajectoryDatabase validate_trajectory / validate_all helpers

Run with:
    uv run python tests/database_api_walkthrough.py
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from icrl import Step, Trajectory
from icrl.curation import CurationManager
from icrl.database import TrajectoryDatabase
from icrl.embedder import HashEmbedder
from icrl.retriever import TrajectoryRetriever
from icrl.validators import CodePersistenceValidator, extract_code_artifacts


def make_trajectory(goal: str, action: str) -> Trajectory:
    return Trajectory(
        goal=goal,
        plan="1. Inspect\n2. Execute",
        steps=[
            Step(
                observation=f"Observation for: {goal}",
                reasoning=f"Reasoning for: {goal}",
                action=action,
            )
        ],
        success=True,
    )


def run_database_and_retriever_examples(base_dir: Path) -> None:
    db = TrajectoryDatabase(
        path=base_dir / "db",
        embedder=HashEmbedder(dimension=64),
    )

    traj_config = make_trajectory(
        "Find the service port in config",
        "cat /etc/app/config.json",
    )
    traj_backup = make_trajectory(
        "Copy notes file to backup",
        "cp /home/user/docs/notes.txt /backup",
    )

    db.add(traj_config, extract_artifacts=False)
    db.add(traj_backup, extract_artifacts=False)

    assert len(db) == 2
    assert db.get(traj_config.id) is not None
    assert db.get("missing-id") is None
    assert len(db.get_all()) == 2
    assert db.search("config port", k=1), "search() should return similar trajectory"
    assert db.search_steps("config", k=2), "search_steps() should return step examples"

    retriever = TrajectoryRetriever(db, k=1)
    plan_examples = retriever.retrieve_for_plan("service config")
    step_examples = retriever.retrieve_for_step(
        "service config",
        "inspect config",
        "saw config path",
    )
    assert plan_examples
    assert step_examples
    assert retriever.get_retrieved_ids(), "retrieved ids should be tracked"
    retriever.record_episode_result(success=True)
    assert retriever.get_retrieved_ids() == []

    for _ in range(3):
        db.record_retrieval([traj_config.id], led_to_success=False)

    metadata = db.get_curation_metadata(traj_config.id)
    assert metadata is not None
    assert metadata.times_retrieved >= 3

    curation = CurationManager(
        db,
        threshold=0.6,
        min_retrievals=3,
        curate_every=1,
    )
    low_utility = curation.get_low_utility_trajectories()
    assert traj_config.id in low_utility

    removed = curation.curate()
    assert traj_config.id in removed
    assert db.get(traj_config.id) is None

    assert db.remove("missing-id") is False
    assert db.remove(traj_backup.id) is True
    assert len(db) == 0


def run_validation_examples(base_dir: Path) -> None:
    working_dir = base_dir / "workspace"
    working_dir.mkdir(parents=True, exist_ok=True)

    write_payload = {"path": "settings.env", "content": "PORT=3000\nDEBUG=true\n"}
    write_action = f"Write({json.dumps(write_payload)})"
    write_trajectory = make_trajectory("Create settings file", write_action)

    artifacts = extract_code_artifacts(write_trajectory, working_dir=working_dir)
    assert len(artifacts) == 1

    settings_file = working_dir / "settings.env"
    settings_file.write_text("PORT=3000\nDEBUG=true\n")

    validator = CodePersistenceValidator(working_dir=working_dir)
    intact = validator.validate(write_trajectory, artifacts)
    assert intact.score == 1.0

    settings_file.write_text("PORT=9000\n")
    modified = validator.validate(write_trajectory, artifacts)
    assert modified.score < 1.0

    db = TrajectoryDatabase(
        path=base_dir / "validation_db",
        embedder=HashEmbedder(dimension=64),
    )
    db.add(write_trajectory, working_dir=working_dir, extract_artifacts=True)

    one = db.validate_trajectory(write_trajectory.id, working_dir=working_dir)
    assert one is not None

    all_results = db.validate_all(working_dir=working_dir)
    assert len(all_results) == 1

    assert db.get_active_trajectories()
    assert db.get_deprecated_trajectories() == []
    assert db.get_superseded_trajectories() == []


def main() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        run_database_and_retriever_examples(base)
        run_validation_examples(base)

    print("Database API walkthrough passed.")


if __name__ == "__main__":
    main()
