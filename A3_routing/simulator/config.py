from generic_node import Generic_Node
from distance_vector_node import Distance_Vector_Node
from distance_vector_split_horizon_node import Distance_Vector_Split_Horizon_Node
from link_state_node import Link_State_Node

ROUTE_ALGORITHM = [
    "GENERIC",
    "DV",
    "DISTANCE_VECTOR",
    "DV_SH",
    "DISTANCE_VECTOR_SPLIT_HORIZON",
    "LS",
    "LINK_STATE"
]


ROUTE_ALGORITHM_NODE = {
    "GENERIC" : Generic_Node,
    "DV" : Distance_Vector_Node,
    "DISTANCE_VECTOR" : Distance_Vector_Node,
    "DV_SH" : Distance_Vector_Split_Horizon_Node,
    "DISTANCE_VECTOR_SPLIT_HORIZON" : Distance_Vector_Split_Horizon_Node,
    "LS" : Link_State_Node,
    "LINK_STATE" : Link_State_Node
}

class EVENT_TYPE:
    ADD_NODE = "ADD_NODE"
    ADD_LINK = "ADD_LINK"

    DELETE_NODE = "DELETE_NODE"
    DELETE_LINK = "DELETE_LINK"

    CHANGE_LINK = "CHANGE_LINK"

    PRINT = "PRINT"
    DRAW_TOPOLOGY = "DRAW_TOPOLOGY"
    DRAW_PATH = "DRAW_PATH"
    DRAW_TREE = "DRAW_TREE"
    DUMP_NODE = "DUMP_NODE"
    DUMP_SIM = "DUMP_SIM"

    # Not for user
    ROUTING_MESSAGE_ARRIVAL = "ROUTING_MESSAGE_ARRIVAL"
    SEND_LINK = "SEND_LINK"


OUTPUT_PATH = "output/"

USAGE_STR = "usage: sim.py route_algorithm event\n" \
            "\troute_algorithm\t- {GENERIC DV DISTANCE_VECTOR DV_SH DISTANCE_VECTOR_SPLIT_HORIZON LS LINK_STATE}\n" \
            "\tevent\t\t\t- a .event file\n"


LOGGING_FORMAT = "[%(asctime)s][%(levelname)s] %(name)s: %(message)s"

LOGGING_DATAFMT = '%Y-%m-%d %H:%M:%S'
