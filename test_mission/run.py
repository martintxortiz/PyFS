# test_mission/run.py

from __future__ import annotations


from pyfs.core.fs_executive import FSExecutive
from test_mission.nodes.afm_node import AutomatedFLightManagerNode
from test_mission.nodes.gnc_c_node import GNCCNode
from test_mission.nodes.gnc_g_node import GNCGNode
from test_mission.nodes.gnc_n_node import GNCNNode
from test_mission.nodes.tc_node import TelemetryAndControlNode

def main() -> None: 
    exec_ = FSExecutive()
    
    # Custom mission nodes
    exec_.register_node(TelemetryAndControlNode())
    exec_.register_node(AutomatedFLightManagerNode())
    exec_.register_node(GNCCNode())
    exec_.register_node(GNCGNode())
    exec_.register_node(GNCNNode())

    exec_.start()

if __name__ == "__main__":
    main()
