import pytest
import sys
from typing import Any
from fs.messages.message import Message
from fs.common import constants, message_ids

# Custom MIDs for testing
CUSTOM_CMD_MID = 0x1A2B  # bit 12 is 1 (0x1000)
CUSTOM_TEL_MID = 0x0C3D  # bit 12 is 0 (0x0000)

def test_message_all_fields():
    # Construct a Message with every field explicitly set
    payload = {"key": "value"}
    msg = Message(
        mid=CUSTOM_CMD_MID,
        aid=constants.APP_ID_GS,
        func_code=1,
        payload=payload
    )
    assert msg.mid == CUSTOM_CMD_MID
    assert msg.aid == constants.APP_ID_GS
    assert msg.seq == 0
    assert msg.timestamp == 0.0
    assert msg.func_code == 1
    assert msg.payload == payload

def test_message_no_optional_fields():
    # Construct a Message with no optional fields, assert defaults are correct
    msg = Message(mid=CUSTOM_TEL_MID, aid=constants.APP_ID_ES)
    assert msg.mid == CUSTOM_TEL_MID
    assert msg.aid == constants.APP_ID_ES
    assert msg.seq == 0
    assert msg.timestamp == 0.0
    assert msg.func_code == 0
    assert msg.payload == {}

def test_mid_identifies_command_vs_telemetry():
    # Assert mid & 0x1000 correctly identifies command vs telemetry
    cmd_msg = Message(mid=CUSTOM_CMD_MID, aid=constants.APP_ID_GS)
    tel_msg = Message(mid=CUSTOM_TEL_MID, aid=constants.APP_ID_ES)
    
    # 0x1000 bit is 1 for commands, 0 for telemetry
    assert (cmd_msg.mid & 0x1000) != 0, "Command MID should have 0x1000 bit set"
    assert (tel_msg.mid & 0x1000) == 0, "Telemetry MID should not have 0x1000 bit set"

def test_immutability_of_timestamp():
    # Assert you cannot accidentally mutate a sent message's timestamp from outside
    msg = Message(mid=CUSTOM_TEL_MID, aid=constants.APP_ID_ES)
    with pytest.raises(AttributeError):
        msg.timestamp = 123.45

def test_mid_undefined_is_invalid_routing_key():
    # Assert MID_UNDEFINED is never a valid routing key (used as a sentinel everywhere)
    assert message_ids.MID_UNDEFINED == 0x0000

    with pytest.raises(ValueError):
        Message(mid=message_ids.MID_UNDEFINED, aid=constants.APP_ID_ES)

def test_zero_dynamic_allocation():
    # Zero dynamic allocation after construction (slots=True enforces this)
    msg = Message(mid=CUSTOM_TEL_MID, aid=constants.APP_ID_ES)
    
    # slots prevents dynamic attribute assignment
    with pytest.raises(AttributeError):
        msg.new_dynamic_field = 1

def test_mid_registry_unique():
    # Every constant in the MID registry is unique
    mids_list = [
        getattr(message_ids, name) 
        for name in dir(message_ids) 
        if not name.startswith("__") and isinstance(getattr(message_ids, name), int)
    ]
    assert len(set(mids_list)) == len(mids_list), f"MIDs in registry are not unique: {mids_list}"

def test_explicit_types_enforced_by_annotations():
    # All fields have explicit types, no Any where avoidable
    annotations = Message.__annotations__
    assert "mid" in annotations
    assert "aid" in annotations
    assert "func_code" in annotations
    assert "payload" in annotations
    
    # Just asserting we aren't using bare Any
    for field_name, field_type in annotations.items():
        assert field_type is not Any, f"Field {field_name} uses Any!"
