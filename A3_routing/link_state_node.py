from simulator.node import Node


class Link_State_Node(Node):

    def __init__(self, id):
        super().__init__(id)
        # Add your own instance variables here if needed.

    def __str__(self):
        # Return a human-readable string describing this node's current state
        # (e.g., link-state database, routing table). Used for debugging output.
        return f"Node {self.id}"

    def link_has_been_updated(self, neighbor, latency):
        """
        Called by the simulator whenever a direct link to a neighbor changes.

        Parameters:
            neighbor (int): The ID of the neighboring node.
            latency (int): The new latency (cost) of the link.
                           A value of -1 means the link has been deleted.

        You should update your local link-state information, generate a new
        Link State Packet (LSP) with an incremented sequence number, and flood
        it to all neighbors so the entire network can update its link-state
        database. Then recompute your routing table using Dijkstra's algorithm.
        """
        pass

    def process_incoming_routing_message(self, m):
        """
        Called by the simulator when a routing message arrives from a neighbor.

        Parameters:
            m (str): The message string sent by a neighboring node.
                     You decide the format — it must match what you send.

        You should parse the LSP, check whether it is newer than what you
        already have (using the sequence number), store it in your link-state
        database, recompute your routing table, and flood the LSP out to all
        neighbors except the one it arrived from.
        """
        pass

    def get_next_hop(self, destination):
        """
        Called by the simulator to look up the next hop for a destination.

        Parameters:
            destination (int): The ID of the destination node.

        Returns:
            int: The ID of the neighboring node to forward to, or -1 if the
                 destination is unreachable.
        """
        pass
