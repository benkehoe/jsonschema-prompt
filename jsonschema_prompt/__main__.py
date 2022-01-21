# Copyright 2022 Ben Kehoe
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import sys
import json

try:
    import yaml

    loads = yaml.safe_load
    loadf = yaml.safe_load
except ModuleNotFoundError:
    loads = json.loads
    loadf = json.load

from . import prompt, SetValueError

parser = argparse.ArgumentParser()
group = parser.add_mutually_exclusive_group()
group.add_argument("--schema")
group.add_argument("--schema-file", type=argparse.FileType("r"))
parser.add_argument("--set", nargs=2, action="append")
args = parser.parse_args()

if not (args.schema or args.schema_file):
    parser.exit("Must specify --schema or --schema-file")
if args.schema:
    try:
        schema = loads(args.schema)
    except Exception as e:
        parser.exit(f"Error parsing schema: {e}")
if args.schema_file:
    try:
        schema = loadf(args.schema_file)
        print("Schema: " + json.dumps(schema) + "\n")
    except Exception as e:
        parser.exit(f"Error loading file: {e}")

values = {}
for key, value in args.set or []:
    try:
        value = json.loads(value)
    except json.JSONDecodeError:
        pass
    values[key] = value

try:
    value = prompt(schema, set_values=values)
    print(json.dumps(value, indent=2))
except SetValueError as e:
    print(f"ERROR: {e}", file=sys.stderr)
    sys.exit(1)
except KeyboardInterrupt:
    pass
