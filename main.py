#!/usr/bin/env python3
# coding: utf-8

import json
import os
import signal
import sys
from datetime import datetime
from typing import List, Optional

import can

from canparser_generator import CanTopicParser


class CanIds:
    """
    Usage:
            schema = load_can_ids('can_ids.json')

            # Print each topic of each module:
            [print(module, topic)
             for topic in schema['modules'][module]['topics']
             for module in schema['modules']]

            # Access a specific topic of a specific module:
            parsed_id, parsed_signature = 33, 250
            module = schema['modules'].get(parsed_signature)
            topic = module['topics'].get(parsed_id)
            print(module['name'], topic['name'])
    """

    @staticmethod
    def load(filename: str) -> dict:
        with open(filename) as schema_file:
            schema = json.load(schema_file)

            modules = {}
            for module in schema["modules"]:
                topics = {}
                for topic in module["topics"]:
                    topics[topic["id"]] = topic
                modules[module["signature"]] = module
                module["topics"] = topics
            schema["modules"] = modules

            return schema


class Datasets:
    def __init__(
        self, datasets: list, input_path: str, output_path: Optional[str] = None
    ):
        from pandas import Timedelta

        if output_path is None:
            output_path = input_path

        self.datasets = datasets

        for d in self.datasets:
            if "from" in d and "to" in d:
                d["offset"] = d["to"] - d["from"]
            else:
                d["offset"] = Timedelta("0")
            d["input_path"] = input_path
            d["output_path"] = output_path

    def as_list(self):
        return self.datasets


class MovingAverage:
    def __init__(self, period):
        self.period = period
        self.data = {}

    def add(self, key: str, value: float):
        if key not in self.data:
            self.data[key] = []

        self.data[key].append(value)

        if len(self.data[key]) > self.period:
            self.data[key].pop(0)

    def average(self, key: str) -> float:
        if key not in self.data:
            return float("NaN")

        lenght = len(self.data[key])
        if lenght == 0:
            return float("NaN")

        return sum(self.data[key]) / lenght


def parse_payload(
    topic: dict,
    payload: bytearray,
    module_name: str,
    verbose: bool = False,
    warning: bool = True,
) -> Optional[List[dict]]:
    if verbose:
        print(f"{payload=}, {len(payload)=}")

    topic_parser = topic["parser"]
    expected_payload_length = topic_parser.size
    payload_length = len(payload)
    if payload_length != expected_payload_length:
        topic_name = topic["name"]
        if warning:
            print(
                f"Warning: wrong payload size from {topic_name=} from {module_name=}. "
                f"Expected: {expected_payload_length}, "
                f"got: {payload_length=} {payload=}."
            )
        return None

    parsed_payload = topic_parser.from_buffer(bytearray(payload)).as_dict()

    if verbose:
        print(f"{parsed_payload=}")

    payload_data_list = []
    for b, parsed_byte_name in enumerate(parsed_payload):
        parsed_byte_value = parsed_payload[parsed_byte_name]
        parsed_byte_units = topic["bytes"][b]["units"]

        parsed_byte_units, parsed_byte_value = CanTopicParser.apply_units(
            parsed_byte_units, parsed_byte_value
        )

        parsed_dict = {
            "byte_name": parsed_byte_name,
            "value": parsed_byte_value,
            "unit": parsed_byte_units,
        }
        payload_data_list += [parsed_dict]

        if verbose:
            print(f"{parsed_dict=}")

    return payload_data_list


def clear_terminal():
    os.system("cls" if os.name == "nt" else "clear")


def formatted_time(timestamp) -> str:
    return datetime.fromtimestamp(timestamp).strftime("%H:%M:%S.%f")[:-3]


def process_message(parsed: dict, verbose: bool = False) -> Optional[list]:
    """Returns a list containing each data from a topic as a dict"""
    parsed["signature"] = parsed["payload"][0]

    # Fixing BUGS related to wrong configs in some can modules
    if "version" not in schema.keys():
        if parsed["topic"] == 65:
            parsed["signature"] = 230
            # see https://github.com/ZeniteSolar/MAB20/issues/6
            parsed["payload"] = parsed["payload"][:2]
        elif parsed["topic"] == 64:
            parsed["signature"] = 230

    module = schema["modules"].get(parsed["signature"], None)
    if module is None:
        if verbose:
            print("module =", module, "parsed =", parsed, parsed["payload"])
        return None

    topic = module["topics"].get(parsed["topic"], None)
    if topic is None:
        if verbose:
            print("topic =", topic, "parsed =", parsed, parsed["payload"])
        return None

    parsed_data_dict_list = parse_payload(
        topic, parsed["payload"], module["name"], warning=False
    )
    if parsed_data_dict_list is None:
        if verbose:
            print(
                "parsed_data_dict_list =",
                parsed_data_dict_list,
                "parsed =",
                parsed,
                parsed["payload"],
            )
        return None

    parsed_data_dict_list = [
        dict(
            item,
            **{
                "timestamp": parsed["timestamp"],
                "module_name": module["name"],
                "topic_name": topic["name"],
            },
        )
        for item in parsed_data_dict_list
    ]

    return parsed_data_dict_list


if __name__ == "__main__":

    global schema

    schema = CanIds.load("can_ids.json")
    schema = CanTopicParser.generate_parsers(schema)

    boat_data = MovingAverage(10)

    bus = can.interface.Bus(bustype="socketcan", bitrate=500_000)  # type: ignore

    def int_handler(signum, frame):
        bus.shutdown()
        print("\nNicely terminated.")
        sys.exit(0)

    signal.signal(signal.SIGINT, int_handler)
    signal.signal(signal.SIGTERM, int_handler)

    print("Waiting for messages from CAN bus...")

    try:
        # Start receiving messages from the bus
        for message in bus:
            # Dispatch the received message to the custom parser
            parsed_topic = process_message(
                {
                    "timestamp": message.timestamp,
                    "topic": message.arbitration_id,
                    "payload": message.data,
                },
                verbose=False,
            )

            if not parsed_topic:
                continue

            key = ""
            value = 0
            for data in parsed_topic:
                if (
                    data["module_name"] == "MIC19"
                    and data["topic_name"] == "MOTOR"
                    and data["byte_name"] == "D"
                ):
                    key = "mot_D"
                    value = data["value"] * 100
                elif (
                    data["module_name"] == "MCS19"
                    and data["topic_name"] == "BAT"
                    and data["byte_name"] == "AVG"
                ):
                    key = "bat_V"
                    value = data["value"] * 1e-2
                elif (
                    data["module_name"] == "MSC19_4"
                    and data["topic_name"] == "ADC"
                    and data["byte_name"] == "AVG"
                ):
                    key = "bat_I_IN"
                    value = data["value"]
                elif (
                    data["module_name"] == "MSC19_5"
                    and data["topic_name"] == "ADC"
                    and data["byte_name"] == "AVG"
                ):
                    key = "bat_I_OUT"
                    value = data["value"]
                elif (
                    data["module_name"] == "MIC19"
                    and data["topic_name"] == "MDE"
                    and data["byte_name"] == "POSITION"
                ):
                    key = "dir_pos"
                    value = (26.3929618 * data["value"]) - 135.0
                else:
                    continue

            boat_data.add(key, value)

            avg = {
                "mot_D": boat_data.average("mot_D"),
                "bat_V": boat_data.average("bat_V"),
                "bat_I_IN": boat_data.average("bat_I_IN"),
                "bat_I_OUT": boat_data.average("bat_I_OUT"),
                "dir_pos": boat_data.average("dir_pos"),
            }

            avg["bat_I"] = avg["bat_I_IN"] - avg["bat_I_OUT"]
            avg["bat_P"] = avg["bat_I"] * avg["bat_V"]

            display = "\n".join(
                [
                    formatted_time(message.timestamp),
                    "mot_D  :  {:>5.1f}  [%]".format(avg["mot_D"]),
                    "bat_V  :  {:>6.2f} [V]".format(avg["bat_V"]),
                    "bat_I  :  {:>6.2f} [A]".format(avg["bat_I"]),
                    "bat_P  :  {:>6.2f} [W]".format(avg["bat_P"]),
                    "dir_pos: {:>6.2f} [°]".format(avg["dir_pos"]),
                ]
            )

            clear_terminal()
            print(display)

    except KeyboardInterrupt:
        # Stop receiving messages on keyboard interrupt
        pass
    except Exception as e:
        print(e)

    bus.shutdown()
