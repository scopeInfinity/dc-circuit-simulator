from typing import Union
import logging
import termcolor
import time

from auto import circuit_pb2
import algo
import hcomponent
import solver

_LedColorToTermColor = {
    circuit_pb2.Led.RED: "on_red",
    circuit_pb2.Led.YELLOW: "on_yellow",
    circuit_pb2.Led.GREEN: "on_green",
}

class Sim:
    def __init__(self, config: circuit_pb2.Simulator, is_interactive=True):
        self.humanize_auto_terminal = {}
        self.circuit = config.circuit
        self.prep_circuit()
        if is_interactive:
            self.prep_button_and_handler()
        self.kirchhoff = solver.KirchhoffCircuit(self.circuit)

    def _insert_internal_resistor(self, name, c: Union[
        circuit_pb2.Battery,
        circuit_pb2.Led]):
        if isinstance(c, circuit_pb2.Battery) or isinstance(c, circuit_pb2.Led):
            o_cathode = c.cathode.id
            n_cathode = hcomponent.generate_uniq_terminal()
            assert n_cathode not in self.humanize_auto_terminal
            self.humanize_auto_terminal[n_cathode] = set([f"INSIDE:{name}"])
            c.cathode.id = n_cathode
            new_component = self.circuit.components.add()
            new_component.resistor.ohms = c.resistor.ohms
            new_component.resistor.point_a.id = n_cathode
            new_component.resistor.point_b.id = o_cathode
            new_component.name = f"{name}_ir"
            c.ClearField("resistor")
        else:
            raise ValueError("_insert_internal_resistor is only for Batter or LED")

    def prep_circuit(self):
        all_terminal_ids = set()
        for c in self.circuit.components:
            terminal_ids = [t.id for t in hcomponent.get_terminals(c)]
            all_terminal_ids = all_terminal_ids.union(set(terminal_ids))

        for j in self.circuit.junctions:
            terminal_ids = [t.id for t in hcomponent.get_terminals_from_junction(j)]
            all_terminal_ids = all_terminal_ids.union(set(terminal_ids))

        dsu = algo.DSU(all_terminal_ids)
        for c in self.circuit.junctions:
            for t in c.terminals:
                dsu.merge(c.terminals[0].id, t.id)

        terminal_to_group = dsu.summarize()
        new_terminal_naming = {}

        for gid in terminal_to_group:
            ids = terminal_to_group[gid]
            new_terminal = hcomponent.generate_uniq_terminal()
            for _id in ids:
                assert _id not in new_terminal_naming
                new_terminal_naming[_id] = new_terminal
            self.humanize_auto_terminal[new_terminal] = ids

        for c in self.circuit.components:
            hcomponent.replace_terminal_ids(c, new_terminal_naming)

        del self.circuit.junctions[:]


        # add internal resistors
        # please note internal resistors never add new mergeable
        # junction.
        for c in self.circuit.components:
            if c.HasField("battery"):
                self._insert_internal_resistor(c.name, c.battery)
            elif c.HasField("led"):
                self._insert_internal_resistor(c.name, c.led)


        logging.info("Auto Terminals")
        for tt in self.humanize_auto_terminal:
            logging.info(f"{tt} => {self.humanize_auto_terminal[tt]}")

    def prep_button_and_handler(self):
        # Load package iff we need it, it's not required for non-interactive mode.
        from pynput import keyboard

        allowed_keys = {}
        for index, c in enumerate(self.circuit.components):
            if c.HasField("button"):
                key = hcomponent.get_key(c.button)
                if key not in allowed_keys:
                    allowed_keys[key] = []
                allowed_keys[key].append(index)

        def on_press(key):
            for bindex in allowed_keys.get(str(key), []):
                self.circuit.components[bindex].button.input.is_pressed = True

        def on_release(key):
            for bindex in allowed_keys.get(str(key), []):
                self.circuit.components[bindex].button.input.is_pressed = False

        for _key in allowed_keys:
            on_release(_key)

        self.key_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        self.key_listener.start()

    def _process_reset_state(self):
        for c in self.circuit.components:
            c.state.ClearField("current")

    def _process_compute_vi(self):
        self.kirchhoff.step()
        return False # stable state

    def process(self):
        self._process_reset_state()
        changes_count = 0
        while True:
            if not self._process_compute_vi():
                break
            changes_count += 1
            assert changes_count < 10000, "stuck or circuit too big"

    def step(self):
        self.process()

    def draw(self, clrscr=True):
        if clrscr:
            print("\x1b[2J") # clear screen
        print("# Button(s)")
        for c in hcomponent.filter_components(self.circuit.components, "button"):
            label = f"{c.button.label:^10s}"
            if c.button.input.is_pressed:
                label = termcolor.colored(label, "black", "on_light_grey")
            print(f"[{label}] key:'{c.button.input.keyboard_key}'\tname: {c.name}")
        print()
        print()
        print()
        print("# Led(s)")
        for c in hcomponent.filter_components(self.circuit.components, "led"):
            label = "  "
            if hcomponent.is_led_on(c):
                label = termcolor.colored(label, None, _LedColorToTermColor.get(c.led.color, None))
            print(f"[{label}]\tname: {c.name}")
        print()
        print()

    def print(self):
        print(self.circuit)

    def run(self):
        while(True):
            self.step()
            self.draw()
            time.sleep(0.1)
