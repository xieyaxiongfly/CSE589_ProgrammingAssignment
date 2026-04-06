import sys

from simulator.config import *


class Event:

    def __init__(self, time_stamp, event_type, sim, arg1 = -1, arg2 = -1, arg3 = -1):
        self.time_stamp = time_stamp
        self.event_type = event_type
        self.sim = sim
        self.serial = None

        self.arg1 = arg1
        self.arg2 = arg2
        self.arg3 = arg3

    def __lt__(self, other):
        if self.time_stamp != other.time_stamp:
            return self.time_stamp < other.time_stamp

        self_send_link = self.event_type == EVENT_TYPE.SEND_LINK
        other_send_link = other.event_type == EVENT_TYPE.SEND_LINK
        if self_send_link != other_send_link:
            return self_send_link

        return self.serial < other.serial

    def __str__(self):
        args = ""
        if self.arg1 != -1:
            args += " " + str(self.arg1)
        if self.arg2 != -1:
            args += " " + str(self.arg2)
        if self.arg3 != -1:
            args += " " + str(self.arg3)

        return "Time_Stamp: " + str(self.time_stamp) + " Event_Type: " + self.event_type + args

    # Event types that are visible to the user (shown with a banner)
    _USER_EVENTS = {
        EVENT_TYPE.PRINT, EVENT_TYPE.DUMP_NODE, EVENT_TYPE.DUMP_SIM,
        EVENT_TYPE.DRAW_TOPOLOGY, EVENT_TYPE.DRAW_PATH, EVENT_TYPE.DRAW_TREE,
        EVENT_TYPE.ADD_NODE, EVENT_TYPE.ADD_LINK, EVENT_TYPE.CHANGE_LINK,
        EVENT_TYPE.DELETE_NODE, EVENT_TYPE.DELETE_LINK,
    }

    def _banner(self):
        label = self.event_type
        if self.arg1 != -1:
            label += " " + str(self.arg1)
        if self.arg2 != -1:
            label += " " + str(self.arg2)
        if self.arg3 != -1:
            label += " " + str(self.arg3)
        print("\n[T=%-6d] %s" % (self.time_stamp, label))

    def dispatch(self):
        if self.event_type in Event._USER_EVENTS:
            self._banner()

        _STRUCTURAL_EVENTS = {
            EVENT_TYPE.ADD_NODE, EVENT_TYPE.ADD_LINK, EVENT_TYPE.CHANGE_LINK,
            EVENT_TYPE.DELETE_NODE, EVENT_TYPE.DELETE_LINK,
        }

        if self.event_type == EVENT_TYPE.ADD_NODE:
            self.sim.add_node(self.arg1)
        elif self.event_type == EVENT_TYPE.ADD_LINK:
            self.sim.add_link(self.arg1, self.arg2, self.arg3)
        elif self.event_type == EVENT_TYPE.CHANGE_LINK:
            self.sim.change_link(self.arg1, self.arg2, self. arg3)
        elif self.event_type == EVENT_TYPE.DELETE_LINK:
            self.sim.delete_link(self.arg1, self.arg2)
        elif self.event_type == EVENT_TYPE.DELETE_NODE:
            self.sim.delete_node(self.arg1)

        if self.event_type in _STRUCTURAL_EVENTS:
            self.sim.trace_event(
                self.time_stamp,
                self.event_type,
                [a for a in [self.arg1, self.arg2, self.arg3] if a != -1]
            )

        if self.event_type == EVENT_TYPE.PRINT:
            self.sim.print_comment(self.arg1)
        elif self.event_type == EVENT_TYPE.DUMP_NODE:
            self.sim.dump_node(self.arg1)
        elif self.event_type == EVENT_TYPE.DRAW_TOPOLOGY:
            self.sim.draw_topology()
        elif self.event_type == EVENT_TYPE.ROUTING_MESSAGE_ARRIVAL:
            self.sim.routing_message_arrival(self.arg1, self.arg2)
        elif self.event_type == EVENT_TYPE.DUMP_SIM:
            self.sim.dump_sim()
        elif self.event_type == EVENT_TYPE.DRAW_PATH:
            self.sim.draw_path(self.arg1, self.arg2)
        elif self.event_type == EVENT_TYPE.DRAW_TREE:
            self.sim.draw_tree(self.arg1)
        elif self.event_type == EVENT_TYPE.SEND_LINK:
            self.sim.send_link(self.arg1, self.arg2, self.arg3)
        else:
            pass
            # sys.stderr.write("Unknown event type %s" % self.event_type)
            # sys.exit(-1)
