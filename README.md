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
