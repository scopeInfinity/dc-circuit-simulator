from typing import List

from auto import circuit_pb2

LED_MIN_CURRENT = 0.1e-3  # 0.1mA

def get_current(state: circuit_pb2.StateVC):
    return state.current

def is_led_on(led_c: circuit_pb2.Component):
    assert led_c.HasField("led")
    return get_current(led_c.state) >= LED_MIN_CURRENT

_auto_terminal = set()
def generate_uniq_terminal():
    # Be careful as user can reuse this terminal name as well
    # but we don't care at this moment.
    terminal_name = f"tmp_{len(_auto_terminal)}"
    _auto_terminal.add(terminal_name)
    return terminal_name

def get_key(button: circuit_pb2.Button):
    assert len(button.input.keyboard_key) == 1, f"exactly one key char expected in: {button}"
    c = button.input.keyboard_key
    return f"'{str(c)}'"

def get_terminals(c: circuit_pb2.Component):
    '''Return terminals of a component.

    The order of component is from anode, cathode and then
    the third terminal (doesn't exists).
    '''
    if c.HasField("battery"):
        terminals = [c.battery.anode, c.battery.cathode]
    elif c.HasField("led"):
        terminals = [c.led.anode, c.led.cathode]
    elif c.HasField("resistor"):
        terminals = [c.resistor.point_a, c.resistor.point_b]
    elif c.HasField("button"):
        terminals = [c.button.point_a, c.button.point_b]
    else:
        raise ValueError("component doesn't have a component")
    assert len(terminals) >= 2, "atleast two terminals expected"
    for t in terminals:
        assert len(t.id) > 0, f"0 length terminal find in {c}"
    return terminals

def get_terminals_from_junction(j: circuit_pb2.Junction):
    for t in j.terminals:
        assert len(t.id) > 0, f"0 length terminal find in {j}"
    return j.terminals

def replace_terminal_ids(c: circuit_pb2.Component, new_map):
     for t in get_terminals(c):
          t.id = new_map[t.id]

def filter_components(cl: List[circuit_pb2.Component], _type):
    result = []
    for c in cl:
        if c.HasField(_type):
            if _type in ["button", "led", "battery", "resistor"]:
                result.append(c)
            else:
                raise ValueError(f"can't filter {_type} from components")
    return result

def is_same_current_on_component_terminal(c: circuit_pb2.Component):
    connected = False
    if c.HasField("resistor") or c.HasField("led") or c.HasField("battery"):
        connected = True
    elif c.HasField("button"):
        connected = c.button.input.is_pressed
    else:
        raise ValueError(f"unkown component {c}")
    return connected
