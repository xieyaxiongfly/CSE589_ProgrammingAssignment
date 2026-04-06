import json
import os


class Tracer:
    enabled = False
    _frames = []

    @classmethod
    def reset(cls):
        cls._frames = []

    @classmethod
    def record_topology_event(cls, time, event_type, args, snapshot):
        if not cls.enabled:
            return
        cls._frames.append({
            "type": "topology_event",
            "time": time,
            "event_type": event_type,
            "args": args,
            "snapshot": snapshot,
        })

    @classmethod
    def record_print(cls, time, message, snapshot):
        if not cls.enabled:
            return
        cls._frames.append({
            "type": "print",
            "time": time,
            "message": message,
            "snapshot": snapshot,
        })

    @classmethod
    def record_dump_node(cls, time, node_id, dump_str, snapshot):
        if not cls.enabled:
            return
        cls._frames.append({
            "type": "dump_node",
            "time": time,
            "node_id": node_id,
            "dump_str": dump_str,
            "snapshot": snapshot,
        })

    @classmethod
    def record_draw_path(cls, time, source, dest, correct_path, correct_length,
                         student_path, student_length, snapshot):
        if not cls.enabled:
            return
        cls._frames.append({
            "type": "draw_path",
            "time": time,
            "source": source,
            "dest": dest,
            "correct_path": correct_path,
            "correct_length": correct_length if correct_length != float("inf") else -1,
            "student_path": student_path,
            "student_length": student_length if student_length != float("inf") else -1,
            "snapshot": snapshot,
        })

    @classmethod
    def record_draw_tree(cls, time, source, paths, snapshot):
        if not cls.enabled:
            return
        cls._frames.append({
            "type": "draw_tree",
            "time": time,
            "source": source,
            "paths": paths,
            "snapshot": snapshot,
        })

    @classmethod
    def save(cls, output_path):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            json.dump({"frames": cls._frames}, f)
