from __future__ import annotations

import json

import pytest

from last_asylum_doctor.probe.navigation import (
    Frame,
    NavigationAgent,
    NavigationGraph,
    NavigationPolicy,
    OCRAnchor,
    RapidOcrPerceiver,
    SafeAction,
    SafeNavigationError,
    SessionJournal,
    StateRecognizer,
)


class FixtureFrames:
    def __init__(self, *frames: Frame) -> None:
        self.frames = list(frames)
        self.labels: list[str | None] = []

    def capture(self, label: str | None = None) -> Frame:
        self.labels.append(label)
        return self.frames.pop(0)


class RecordingInput:
    def __init__(self) -> None:
        self.actions: list[SafeAction] = []

    def perform(self, action: SafeAction, frame: Frame) -> None:
        del frame
        self.actions.append(action)


def frame(
    digest: str,
    *texts: str,
    bbox: tuple[tuple[float, float], ...] = ((100.0, 200.0), (300.0, 200.0)),
) -> Frame:
    anchors = tuple(OCRAnchor(text, 0.95, bbox) for text in texts)
    return Frame(
        b"frame", digest, 900, 1600, anchors, {"client_version_name": "1.0.97"}
    )


def journal(tmp_path, goal: str) -> SessionJournal:
    return SessionJournal(
        tmp_path / "sessions",
        goal=goal,
        client_version="1.0.97",
        server="283",
        session_id=goal.replace("-", "_") + "_session",
    )


def test_allowlisted_navigation_action_is_accepted() -> None:
    action = SafeAction(
        action_type="tap",
        semantic_target="research_lab",
        source_state="sanctuary_main",
        normalized_point=(0.5, 0.25),
        expected_next_state="research_lab",
        confidence=0.9,
    )

    NavigationPolicy().validate(action)


def test_account_changing_action_is_rejected() -> None:
    action = SafeAction(
        action_type="tap",
        semantic_target="start_research",
        source_state="research_node_detail",
        normalized_point=(0.5, 0.5),
        confidence=0.9,
    )

    with pytest.raises(SafeNavigationError):
        NavigationPolicy().validate(action)


def test_unknown_action_type_is_rejected() -> None:
    action = SafeAction(
        action_type="attack",
        semantic_target="enemy_base",
        source_state="sanctuary_main",
        confidence=0.9,
    )

    with pytest.raises(SafeNavigationError):
        NavigationPolicy().validate(action)


def test_dry_run_sends_no_input_and_creates_journal(tmp_path) -> None:
    source = FixtureFrames(frame("before", "Research Lab", "Training Grounds"))
    input_driver = RecordingInput()
    graph = NavigationGraph(tmp_path / "graph.json")
    session = journal(tmp_path, "navigate-to-research-lab")
    result = NavigationAgent(
        source,
        input_driver,
        graph=graph,
        journal=session,
        dry_run=True,
        transition_wait=0,
    ).run("navigate-to-research-lab")

    assert result["stop_reason"] == "dry_run"
    assert input_driver.actions == []
    assert result["proposed_action"]["semantic_target"] == "research_lab"
    assert session.json_path.exists()
    assert session.markdown_path.exists()
    assert not graph.path.exists()


def test_successful_transition_is_recorded_and_persisted(tmp_path) -> None:
    source = FixtureFrames(
        frame("before", "Research Lab", "Training Grounds"),
        frame("after", "Research Lab", "Research"),
    )
    input_driver = RecordingInput()
    graph_path = tmp_path / "graph.json"
    result = NavigationAgent(
        source,
        input_driver,
        graph=NavigationGraph(graph_path),
        journal=journal(tmp_path, "navigate-to-research-lab"),
        dry_run=False,
        transition_wait=0,
    ).run("navigate-to-research-lab")

    assert result["stop_reason"] == "goal_reached"
    assert len(input_driver.actions) == 1
    saved = json.loads(graph_path.read_text(encoding="utf-8"))
    edge = next(iter(saved["edges"].values()))
    assert edge["success_count"] == 1
    assert edge["failure_count"] == 0
    assert edge["destination_state"] == "research_lab"
    assert len(NavigationGraph(graph_path).edges) == 1


def test_failed_transition_is_recorded(tmp_path) -> None:
    source = FixtureFrames(
        frame("before", "Research Lab", "Training Grounds"),
        frame("after", "No known controls"),
    )
    graph_path = tmp_path / "graph.json"
    result = NavigationAgent(
        source,
        RecordingInput(),
        graph=NavigationGraph(graph_path),
        journal=journal(tmp_path, "navigate-to-research-lab"),
        dry_run=False,
        transition_wait=0,
    ).run("navigate-to-research-lab")

    assert result["stop_reason"] == "transition_failed"
    edge = next(
        iter(json.loads(graph_path.read_text(encoding="utf-8"))["edges"].values())
    )
    assert edge["success_count"] == 0
    assert edge["failure_count"] == 1


def test_loop_detection_stops_after_recording_transition(tmp_path) -> None:
    source = FixtureFrames(
        frame("same", "Research Lab", "Training Grounds"),
        frame("same", "Research Lab", "Research"),
    )
    result = NavigationAgent(
        source,
        RecordingInput(),
        graph=NavigationGraph(tmp_path / "graph.json"),
        journal=journal(tmp_path, "navigate-to-research-lab"),
        dry_run=False,
        transition_wait=0,
    ).run("navigate-to-research-lab")

    assert result["stop_reason"] == "loop_detected"


def test_step_limit_handling(tmp_path) -> None:
    class OneStepAgent(NavigationAgent):
        def propose_action(self, goal, frame, state):
            del goal, frame, state
            return SafeAction(
                action_type="tap",
                semantic_target="research_lab",
                source_state="sanctuary_main",
                expected_next_state="training_grounds",
                normalized_point=(0.5, 0.5),
                confidence=0.9,
            )

    source = FixtureFrames(
        frame("before", "Research Lab", "Training Grounds"),
        frame("after", "Training Grounds", "Current Level", "Next Level", "Back"),
    )
    result = OneStepAgent(
        source,
        RecordingInput(),
        graph=NavigationGraph(tmp_path / "graph.json"),
        journal=journal(tmp_path, "navigate-to-research-lab"),
        dry_run=False,
        max_steps=1,
        transition_wait=0,
    ).run("navigate-to-research-lab")

    assert result["stop_reason"] == "step_limit_reached"


def test_state_recognizer_does_not_claim_unknown_state() -> None:
    state = StateRecognizer().recognize(frame("unknown", "A random label"))

    assert state.state_id == "unknown"
    assert state.confidence == 0.0


@pytest.mark.parametrize("text", ["Upgrade", "Training Grounds"])
def test_map_banners_do_not_claim_detail_states(text: str) -> None:
    state = StateRecognizer().recognize(frame("map", text))

    assert state.state_id == "unknown"
    assert state.confidence == 0.0


def test_building_detail_requires_panel_evidence() -> None:
    state = StateRecognizer().recognize(
        frame("detail", "Upgrade", "Current Level", "Back")
    )

    assert state.state_id == "building_detail"
    assert state.confidence > 0.0


def test_high_confidence_captured_states_are_recognized() -> None:
    recognizer = StateRecognizer()
    fixtures = {
        "bag_inventory": ("Bag", "Special", "Resource", "Speedup", "Hero", "Gear"),
        "insufficient_items": (
            "Insufficient Items",
            "Owned",
            "Resource Item",
            "Use",
        ),
        "kingdom_war": ("Kingdom War", "Weekly", "Royal City", "Overview"),
        "black_ops": ("Black Ops", "Covert Ops Force"),
        "loot": ("Loot", "Claim All"),
        "sanctuary_map": ("Upgrade", "Bag", "Hero", "Territory", "Alliance"),
    }

    for expected, texts in fixtures.items():
        state = recognizer.recognize(frame(expected, *texts))
        assert state.state_id == expected
        assert state.confidence >= 0.9


def test_rapid_ocr_engine_is_constructed_once() -> None:
    constructions = 0

    def create_engine():
        nonlocal constructions
        constructions += 1

        def recognize(image):
            del image
            return [([(0, 0), (1, 0), (1, 1), (0, 1)], "Research", 0.9)], None

        return recognize

    perceiver = RapidOcrPerceiver(
        engine_factory=create_engine, image_decoder=lambda screenshot: screenshot
    )

    assert perceiver.detect(b"first")[0].text == "Research"
    assert perceiver.detect(b"second")[0].text == "Research"
    assert constructions == 1
