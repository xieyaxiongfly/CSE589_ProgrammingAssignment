import sys
import logging
import traceback
import time
import networkx as nx
import matplotlib.pyplot as plt

from simulator.config import *
from simulator.event import Event
from simulator.event_queue import Event_Queue
from simulator.tracer import Tracer


class Topology:

    Nodes = {}
    this = None

    def __init__(self, algorithm, step='NORMAL', draw=True):
        Event_Queue.Reset()
        self.__g = nx.Graph()
        self.node_cls = ROUTE_ALGORITHM_NODE[algorithm]
        self.step = step
        self.draw = draw
        self.logging = logging.getLogger('Sim')
        self.position = None
        self.message_count = 0
        self.print_count = 0
        self.pass_count = 0
        self.fail_count = 0
        Topology.Nodes = {}
        Topology.this = self

    def __str__(self):
        ans = ""
        for node in self.__g.nodes:
            ans += "node " + str(node) + ": "
            ans += str(self.__g[node])
            ans += "\n"
        return ans

    def get_snapshot(self):
        nodes = list(self.__g.nodes)
        edges = [{"from": u, "to": v, "latency": self.__g[u][v]["latency"]} for u, v in self.__g.edges]
        node_details = {}
        for node in nodes:
            if node in Topology.Nodes:
                node_details[node] = str(Topology.Nodes[node])

        positions = {}
        if len(nodes) == 1:
            positions = {nodes[0]: {"x": 0.0, "y": 0.0}}
        elif len(nodes) >= 2:
            try:
                # kamada_kawai minimises edge crossings — best for small graphs
                pos = nx.kamada_kawai_layout(self.__g, weight=None, scale=400)
            except Exception:
                # fallback: spring layout (handles disconnected graphs)
                pos = nx.spring_layout(self.__g, weight=None, scale=400, seed=42, iterations=500)
            positions = {n: {"x": float(p[0]), "y": float(p[1])} for n, p in pos.items()}

        return {
            "nodes": [{"id": n} for n in nodes],
            "edges": edges,
            "positions": positions,
            "node_details": node_details,
        }

    def trace_event(self, time, event_type, args):
        Tracer.record_topology_event(time, event_type, args, self.get_snapshot())

    def add_node(self, node):
        if node not in Topology.Nodes.keys():
            self.position = None
            Topology.Nodes[node] = self.node_cls(node)
        self.__g.add_node(node)

    def add_link(self, node1, node2, latency):
        if latency < 0:
            sys.stderr.write("Latency of a link cannot be negative.")
            sys.exit(-1)
        self.add_node(node1)
        self.add_node(node2)
        self.__g.add_edge(node1, node2, latency = latency)
        self.post_send_link(node1, node2, latency)
        self.post_send_link(node2, node1, latency)

    def change_link(self, node1, node2, latency):
        self.add_link(node1, node2, latency)

    def send_link(self, node, neighbor, latency):
        if node not in Topology.Nodes:
            return
        Topology.Nodes[node].link_has_been_updated(neighbor, latency)

    def post_send_link(self, node, neighbor, latency):
        Event_Queue.Post(
            Event(
                Get_Time(),
                EVENT_TYPE.SEND_LINK,
                self,
                node,
                neighbor,
                latency
            )
        )

    def delete_link(self, node1, node2):
        if (node1, node2) in self.__g.edges:
            self.__g.remove_edge(node1, node2)
            self.post_send_link(node1, node2, -1)
            self.post_send_link(node2, node1, -1)
        else:
            self.logging.warning("remove link (%d, %d) does not exit" % (node1, node2))

    def delete_node(self, node):
        if node in self.__g.nodes:
            for neighbor in list(self.__g[node].keys()):
                self.delete_link(node, neighbor)
            self.__g.remove_node(node)
            Topology.Nodes.pop(node)
            self.position = None
            self.logging.debug("node %d deleted at time %d" % (node, Get_Time()))
        else:
            self.logging.warning("remove node %d does not exit" % node)

    def dump_node(self, node):
        if (node in self.__g.nodes) and (node in Topology.Nodes.keys()):
            dump_str = str(Topology.Nodes[node])
            self.logging.info('DUMP_NODE: ' + dump_str)
            Tracer.record_dump_node(Get_Time(), node, dump_str, self.get_snapshot())
        else:
            self.logging.warning("node %d does not exit" % node)

    def send_to_neighbors(self, node, m):
        for neighbor in list(self.__g[node].keys()):
            self.send_to_neighbor(node, neighbor, m)

    def send_to_neighbor(self, node, neighbor, m):
        if (node, neighbor) not in self.__g.edges:
            return
        Event_Queue.Post(
            Event(
                Get_Time() + int(self.__g[node][neighbor]['latency']),
                EVENT_TYPE.ROUTING_MESSAGE_ARRIVAL,
                self,
                neighbor,
                m
            )
        )

    def routing_message_arrival(self, neighbor, m):
        self.message_count += 1
        if neighbor in self.__g.nodes:
            Topology.Nodes[neighbor].process_incoming_routing_message(m)

    def node_labels(self):
        return {node : str(node) for node in self.__g.nodes}

    def edge_labels(self):
        return {(node1, node2) : self.__g[node1][node2]['latency'] for node1, node2 in self.__g.edges}

    def draw_topology(self):
        if not self.draw:
            return
        if self.position == None:
            self.position = nx.spring_layout(self.__g)
        nx.draw_networkx_nodes(self.__g, self.position, node_size=600, node_color='b', alpha=0.7)
        nx.draw_networkx_labels(self.__g, self.position, labels=self.node_labels(), font_size=14, font_color='w')
        nx.draw_networkx_edges(self.__g, self.position, width=2, alpha=0.5)
        nx.draw_networkx_edge_labels(self.__g, self.position, edge_labels=self.edge_labels(), font_size=14)
        plt.axis('off')

        filename = 'Topo_' + time.strftime("%H_%M_%S", time.localtime()) + '_Count_' + str(self.print_count) + '_Time_' + str(Get_Time()) + '.png'
        self.print_count += 1
        plt.savefig(OUTPUT_PATH + filename) # call savefig before show
        plt.show()
        plt.close(OUTPUT_PATH + filename)
        self.wait()

    def get_correct_path(self, source, destination):
        try:
            shortest_path = nx.algorithms.shortest_path(self.__g, source=source, target=destination, weight='latency')
            shortest_length = nx.algorithms.shortest_path_length(self.__g, source=source, target=destination, weight='latency')
        except:
            self.logging.warning("No path from %d to %d, please correct event/topo file" % (source, destination))
            return None, float("inf")
        return shortest_path, shortest_length


    def get_correct_path_dict(self, source):
        try:
            shortest_paths = nx.algorithms.shortest_path(self.__g, source=source, weight='latency')
            shortest_lengths = nx.algorithms.shortest_path_length(self.__g, source=source, weight='latency')
        except:
            self.logging.warning("No Tree from %d, please correct event/topo file" % source)
            return None, float("inf")
        shortest_path_dict = {(source, k):v for (k,v) in shortest_paths.items() if source != k}
        shortest_length_dict = {(source, k):v for (k,v) in shortest_lengths.items() if source != k}
        return shortest_path_dict, shortest_length_dict


    def get_user_path(self, source, destination):
        path = [source]
        length = 0

        while destination not in path:
            next = Topology.Nodes[path[-1]].get_next_hop(destination)
            if next == None:
                self.logging.warning("Your algorithm cannot find a path from %d to %d. Output: %s." % (source, destination, str(path)))
                return [], float("inf")
            elif next == -1 or next not in self.__g.nodes or next in path:
                path.append(next)
                self.logging.warning(
                    "Your algorithm cannot find a path from %d to %d. Output: %s." % (source, destination, str(path)))
                return [], float("inf")
            elif (path[-1], next) not in self.__g.edges:
                self.logging.warning("Link from %d to %d does not exist, you cannot use it" % (path[-1], next))
                path.append(next)
                return [], float("inf")
            length += self.__g[path[-1]][next]['latency']
            path.append(next)
        return path, length


    def get_user_path_dict(self, source):
        path_dict, length_dict = {}, {}
        for d in self.__g.nodes:
            if d == source: continue
            path_dict[(source, d)], length_dict[(source, d)] = self.get_user_path(source, d)
        return path_dict, length_dict



    def draw_path(self, source, destination):
        if (source not in self.__g.nodes) or  (destination not in self.__g.nodes) or (source == destination):
            self.logging.warning("Parameters in DRAW_PATH are illegal.")
            return

        correct_path, correct_length = self.get_correct_path(source, destination)
        if correct_path == None:
            return

        user_path, user_length = self.get_user_path(source, destination)

        passed = (correct_length == user_length)
        if passed:
            self.pass_count += 1
        else:
            self.fail_count += 1
        print("correct_path: (length=%s) %s" % (correct_length, correct_path))
        print("student_path: (length=%s) %s" % (user_length, user_path))
        print("student's solution is %s!\n" % ("correct" if passed else "incorrect"))

        Tracer.record_draw_path(
            Get_Time(), source, destination,
            correct_path, correct_length,
            user_path, user_length,
            self.get_snapshot()
        )

        red_nodes = [source, destination]
        blue_nodes = list(self.__g.nodes)
        for node in red_nodes:
            blue_nodes.remove(node)

        correct_edges = set([(correct_path[i], correct_path[i+1]) for i in range(len(correct_path)-1)])
        user_edges = set([(user_path[i], user_path[i+1]) for i in range(len(user_path)-1)])

        self.draw_in_networkx(red_nodes, blue_nodes, correct_edges, user_edges)



    def draw_tree(self, source):
        if source not in self.__g.nodes:
            self.logging.warning("Parameter in DRAW_TREE is illegal.")
            return

        correct_path_dict, correct_length_dict = self.get_correct_path_dict(source)
        if correct_path_dict == None:
            return

        user_path_dict, user_length_dict = self.get_user_path_dict(source)

        print("checking all paths starting from Node #%d..." % source)
        paths_for_tracer = []
        for (k, v) in correct_path_dict.items():
            dest = k[1]
            c_len = correct_length_dict[k]
            s_path = user_path_dict.get(k, [])
            s_len = user_length_dict.get(k, float("inf"))
            is_correct = (c_len == s_len)
            if not is_correct:
                print("from %s to %s:" % (k[0], dest))
                print("correct_path: (length=%s) %s" % (c_len, v))
                print("student_path: (length=%s) %s" % (s_len, s_path))
            paths_for_tracer.append({
                "from": k[0],
                "to": dest,
                "correct_path": v,
                "correct_length": c_len if c_len != float("inf") else -1,
                "student_path": s_path,
                "student_length": s_len if s_len != float("inf") else -1,
                "is_correct": is_correct,
            })
        tree_passed = (correct_length_dict == user_length_dict)
        for k in correct_path_dict:
            c_len = correct_length_dict[k]
            s_len = user_length_dict.get(k, float("inf"))
            if c_len == s_len:
                self.pass_count += 1
            else:
                self.fail_count += 1
        print("student's solution is %s!\n" % ("correct" if tree_passed else "incorrect"))

        Tracer.record_draw_tree(Get_Time(), source, paths_for_tracer, self.get_snapshot())

        red_nodes = [source]
        blue_nodes = list(self.__g.nodes)
        blue_nodes.remove(source)

        correct_edges, user_edges = set(), set()
        for (k,v) in correct_path_dict.items():
            correct_edges |= set([(v[i], v[i+1]) for i in range(len(v)-1)])
        for (k,v) in user_path_dict.items():
            user_edges |= set([(v[i], v[i+1]) for i in range(len(v)-1)])

        self.draw_in_networkx(red_nodes, blue_nodes, correct_edges, user_edges)

    def draw_in_networkx(self, red_nodes, blue_nodes, correct_path, user_path):
        if not self.draw:
            return
        if self.position == None:
            self.position = nx.spring_layout(self.__g)
            
        nx.draw_networkx_nodes(self.__g, self.position, nodelist=blue_nodes, node_size=600, node_color='b', alpha=0.7)
        nx.draw_networkx_nodes(self.__g, self.position, nodelist=red_nodes, node_size=700, node_color='r', alpha=0.6)
        nx.draw_networkx_labels(self.__g, self.position, labels=self.node_labels(), font_size=14, font_color='w')

        nx.draw_networkx_edges(self.__g, self.position, width=2, alpha=0.5)
        if user_path != None:
            nx.draw_networkx_edges(self.__g, self.position, edgelist=user_path, width=6, edge_color='r', alpha=0.4)
        nx.draw_networkx_edges(self.__g, self.position, edgelist=correct_path, width=3, edge_color='g', alpha=0.8)
        nx.draw_networkx_edge_labels(self.__g, self.position, edge_labels=self.edge_labels(), font_size=14)
        plt.axis('off')

        filename = 'Topo_' + time.strftime("%H_%M_%S", time.localtime()) + '_Count_' + str(self.print_count) + '_Time_' + str(Get_Time()) + '.png'
        self.print_count += 1
        plt.savefig(OUTPUT_PATH + filename)  # call savefig before show
        plt.show()
        plt.close(OUTPUT_PATH + filename)
        self.wait()

    def wait(self):
        if self.step == 'NO_STOP':
            return
        input('Press Enter to Continue...')

    def load_command_file(self, file):
        try:
            f = open(file)
            for line in f.readlines():
                line = line.strip()
                if line == "" or line[0] == '#':
                    continue

                items = line.split(' ')
                time_stamp = int(items[0])
                event_type = items[1]

                num_args = len(items) - 2
                if event_type == EVENT_TYPE.PRINT:
                    Event_Queue.Post(Event(time_stamp, event_type, self, "".join(items[2:])))
                elif num_args < 0 or num_args > 3:
                    sys.stderr.write(line)
                    raise BufferError
                elif num_args == 0:
                    Event_Queue.Post(Event(time_stamp, event_type, self))
                elif num_args == 1:
                    Event_Queue.Post(Event(time_stamp, event_type, self, int(items[2])))
                elif num_args == 2:
                    Event_Queue.Post(Event(time_stamp, event_type, self, int(items[2]), int(items[3])))
                elif num_args == 3:
                    Event_Queue.Post(Event(time_stamp, event_type, self, int(items[2]), int(items[3]), int(items[4])))
            f.close()

        except IOError as e:
            print("Can not open file " + file)
            print(e)
            sys.exit(-1)

        except BufferError:
            print("File with wrong format " + file)
            sys.exit(-1)

        except Exception as e:
            print("File with wrong format " + file)
            print(e)
            traceback.print_exc()
            sys.exit(-1)


def Send_To_Neighbors(node, m):
    Topology.this.send_to_neighbors(node.id, m)

def Send_To_Neighbor(node, neighbor, m):
    Topology.this.send_to_neighbor(node.id, neighbor, m)

def Get_Time():
    return Event_Queue.Current_Time
