.PHONY: artifacts

build:
	mkdir build

auto:
	mkdir -p auto

auto/circuit_pb2.py: proto/circuit.proto auto
	protoc --proto_path=proto --python_out=auto/ $<

build/circuit_%.txt: tests/%.textproto build
	python3 . -pc $< > $@

build/display_%.txt: tests/%.textproto build
	python3 . -dc $< > $@

artifacts: \
	$(patsubst tests/%.textproto, build/circuit_%.txt,$(wildcard tests/*.textproto)) \
	$(patsubst tests/%.textproto, build/display_%.txt,$(wildcard tests/*.textproto))
