from typing import Optional
import logging
import numpy as np

from auto import circuit_pb2
import hcomponent

class EquationManager:
    def __init__(self) -> None:
        self.current_vcount = 0
        self.constaints = []
        # A * I = B
        self.I = None  # not solved

    def reset(self):
        self.current_vcount = 0
        self.constaints.clear()
        self.I = None

    def is_solved(self):
        return self.I is not None

    def add_current_constraint(self, current_coffs, sum):
        self.I = None
        self.constaints.append((current_coffs, sum))

    def get_result(self, current_coffs):
        assert self.is_solved()
        ans = 0
        for c_var in current_coffs:
            ans += current_coffs[c_var] * self.I[c_var]
        return ans

    def add_new_junction_currents(self, count):
        new_currents = [self.current_vcount+i for i in range(count)]
        self.current_vcount += count
        # sum of all outgoing current within a terminal is 0
        self.add_current_constraint({c:1 for c in new_currents}, 0)
        return new_currents

    def solve(self):
        A = []
        B = []
        for coeffs, sum in self.constaints:
            coeffs_list = [0]*self.current_vcount
            for cvar in coeffs:
                coeff = coeffs[cvar]
                coeffs_list[cvar] += coeff
            A.append(coeffs_list)
            B.append(sum)
        A = np.array(A)
        B = np.array(B)

        # This will return result even if the equations are incomplete
        self.I = list(np.linalg.lstsq(A, B, rcond=None)[0])
        return self.I


def get_term_to_comp_key(_term_id, c: circuit_pb2.Component):
    return (_term_id, id(c))

class KirchhoffCircuit:
    def __init__(self, circuit: circuit_pb2.Circuit) -> None:
        self.circuit = circuit
        self.eq = EquationManager()
        self.terminal_to_components = {}
        self.terminal_to_component_cvar = {}
        self.all_cycles = []  # avoid repeated info cycle if possible
        assert len(self.circuit.components) > 0, "atleast one component expected in circuit"
        self.reset()

    def reset(self):
        self.all_cycles.clear()
        self.eq.reset()
        self.remap_terminals()

        # takes care of disconnected or short circuit comp
        for c in self.circuit.components:
            c.state.current = 0

    def get_terminal_to_components(self):
        return self.terminal_to_components.copy()

    def remap_terminals(self):
        self.terminal_to_components.clear()
        self.terminal_to_component_cvar.clear()
        for c in self.circuit.components:
            for t in hcomponent.get_terminals(c):
                if t.id not in self.terminal_to_components:
                    self.terminal_to_components[t.id] = []
                self.terminal_to_components[t.id].append(c)

        for _id in self.terminal_to_components:
            currents = self.eq.add_new_junction_currents(len(self.terminal_to_components[_id]))
            for c, c_var in zip(self.terminal_to_components[_id], currents):
                key = get_term_to_comp_key(_id, c)

                # The following assert isn't valid
                # assert key not in self.terminal_to_component_cvar
                # a single terminal can be on both side of terminal
                # even in those cases it's same current going towards
                # the component, which can eventually lead to that
                # current being 0.
                if key in self.terminal_to_component_cvar:
                    oc_var = self.terminal_to_component_cvar[key]
                    if oc_var != c_var:
                        # both current have to be equal
                        self.eq.add_current_constraint({c_var: 1, oc_var: -1}, 0)
                self.terminal_to_component_cvar[key] = c_var

    def update_component_terminal_c(self, push_currents=False):
        for c in self.circuit.components:
            keys = [get_term_to_comp_key(o.id, c) for o in hcomponent.get_terminals(c)]
            assert len(keys) == 2, "solver is designed for component with 2 terminals only"
            anode_cvar = self.terminal_to_component_cvar[keys[0]]
            cathode_cvar = self.terminal_to_component_cvar[keys[1]]
            if hcomponent.is_same_current_on_component_terminal(c):
                if not push_currents:
                    self.eq.add_current_constraint({anode_cvar:1, cathode_cvar:1}, 0)
                else:
                    c.state.current = self.eq.get_result({anode_cvar:1})
            else:
                if not push_currents:
                    self.eq.add_current_constraint({anode_cvar:1}, 0)
                    self.eq.add_current_constraint({cathode_cvar:1}, 0)
                else:
                    c.state.current = 0

    def step(self):
        self.reset()
        self.dfs_start()
        self.update_component_terminal_c()
        for cycle in self.all_cycles:
            self.compute_loop_voltage(cycle)
        self.eq.solve()
        self.update_component_terminal_c(push_currents=True)

    def _get_voltage(self, t_id1, c: circuit_pb2.Component, t_id2):
        # this method only runs on circuit loop
        assert hcomponent.is_same_current_on_component_terminal(c)
        key = get_term_to_comp_key(t_id1, c)
        c_var = self.terminal_to_component_cvar[key]
        fixed_voltage = 0
        if c.HasField("button") or c.HasField("led"):
            c_coeff = 0 # no voltage drop, led have it's own internal resistor
        elif c.HasField("resistor"):
            c_coeff = c.resistor.ohms
        elif c.HasField("battery"):
            c_coeff = 0
            fixed_voltage = c.battery.voltage
            # current in battery from cathode to anode
            if c.battery.cathode.id == t_id1:
                pass
            else:
                assert c.battery.anode.id == t_id1
                fixed_voltage *= -1
        else:
            raise ValueError("not supported")

        return (c_var, c_coeff, fixed_voltage)

    def compute_loop_voltage(self, path):
        # path have terminal and components in alternate order
        # terminals, [comp, term]*
        assert len(path) % 2 == 1
        eqc = {}
        loop_fixed_voltage = 0
        for i in range(1,len(path),2):
            c_var, c_coeff, vol = self._get_voltage(path[i-1], path[i], path[i+1])
            if c_var not in eqc:
                eqc[c_var] = 0
            eqc[c_var] += c_coeff
            loop_fixed_voltage += vol
        self.eq.add_current_constraint(eqc, loop_fixed_voltage)

    def dfs_start(self):
        self._node_parent = {}
        for _id in self.terminal_to_components:
            logging.info(f"{_id} => [{[c.name for c in self.terminal_to_components[_id]]}]")

        start_terminal = hcomponent.get_terminals(self.circuit.components[0])[0]
        path = []
        self.dfs(node=start_terminal,
                 parent=None,path=path)

    def dfs_over_component(self, c: circuit_pb2.Component):
        return hcomponent.is_same_current_on_component_terminal(c)

    def dfs_found_cycle(self, path):
        self.all_cycles.append(path)

    def dfs(self,
            node: circuit_pb2.Terminal,
            path,
            parent: Optional[circuit_pb2.Terminal] = None,
            ):
        if node.id in path:
            # loop detected
            # badly optimized implementation it's error prone
            loop = path[path.index(node.id):]+[node.id]
            assert len(loop) >= 3
            self.dfs_found_cycle(loop)
            return
        path.append(node.id)

        avoid_terminals = [node.id]
        if parent is not None:
            avoid_terminals.append(parent.id)
        for c in self.terminal_to_components[node.id]:
            if self.dfs_over_component(c):
                for o in hcomponent.get_terminals(c):
                    if o.id not in avoid_terminals:
                        self.dfs(o, parent=node, path=path+[c])
