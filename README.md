# DC Circuit Simulator [![CI](https://github.com/scopeInfinity/dc-circuit-simulator/actions/workflows/ci.yml/badge.svg)](https://github.com/scopeInfinity/dc-circuit-simulator/actions/workflows/ci.yml)

Simulate an electrical circuit represented in a configuration.

## Components

As of now following components/junctions are supported.

* LED: Acts as a visual signal
* Button / Switch: Controlled using a keyboard (in interactive mode)
* Battery: DC power source
* Resistor
* Wires

## Quick Usage
* To rebuilt `circuit_pb2.py`
  * Install `protoc` and execute `make auto/circuit_pb2.py`
* See tool usage using `python3 . --help`
* Run example in interactive mode: `python3 . -i tests/5buttons_3leds.textproto`

## Example

A circuit powered by 5V battery to
  *  Turn on `Led{L_RED}` if both `Button{B_RED1}` and `Button{B_RED2}` are pressed.
  *  Turn on `Led{L_YELLOW}` if `Button{B_YELLOW}` is pressed.
  *  Keep `Led{L_ALLRED}` always on.
  *  Turn off `Led{L_GREEN}` if `Button{B_GREEN}` is pressed.

Config: [5buttons_3leds.textproto](tests/5buttons_3leds.textproto)

<img src="https://github.com/scopeInfinity/dc-circuit-simulator/assets/9819066/9fff45c5-c39b-483c-901d-573aead0b215" width=60% height=60%>




