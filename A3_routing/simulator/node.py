import logging

class Node:
    def __init__(self, id):
        self.id = id
        self.neighbors = []
        self.logging = logging.getLogger('Node %d' % self.id)

    def __str__(self):
        pass

    def link_has_been_updated(self, neighbor, latency):
        pass

    def process_incoming_routing_message(self, m: str):
        pass

    def get_next_hop(self, destination):
        pass

    def get_routing_table(self):
        pass

    def send_to_neighbors(self, message: str):
        from simulator.topology import Send_To_Neighbors
        Send_To_Neighbors(self, message)

    def send_to_neighbor(self, neighbor, message: str):
        from simulator.topology import Send_To_Neighbor
        Send_To_Neighbor(self, neighbor, message)

    def get_time(self):
        from simulator.topology import Get_Time
        return Get_Time()


class Link:
    def __init__(self, node1, node2, latency):
        self.node1 = node1
        self.node2 = node2
        self.latency = latency

    def __str__(self):
        return "Link: " + str(self.node1) + " " + str(self.node2) + " Latency: " + str(self.latency) + "\n"

