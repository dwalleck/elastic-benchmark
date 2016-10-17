import argparse
import datetime
import dateutil.parser
import json
import re
import sys
import uuid

from elasticsearch import Elasticsearch


def parse_rally_results(raw_results):
    json_results = json.loads(raw_results)

    result_data = []
    for result in json_results:
        scenario_name = result.get("key").get("kw").get("args").get(
            "alternate_name") or result.get("key").get("name")
        run_id = str(uuid.uuid4())
        for individual_result in result.get('result'):
            run_at = individual_result.get('timestamp')
            duration = individual_result.get('duration')
            outcome = 'pass' if len(individual_result.get('error')) == 0 else 'fail'
            runner_config = result.get('key').get('kw').get('runner')
            test_type = "benchmark" if runner_config.get('concurrency') != "1" or runner_config.get('times') == "1" else "stress_test"
            result_data.append({
                    "logs": "",
                    "test_type": test_type,
                    "runner_config": runner_config,
                    "scenario_name": scenario_name,
                    "run_id": run_id,
                    "run_at": datetime.datetime.fromtimestamp(int(run_at)).strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "runtime": duration,
                    "atomic_actions": {key.replace(".", ":"): val for key, val in individual_result.get("atomic_actions").items()},
                    "result": outcome})
    return result_data


class ArgumentParser(argparse.ArgumentParser):
    def __init__(self):
        desc = "Parses a given input and inserts into ElasticSearch."
        usage_string = "elastic-benchmark [-t/--type]"

        super(ArgumentParser, self).__init__(
            usage=usage_string, description=desc)

        self.prog = "Argument Parser"

        self.add_argument(
            "-e", "--environment", metavar="<environment>",
            required=True, default="devstack",
            help="The environment you're running against.")

        self.add_argument(
            "-l", "--logs", metavar="<log link>",
            required=False, default=None, help="A link to the logs.")

        self.add_argument('input', nargs='?', type=argparse.FileType('r'),
                          default=sys.stdin)


def entry_point():
    cl_args = ArgumentParser().parse_args()
    result_data = parse_rally_results(cl_args.input.read())
    
    client = Elasticsearch()

    for result in result_data:
        result['logs'] = cl_args.logs
        client.index(
            index='{0}_elastic_bench_results'.format(cl_args.environment),
            doc_type='elasic_bench_result',
            body=result)