from miniviki.mca import (
    APPROVAL_REQUEST,
    MESSAGE,
    RUN_END,
    TERMINAL_KINDS,
    ClientCapability,
    ClientTool,
    ContextHandle,
    ContextInit,
    StreamEvent,
    Transport,
)


class HandWrittenTransport:
    """Anyone can bind the contract: no import of the server or the core is needed."""

    async def create_context(self, init: ContextInit) -> dict:
        return {"id": "ctx_1"}

    async def context_state(self, context_id: str) -> dict:
        return {"id": context_id}

    async def submit(self, context_id: str, text: str) -> dict:
        return {"run_id": "run_1"}

    async def subscribe(self, context_id: str, from_seq: int = 0):
        yield StreamEvent(seq=0, kind=RUN_END, payload={"status": "done"})

    async def interrupt(self, context_id: str) -> dict:
        return {"ok": True}

    async def resolve_approval(self, context_id: str, call_id: str, decision: str) -> dict:
        return {"ok": True}

    async def update_tools(self, context_id: str, tools: list[ClientTool]) -> dict:
        return {"id": context_id}

    async def aclose(self) -> None:
        return None


def test_a_hand_written_transport_satisfies_the_protocol():
    assert isinstance(HandWrittenTransport(), Transport)


def test_stream_event_round_trips():
    event = StreamEvent(seq=3, kind=MESSAGE, payload={"role": "assistant", "content": "hi"})
    assert StreamEvent.from_json(event.to_json()) == event


def test_terminal_kinds_are_exactly_run_end_and_approval():
    assert set(TERMINAL_KINDS) == {RUN_END, APPROVAL_REQUEST}
    assert StreamEvent(seq=0, kind=RUN_END).is_terminal()
    assert StreamEvent(seq=0, kind=APPROVAL_REQUEST).is_terminal()
    assert not StreamEvent(seq=0, kind=MESSAGE).is_terminal()


def test_capability_flags_default_to_the_conservative_side():
    capability = ClientCapability()
    assert capability.shell is False
    assert capability.approval_ui is False
    assert capability.markdown is True
    assert capability.flags() == ("markdown", "streaming")


def test_capability_round_trips_through_json():
    capability = ClientCapability(label="ramyon", shell=True, approval_ui=True)
    assert ClientCapability.from_json(capability.to_json()) == capability


def test_client_tool_round_trips():
    tool = ClientTool(name="client:shell", description="run locally", parameters={"type": "object"})
    assert ClientTool.from_json(tool.to_json()) == tool


def test_context_init_serialises_capabilities_and_tools():
    init = ContextInit(
        kind="side",
        label="notes",
        capabilities=ClientCapability(label="ramyon"),
        tools=(ClientTool(name="client:shell"),)
    )
    raw = init.to_json()
    assert raw["kind"] == "side"
    assert raw["capabilities"]["label"] == "ramyon"
    assert raw["tools"][0]["name"] == "client:shell"


def test_context_handle_parses_the_wire_shape():
    handle = ContextHandle.from_json(
        {"id": "ctx_9", "kind": "main", "toolset_version": "abc", "label": "work"}
    )
    assert handle.id == "ctx_9"
    assert handle.toolset_version == "abc"
