#!/usr/bin/env python3
# coding: utf-8

import json
from typing import Optional, List
import can
import datetime
import signal, sys

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

    boat_data = {
        "mot_D": 0.0,
        "bat_I": 0.0,
        "bat_I_IN": 0.0,
        "bat_I_OUT": 0.0,
        "bat_V": 0.0,
        "bat_P": 0.0,
    }
    should_display = True

    bus = can.interface.Bus(bustype="socketcan", bitrate=500_000)  # type: ignore

    def int_handler(signum, frame):
        bus.shutdown()
        print("\nNicely terminated.")
        sys.exit(0)

    signal.signal(signal.SIGINT, int_handler)
    signal.signal(signal.SIGTERM, int_handler)

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

            for data in parsed_topic:
                if (
                    data["module_name"] == "MIC19"
                    and data["topic_name"] == "MOTOR"
                    and data["byte_name"] == "D"
                ):
                    should_display = True
                    boat_data["mot_D"] = data["value"] * 100
                elif (
                    data["module_name"] == "MCS19"
                    and data["topic_name"] == "BAT"
                    and data["byte_name"] == "AVG"
                ):
                    should_display = True
                    boat_data["bat_V"] = data["value"]
                elif (
                    data["module_name"] == "MSC19_4"
                    and data["topic_name"] == "ADC"
                    and data["byte_name"] == "AVG"
                ):
                    should_display = True
                    boat_data["bat_I_IN"] = data["value"]
                elif (
                    data["module_name"] == "MSC19_5"
                    and data["topic_name"] == "ADC"
                    and data["byte_name"] == "AVG"
                ):
                    should_display = True
                    boat_data["bat_I_OUT"] = data["value"]

            if should_display:
                should_display = False

                boat_data["bat_I"] = boat_data["bat_I_IN"] - boat_data["bat_I_OUT"]
                boat_data["bat_P"] = boat_data["bat_I"] * boat_data["bat_V"]
                display = ", ".join(
                    [
                        datetime.datetime.fromtimestamp(message.timestamp).strftime(
                            "%H:%M:%S.%f"
                        )[:-3],
                        "mot_D: {:>5.1f} [%]".format(boat_data["mot_D"]),
                        "bat_V: {:>6.2f} [V]".format(boat_data["bat_V"]),
                        "bat_I: {:>6.2f} [A]".format(boat_data["bat_I"]),
                        "bat_P: {:>8.2f} [W]".format(boat_data["bat_P"]),
                    ]
                )
                print(display)

    except KeyboardInterrupt:
        # Stop receiving messages on keyboard interrupt
        pass
    except Exception as e:
        print(e)

    bus.shutdown()