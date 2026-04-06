# Codebase Reference

This document describes every source file in the simulator. Files marked **[TO IMPLEMENT]** contain empty or stub method bodies that students must fill in. All other files are part of the simulator framework and should not be modified.

---

## Files Students Must Implement

### `distance_vector_node.py` — **[TO IMPLEMENT]**

Contains the `Distance_Vector_Node` class. Students implement the basic Bellman-Ford distance vector protocol here.

The three methods to implement are:

```python
def link_has_been_updated(self, neighbor, latency):
    # Called when a direct link is added, changed, or removed.
    # latency == -1 means the link was deleted.
    # You should update your local link table and recompute routes.
    # If the network state changed, advertise your new distance vector
    # to all neighbors.
    pass

def process_incoming_routing_message(self, m: str):
    # Called when a routing message string 'm' arrives from another node.
    # Parse the message, update your neighbor's advertised vector,
    # recompute routes, and propagate updates if necessary.
    pass

def get_next_hop(self, destination):
    # Return the ID of the next-hop neighbor toward 'destination'.
    # Return -1 if the destination is unreachable.
    pass
```

Key design decisions students need to make:
- How to encode/decode routing messages (e.g. JSON)
- How to handle the counting-to-infinity problem
- When to send updates (only on change vs. periodic)
- How to represent infinity for unreachable destinations

---

### `distance_vector_split_horizon_node.py` — **[TO IMPLEMENT]**

Contains the `Distance_Vector_Split_Horizon_Node` class. Same interface as above, but the implementation must add **split horizon with poisoned reverse** to suppress routing loops.

With poisoned reverse: when advertising to neighbor `N`, any route that goes *through* `N` must be advertised back to `N` with cost = ∞ instead of the true cost. This prevents `N` from thinking it can reach that destination via this node, which would create a loop.

---

## Simulator Framework (Do Not Modify)

### `simulator/node.py`

Defines the `Node` base class that all node implementations inherit from.

**Public interface available to students:**

| Method | Description |
|--------|-------------|
| `self.id` | This node's integer identifier |
| `self.send_to_neighbors(msg)` | Broadcast string `msg` to all directly connected neighbors. The message arrives at each neighbor after a delay equal to the link's cost. |
| `self.send_to_neighbor(neighbor, msg)` | Send string `msg` to one specific neighbor. |
| `self.get_time()` | Return the current simulation time as an integer. |
| `self.logging` | A Python `logging.Logger` instance. Use `self.logging.debug(...)` or `self.logging.info(...)` for debug output. |

`send_to_neighbor` and `send_to_neighbors` are fully implemented in `node.py` — students do not need to implement them. They work by delegating through a chain: `Node.send_to_neighbor()` → `topology.Send_To_Neighbor()` → `Topology.send_to_neighbor()`, which posts a `ROUTING_MESSAGE_ARRIVAL` event scheduled at `current_time + link_latency`. When that event fires, the simulator calls `process_incoming_routing_message()` on the destination node.

Also defines the `Link` data class (node1, node2, latency) used internally by the topology.

---

### `simulator/topology.py`

The core of the simulator. The `Topology` class owns the network graph (via `networkx`) and is responsible for:

- **Maintaining the graph** — `add_node`, `add_link`, `change_link`, `delete_link`, `delete_node` all modify the internal `networkx.Graph` and schedule `SEND_LINK` events so affected nodes are notified via `link_has_been_updated()`.
- **Routing message delivery** — `send_to_neighbor(node, neighbor, msg)` schedules a `ROUTING_MESSAGE_ARRIVAL` event at time `current_time + link_latency`. When that event fires, `process_incoming_routing_message()` is called on the destination node. This is how link cost doubles as message propagation delay.
- **Grading** — `draw_path(src, dst)` and `draw_tree(src)` evaluate student routing tables:
  - The correct answer is computed by `networkx.shortest_path` (Dijkstra with `weight='latency'`).
  - The student's answer is reconstructed by repeatedly calling `get_next_hop()` starting from `src` until `dst` is reached (or a loop/dead-end is detected).
  - Grading is based on **total path cost**, not the exact sequence of hops. Two different valid shortest paths with equal cost both pass.
  - Each passing pair increments `pass_count`; each failing pair increments `fail_count`.
- **Snapshot** — `get_snapshot()` returns a JSON-serializable dict of the current graph state (nodes, edges with latencies, node positions, and each node's internal string representation). Used by the tracer.

**Module-level helpers** (called by `Node` methods internally):

```python
Send_To_Neighbors(node, msg)   # delegates to Topology.this.send_to_neighbors
Send_To_Neighbor(node, nb, msg) # delegates to Topology.this.send_to_neighbor
Get_Time()                      # returns Event_Queue.Current_Time
```

---

### `simulator/event_queue.py`

A global min-heap priority queue that drives simulation time.

| Method | Description |
|--------|-------------|
| `Event_Queue.Post(e)` | Insert event `e` into the heap. |
| `Event_Queue.Get_Earliest()` | Pop and return the earliest event; advances `Current_Time` to that event's timestamp. Returns `None` when the queue is empty. |
| `Event_Queue.Current_Time` | The current simulation time (integer). |
| `Event_Queue.Reset()` | Clear the queue and reset time to 0. Called at the start of each simulation. |

At equal timestamps, `SEND_LINK` events (topology notifications to nodes) are dispatched before `ROUTING_MESSAGE_ARRIVAL` events. Within the same type and timestamp, events are ordered by insertion order (FIFO via a serial counter).

---

### `simulator/event.py`

The `Event` class represents a single scheduled action.

Each event stores: `time_stamp`, `event_type` (a string constant from `EVENT_TYPE`), a reference to `sim` (the `Topology` instance), and up to three integer arguments (`arg1`, `arg2`, `arg3`).

`event.dispatch()` reads the event type and calls the appropriate method on `sim`. User-visible events (`ADD_LINK`, `DRAW_PATH`, etc.) also print a banner line like `[T=500   ] DRAW_TREE 0` to stdout before dispatching.

---

### `simulator/config.py`

Centralizes two things:

1. **Algorithm registration** — Maps short names (`DV`, `DV_SH`, `LS`, `GENERIC`) and their long aliases to the corresponding node class. To add a new algorithm, register it here.

2. **`EVENT_TYPE` constants** — String constants for every event type used throughout the simulator. Using constants instead of raw strings prevents typos from causing silent failures.

---

### `simulator/tracer.py`

Records a sequence of "frames" when tracing is enabled (`--trace` or `--viz`). Each frame is a dict capturing:

- The simulation time
- What happened (topology change, message, draw check, dump, print)
- A full snapshot of the network graph at that moment (nodes, edges, positions, node internals)

Frames are accumulated in memory during the simulation and written to `output/trace.json` at the end. The visualizer reads this file to replay the simulation step by step.

`Tracer.enabled` is `False` by default; the `Sim` constructor sets it to `True` when `--trace` or `--viz` is passed.

---

### `simulator/web_server.py`

A minimal HTTP server (stdlib `http.server`) used by `--viz` mode.

- Starts on a random free port in a background daemon thread.
- Serves `GET /` → the visualizer HTML page (with `LIVE_MODE = true` injected so the page polls for data instead of reading embedded JSON).
- Serves `GET /api/frames` → the current trace frames as JSON, plus a `"done"` flag so the browser knows when the simulation has finished.
- `mark_done()` is called after the simulation completes; the browser stops polling once it sees `"done": true`.

---

### `generic_node.py`

A minimal reference node (`Generic_Node`) used with the `GENERIC` algorithm. It does not implement any real routing protocol — `get_next_hop` always returns the first neighbor. Its purpose is to let you verify the simulator infrastructure works before you start implementing your own node.

---

### `sim.py`

The main entry point. Parses command-line arguments, then constructs a `Sim` instance (which inherits from `Topology`) that:

1. Loads the `.event` file into the event queue.
2. Drains the event queue by repeatedly calling `Event_Queue.Get_Earliest()` and dispatching each event.
3. Prints the final statistics block (messages sent, checks passed/failed).
4. If tracing is enabled, saves `output/trace.json` and embeds the trace into `output/visualizer.html`.
5. If `--viz` was passed, starts `web_server` before running the simulation and keeps the process alive after it finishes so the browser can browse the replay.

---

### `run_tests.py`

A batch test runner. Discovers all `.event` files in the given paths, runs each one as a subprocess (`python sim.py ALGORITHM file.event`), parses the stdout/stderr for pass/fail verdicts and message counts, and prints a summary table. Full per-check detail is written to `output/test_results_<ALGORITHM>.txt`. Exit code is 0 if all checks pass, 1 otherwise.

---

### `link_state_node.py`

A complete reference implementation of the Link State protocol using Dijkstra's algorithm. Provided for reference — students are **not** required to implement this file.

The implementation uses:
- A **Link State Database (LSDB)** — each node stores the most recently seen LSP (link-state packet) from every other node it has heard from, keyed by `{origin: {seq, links}}`.
- **Sequence numbers** — every LSP carries a monotonically increasing sequence number. A received LSP is discarded if its sequence number is not newer than what is already in the LSDB, preventing loops and duplicate flooding.
- **Flooding** — when a new LSP is accepted, it is forwarded to all neighbors except the one it arrived from.
- **Dijkstra** — run locally on the full LSDB graph after every update to compute `routing_table` (next hops) and `path_costs`.
