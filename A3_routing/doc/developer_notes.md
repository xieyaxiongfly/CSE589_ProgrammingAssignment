# Developer notes

These notes are for developers of the simulator (not for students).

### Different from C++ version:
- Graph is undirected graph
    - Thus: we do not need to add link (2, 1) after add link (1, 2)
- Remove useless parameters
    1. Remove "bandwidth" and "latency" from a node
        - 0 ADD_NODE 1 1 1 -> 0 ADD_NODE 1 // as well as DELETE_NODE
    2. Remove "bandwidth" from a link
        - 0 ADD_LINK 1 2 10 10 -> 0 ADD_LINK 1 2 10  // as well as CHANGE_LINK. DELETE_LINK only has two parameters.
- Remove some not interested commands
~~1. DRAW_TREE [ID] . Since I think after implementing DRAW_PATH, we can see if it is easy to implemented in~~
    
- Remove useless function
    1. ~~Remove "SendToNeighbor" function, only "SendToNeighbors" is useful.~~
    1.1. I add "send to neighbor" function back. We can use it to confuse students. ( •̀ ω •́ )y
    2. Remove "GetNeighbors" function. Node can only know their neighbors by "link_has_been_updated"
       
- Remove send_current_links() function
    - There is a logic bug in Minet Add_Link Logic, since it reused in both topo file and event file
    - There for, call Add_link in runtime will not call link_has_been_updated
    - Change:
        - remove send_current_links() function after load topology
        - Call link_has_been_updated after Add_Link
    - However, it will introduce a bug in send_to_neighors(). Because we many add many links in one seconds. And call simulator does not know correct neighbor set in the middle.
    - Solution:
        - Introduce a "SEND_LINK" event
        - Post two "SEND_LINK" event afters process ADD_LINK
        - Change cmp function of Event, "SEND_LINK" will run lastest at that second. 
- .topo files are eliminated.  Instead, just put the topology definition at the beginning of the .event file.

### Question
- If message arrive time = message send time + latency, a problem comes
    - suppose latency A to B is 100, A send message 1 at time 0, and will arrive at time 100
    - however, a link change is called at time 10, latency updated to 20
    - A send message 2 at time 20
    - message 2 should arrive at time 40
    - Then, how about message 1? arrive at 100 or at 40, or at 30?
    - In minet, it set to 100

### step options:
    0. NORMAL
        only stop when a picture is 
    1. SINGLE_STEP
        stop after an event
    2. NO_STOP
        no stop at all

### Log Level
    0. logging.DEBUG (recommand when debugging)
    1. logging.INFO (default)
    2. Logging.WARNING 

### Layout options for graph
    - spring_layout (default)
    - https://networkx.github.io/documentation/stable/reference/drawing.html#layout