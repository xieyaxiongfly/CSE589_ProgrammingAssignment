# Routing Protocol Simulator

A Python-based network routing simulator for implementing and testing Distance Vector (DV) routing protocols. This simulator is built on top of the [Routesim2](https://github.com/howdym/routesim2) framework originally developed for Northwestern's EECS-340.

---

## Prerequisites

Python 3.6 or higher is required. Install the two required packages with:

```bash
pip install networkx
```

---

## Background: Split Horizon with Poisoned Reverse

Plain Distance Vector has a well-known failure mode called **count-to-infinity**. Consider:

```
A --1-- B --1-- C
```

After convergence, A reaches C with cost 2 via B. Now the B–C link is deleted:

1. B loses its direct route to C and looks for an alternative.
2. B sees A advertises cost 2 to C — but A's route **goes through B**!
3. B mistakenly computes cost `1 + 2 = 3` via A, and updates.
4. A then updates to `1 + 3 = 4`, B to 5, A to 6 … and so on until infinity.

The loop happens because B re-advertises a route back to the neighbor it learned that route from.

### The Fix

> When sending your distance vector to neighbor `v`, for every destination `y` whose current next hop is `v`, **report your cost to `y` as infinity**.

The reasoning: if I reach `y` through `v`, telling `v` that I can also reach `y` is misleading — it would just route traffic back through itself.

With poisoned reverse, after B–C is deleted, A reports `cost(A → C) = ∞` to B. B immediately sees no path to C and marks it unreachable. No counting loop.

> **Note:** This eliminates two-node loops but **does not fully prevent count-to-infinity in larger cycles** (e.g., a three-node loop). It is a practical improvement, not a complete solution.

### Key Implementation Difference from Plain DV

| | Plain DV | DV + Split Horizon / Poisoned Reverse |
|---|---|---|
| Message to neighbor `v` | Same DV broadcast to all neighbors | Customized per neighbor: next-hop-is-`v` destinations get cost ∞ |
| API | `send_to_neighbors(msg)` | Must use `send_to_neighbor(v, msg)` in a loop |

### Common Pitfalls

- **Poisoned Reverse only affects what you send.** Your internal distance vector always holds your true best-known cost; you only advertise ∞ outward to the relevant neighbor.
- **Do not use `send_to_neighbors`** — each neighbor receives a different message, so you must loop over neighbors and call `send_to_neighbor` individually.
- **Infinity representation** — use a clear constant (e.g., `float('inf')`) and make sure arithmetic on it (e.g., `inf + cost`) doesn't produce unexpected results.
- **Link deletion** (`latency == -1`) — remove the neighbor from your link table and recompute all routes before sending updates.

---

## What You Need to Implement

You are responsible for implementing the following two files. **Do not modify any other simulator files.**

| File | Class | Algorithm |
|------|-------|-----------|
| `distance_vector_node.py` | `Distance_Vector_Node` | Bellman-Ford / Distance Vector |
| `distance_vector_split_horizon_node.py` | `Distance_Vector_Split_Horizon_Node` | DV with Split Horizon + Poisoned Reverse |

Each class must inherit from `simulator.node.Node` and implement three methods:

```python
def link_has_been_updated(self, neighbor, latency):
    """
    Called by the simulator whenever a directly connected link changes.
    - latency > 0  : link to 'neighbor' was added or its cost changed
    - latency == -1: link to 'neighbor' was deleted
    """

def process_incoming_routing_message(self, m: str):
    """
    Called when a routing message 'm' arrives from another node.
    Parse it and update your routing table accordingly.
    """

def get_next_hop(self, destination):
    """
    Return the ID of the next-hop neighbor on the shortest path to
    'destination', or -1 if the destination is unreachable.
    """
```

### Helper methods available on every Node

```python
self.send_to_neighbors(message)          # broadcast to all direct neighbors
self.send_to_neighbor(neighbor, message) # unicast to one neighbor
self.get_time()                          # current simulator time (integer)
self.id                                  # this node's integer ID
self.logging                             # Python logger for debug output
```

---

## Running the Simulator

### Single event file

```
python sim.py <ALGORITHM> <event_file> [--viz]
```

| Argument | Values |
|----------|--------|
| `ALGORITHM` | `DV` / `DISTANCE_VECTOR` |
| | `DV_SH` / `DISTANCE_VECTOR_SPLIT_HORIZON` |
| | `GENERIC` (reference / sanity check) |
| `event_file` | Path to a `.event` file (e.g. `events/demo.event`) |
| `--viz` | Run the simulation, then **open an interactive web visualizer** in your browser |

**Examples:**

```bash
# Run the demo with Distance Vector
python sim.py DV events/demo.event

# Run Distance Vector and open the web visualizer
python sim.py DV events/demo.event --viz
```

### Batch test runner

```
python run_tests.py <ALGORITHM> [event_or_dir ...] [--timeout SECONDS]
```

Runs every `.event` file in the given paths (default: the entire `events/` directory) and prints a summary table. A full report is saved to `output/test_results_<ALGORITHM>.txt`.

**Examples:**

```bash
# Test DV against a single file
python run_tests.py DV events/demo.event

# Test DV_SH against the testing suite with a 120-second timeout per file
python run_tests.py DV_SH events/testing_suite/ --timeout 120
```

---

## Understanding the Output

### Pass / Fail verdict

Each `.event` file contains `DRAW_PATH` and/or `DRAW_TREE` commands. When the simulator executes one of these, it compares your node's `get_next_hop()` answers against the ground-truth shortest paths and prints a verdict for every source–destination pair:

```
correct_path: 0 -> 2 -> 4   length: 15
student_path: 0 -> 2 -> 4   length: 15
student's solution is correct!
```

or

```
correct_path: 0 -> 1 -> 3   length: 10
student_path: 0 -> 2 -> 3   length: 20
student's solution is incorrect!
```

At the end of each simulation run, a statistics block is printed:

```
==================================================
  Simulation Statistics
==================================================
  Messages sent : 42
  Checks        : 8/8 passed  (ALL PASS)
==================================================
```

If any check fails, the `Checks` line will read e.g. `5/8 passed  (3 FAILED)`.

### Batch runner output

`run_tests.py` prints a table like:

```
  File                                         Msgs    Checks  Result
  -------------------------------------------- ------  -------  ------
  events/testing_suite/case_1.event               38    4/4      PASS
  events/testing_suite/case_2.event               55    4/4      PASS
  events/adversarial_cases/island_node.event       12    2/2      PASS
  -------------------------------------------- ------  -------  ------
  TOTAL                                           105   10/10    ALL PASS
```

- **PASS** — every `DRAW_PATH` / `DRAW_TREE` check in the file was correct.
- **FAIL** — at least one check was wrong. Failed checks are printed below the table with the expected vs. actual paths.
- **NO CHECKS** — the file has no path checks (informational only).
- **TIMEOUT** — the simulation exceeded the time limit.

The full per-check detail is always written to `output/test_results_<ALGORITHM>.txt`.

---

## Web Visualizer

> **The visualizer is a debugging tool.** It records every event and network snapshot during the simulation, which adds overhead. Do not use `--viz` for performance measurement or batch testing — use `run_tests.py` instead.

Run a single simulation with `--viz` to open an interactive replay in your browser:

```bash
python sim.py DV events/demo.event --viz
```

A local HTTP server starts automatically and your browser opens to the trace. Press **Ctrl+C** to stop the server. A static copy of the trace is also saved to `output/visualizer.html` and can be opened later without the server.

### What you can do in the visualizer

- **Step through every event** using the arrow keys, Prev/Next buttons, or the progress bar. The graph updates live as the topology changes.
- **See pass/fail at a glance** — `DRAW_PATH` and `DRAW_TREE` events are badged correct/incorrect in the event log.
- **Compare correct vs. incorrect paths** — when a check fails, the graph splits into two side-by-side views: the ground-truth path on the left (green) and your implementation's path on the right (red for wrong hops, green for correct ones).
- **Inspect node state** — click any node to see its routing table / distance vector (whatever your `__str__()` returns) at that point in time.

---

## How the Simulator Works

### Event-driven simulation

The simulator advances through **discrete time steps** (integers). There is no real-time clock — time jumps directly from one scheduled event to the next. At each time step, all events scheduled for that moment are dispatched in order: topology changes are applied first, then routing messages that are in-flight arrive at their destinations.

When a topology event fires (e.g. a link is added or deleted), the simulator calls `link_has_been_updated()` on the affected nodes. Those nodes may then call `send_to_neighbor()` or `send_to_neighbors()`, which schedules new `ROUTING_MESSAGE_ARRIVAL` events at a future time equal to the current time plus the link latency. When that future time is reached, `process_incoming_routing_message()` is called on the receiving node, which may in turn send more messages — and so on, until the network converges and no more messages are in flight.

This means **time is the unit of convergence**. A scenario places topology changes early and check commands later, giving your protocol enough simulated time to exchange messages and reach a stable routing state before the result is evaluated.

### Event file format

An event file is a plain-text script that defines a network scenario. Each non-comment line has the form:

```
<time>  <COMMAND>  [arguments ...]
```

Lines are processed in ascending time order. A `#` anywhere on a line starts a comment.

### Network topology

The simulated network is an **undirected weighted graph**. Nodes represent routers and links represent bidirectional connections between them. Every link has a **cost** (also called **latency** in this simulator — the two terms are interchangeable). The cost of a link serves two roles simultaneously: it is the delay (in time units) that a routing message experiences when traveling across that link, and it is the edge weight used by shortest-path computation. Your routing protocol must find paths that minimize the total cost from source to destination.

### Topology commands

These commands modify the network and trigger `link_has_been_updated()` on the affected nodes.

| Command | Syntax | Description |
|---------|--------|-------------|
| `ADD_NODE` | `t ADD_NODE id` | Add a new isolated node with the given ID. |
| `ADD_LINK` | `t ADD_LINK id1 id2 cost` | Add a bidirectional link between two nodes with the given latency/cost. Creates nodes automatically if they do not exist. |
| `CHANGE_LINK` | `t CHANGE_LINK id1 id2 cost` | Change the cost of an existing link. |
| `DELETE_LINK` | `t DELETE_LINK id1 id2` | Remove the link between two nodes. Both nodes receive `link_has_been_updated(neighbor, -1)`. |
| `DELETE_NODE` | `t DELETE_NODE id` | Remove a node and all its links. |

### Check commands — convergence tests

These are the commands used to **grade your implementation**. They are always placed at a time well after the last topology change, so your protocol has had enough simulated time to converge.

#### `DRAW_PATH t id1 id2`

At time `t`, traces the path from `id1` to `id2` by repeatedly calling `get_next_hop()` starting at `id1`. The simulator compares the resulting path and total cost against the ground-truth shortest path computed by Dijkstra. A pass/fail verdict is printed for this pair:

```
correct_path: 0 -> 2 -> 4   length: 15
student_path: 0 -> 2 -> 4   length: 15
student's solution is correct!
```

#### `DRAW_TREE t id`

At time `t`, runs `DRAW_PATH` from node `id` to **every other node** in the network, building the full shortest-path tree rooted at `id`. Each destination produces its own pass/fail verdict, so a single `DRAW_TREE` command may contribute many checks to the final score.

```
from 0 to 1:
correct_path: 0 -> 1   length: 5
student_path: 0 -> 1   length: 5
student's solution is correct!

from 0 to 2:
correct_path: 0 -> 2   length: 8
student_path: 0 -> 3   length: 12
student's solution is incorrect!
```

### Diagnostic commands

These commands print information for debugging and do not affect the pass/fail count.

| Command | Syntax | Description |
|---------|--------|-------------|
| `DUMP_NODE` | `t DUMP_NODE id` | Print the internal state of node `id` (routing table, DV, etc.). |
| `DUMP_SIM` | `t DUMP_SIM` | Print the full topology and remaining event queue. |
| `PRINT` | `t PRINT "text"` | Print an arbitrary message — useful as a milestone marker in long scenarios. |

### Example event file

```
# Build a triangle network at t=0
0  ADD_LINK  0 1 5
0  ADD_LINK  1 2 3
0  ADD_LINK  0 2 20

# At t=500 the network should have converged — check all paths from node 0
500  DRAW_TREE  0

# At t=600 break the 0-1 link and give the network time to reconverge
600  DELETE_LINK  0 1
900  DRAW_TREE  0
```

Sample event files are provided in the `events/` directory.

---

## Project Structure

For a detailed explanation of what each file does, its interface, and its internal logic, see [doc/codebase.md](doc/codebase.md).

```
.
├── sim.py                                 # main entry point
├── run_tests.py                           # batch test runner
│
├── distance_vector_node.py                # ← implement this
├── distance_vector_split_horizon_node.py  # ← implement this
│
├── generic_node.py                        # reference node (do not modify)
├── link_state_node.py                     # reference LS implementation (do not modify)
│
├── simulator/
│   ├── node.py                            # Node base class & send helpers
│   ├── topology.py                        # network graph, grading, message delivery
│   ├── event.py                           # Event class & dispatch
│   ├── event_queue.py                     # min-heap priority queue, simulation clock
│   ├── config.py                          # algorithm registration & event type constants
│   ├── tracer.py                          # trace frame recorder (for visualizer)
│   └── web_server.py                      # local HTTP server for --viz mode
│
├── events/
│   ├── demo.event
│   ├── testing_suite/                     # graded test cases
│   └── adversarial_cases/                 # edge-case scenarios
│
├── doc/
│   └── codebase.md                        # per-file reference documentation
├── visualizer/                            # web visualizer front-end
└── output/                               # simulation results & logs
```
