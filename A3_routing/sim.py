import sys
import logging
import time

from simulator.config import *
from simulator.topology import Topology, Get_Time
from simulator.event_queue import Event_Queue
from simulator.tracer import Tracer
from simulator import web_server


class Sim(Topology):

    def __init__(self, algorithm, event_file, trace=False):
        Tracer.enabled = trace
        Tracer.reset()
        super().__init__(algorithm, step='NO_STOP', draw=False)
        self.load_command_file(event_file)
        self.dispatch_event()
        self.logging.info("Total messages sent: %d" % self.message_count)
        self._print_stats()
        if trace:
            self._save_trace_artifacts()

    def __str__(self):
        ans = "==== Print Topology ====\n"
        ans += super().__str__()
        ans += "==== Print Event ====\n"
        ans += Event_Queue.Str()
        return ans

    def _print_stats(self):
        total = self.pass_count + self.fail_count
        sep = "=" * 50
        lines = [
            sep,
            "  Simulation Statistics",
            sep,
            f"  Messages sent : {self.message_count}",
        ]
        if total > 0:
            result = "ALL PASS" if self.fail_count == 0 else f"{self.fail_count} FAILED"
            lines.append(f"  Checks        : {self.pass_count}/{total} passed  ({result})")
        else:
            lines.append("  Checks        : none")
        lines.append(sep)
        print("\n" + "\n".join(lines) + "\n")

    def dump_sim(self):
        self.logging.info("DUMP_SIM at Time %d\n" % Get_Time() + str(self))

    def _save_trace_artifacts(self):
        Tracer.save("output/trace.json")
        viz_path = "output/visualizer.html"
        try:
            import os
            template = os.path.join(os.path.dirname(__file__), 'visualizer', 'index.html')
            with open(template) as f:
                html = f.read()
            with open("output/trace.json") as f:
                data = f.read()
            with open(viz_path, 'w') as f:
                f.write(html.replace('"__TRACE_DATA__"', data))
            self.logging.info("Visualizer saved: %s" % viz_path)
        except Exception as e:
            self.logging.warning("Could not save visualizer: %s" % e)

    def dispatch_event(self):
        e = Event_Queue.Get_Earliest()
        while e:
            e.dispatch()
            e = Event_Queue.Get_Earliest()

    def print_comment(self, comment):
        self.logging.info('Time: %d, Comment: %s' % (Get_Time(), comment))
        Tracer.record_print(Get_Time(), comment, self.get_snapshot())


def main():
    args = sys.argv[1:]

    viz = '--viz' in args
    trace = '--trace' in args or viz
    args = [a for a in args if a not in ('--viz', '--trace')]

    if len(args) != 2 or args[0] not in ROUTE_ALGORITHM:
        sys.stderr.write("usage: sim.py route_algorithm event [--trace] [--viz]\n"
                         "\troute_algorithm — {%s}\n"
                         "\tevent           — a .event file\n"
                         "\t--trace         — record trace.json and visualizer.html without opening the browser\n"
                         "\t--viz           — open web visualizer after simulation\n"
                         % " ".join(ROUTE_ALGORITHM))
        sys.exit(-1)

    if not viz:
        s = Sim(args[0], args[1], trace=trace)
        logging.getLogger('Sim').info("Simulation complete.")
        return

    port = web_server.start()
    web_server.open_browser(port)
    logging.getLogger('Sim').info("Visualizer: http://localhost:%d" % port)

    s = Sim(args[0], args[1], trace=True)

    web_server.mark_done()
    logging.getLogger('Sim').info(
        "Simulation complete — visualizer still running at http://localhost:%d  (Ctrl+C to exit)" % port
    )
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nExiting.")


if __name__ == '__main__':
    # Try: python sim.py GENERIC demo.event
    # Change logging level from DEBUG to INFO or WARNING, if DEBUG information bothers you
    logging.basicConfig(level=logging.INFO, format=LOGGING_FORMAT, datefmt=LOGGING_DATAFMT)
    main()
