from simulator.node import Node


class Distance_Vector_Node(Node):

    def __init__(self, id):
        super().__init__(id)
        # Add your own instance variables here if needed.

    def __str__(self):
        # Return a human-readable string describing this node's current state
        # (e.g., routing table, distance vector). Used for debugging output.
        return f"Node {self.id}"

    def link_has_been_updated(self, neighbor, latency):
        """
        Called by the simulator whenever a direct link to a neighbor changes.

        Parameters:
            neighbor (int): The ID of the neighboring node.
            latency (int): The new latency (cost) of the link.
                           A value of -1 means the link has been deleted.

        You should update your local link information, recompute your distance
        vector using the Bellman-Ford equation, and send updated routing
        messages to your neighbors if your distance vector has changed.
        """
        pass

    def process_incoming_routing_message(self, m):
        """
        Called by the simulator when a routing message arrives from a neighbor.

        Parameters:
            m (str): The message string sent by a neighboring node.
                     You decide the format — it must match what you send.

        You should parse the message, update your knowledge of the neighbor's
        distance vector, recompute your own distance vector, and propagate
        updates to your neighbors if anything changed.
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
