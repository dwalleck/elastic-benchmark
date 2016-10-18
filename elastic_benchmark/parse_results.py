import argparse
import datetime
import json
import sys
import uuid

from elasticsearch import Elasticsearch, RequestsHttpConnection


def parse_rally_results(raw_results, log_link):
    json_results = json.loads(raw_results)

    result_data = []
    for result in json_results:

        # The alternate_name field is a hack to be able to provide an unqiue
        # name when running the same scenario with multiple configurations
        args = result.get("key").get("kw").get("args")
        if args and "alternate_name" in args:
            scenario_name = args.get("alternate_name")
        else:
            scenario_name = result.get("key").get("name")

        # Generate a unique UUID for the test run. Ideally, we would use
        # the uuid of the Rally run, but that information is not currently
        # available in the result output
        run_id = str(uuid.uuid4())

        for test_result in result.get('result'):
            run_at = test_result.get('timestamp')
            duration = test_result.get('duration')
            outcome = 'pass' if len(test_result.get('error')) == 0 else 'fail'
            runner_config = result.get('key').get('kw').get('runner')
            concurrency = int(runner_config.get('concurrency'))
            times = int(runner_config.get('times'))

            # This is an ElasticBenchmark-specific concept. If a scenario is
            # run multiple times but with a concurrency of 1, the intent is to
            # determine how consistent a scenario is, and so it is labeled
            # as a benchmark. If the concurrency is higher than 1, then the
            # test is marked as a stress test, which determines the execution
            # time and success rate of a scenario being executed with the
            # given amount of concurrency
            test_type = "benchmark" if concurrency == 1 else "stress_test"
            result_data.append({
                    "logs": log_link,
                    "test_type": test_type,
                    "runner_config": runner_config,
                    "scenario_name": scenario_name,
                    "run_id": run_id,
                    "run_at": datetime.datetime.fromtimestamp(
                        int(run_at)).strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "runtime": duration,
                    "atomic_actions": {
                        key.replace(".", ":"): val for key, val
                        in test_result.get("atomic_actions").items()
                    },
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
        
        self.add_argument(
            "--host", metavar="<host>",
            required=False, default=None, help="")

        self.add_argument(
            "-u", "--user", metavar="<user>",
            required=False, default=None, help="")
        
        self.add_argument(
            "-p", "--password", metavar="<password>",
            required=False, default=None, help="")

        self.add_argument('input', nargs='?', type=argparse.FileType('r'),
                          default=sys.stdin)


def entry():
    cl_args = ArgumentParser().parse_args()
    result_data = parse_rally_results(cl_args.input.read(), cl_args.logs)
    
    es_kwargs = {}
    if cl_args.host:
        es_kwargs['hosts'] = [cl_args.host]
    
    if cl_args.user and cl_args.password:
        es_kwargs['connection_class'] = RequestsHttpConnection
        es_kwargs['http_auth'] = (cl_args.user, cl_args.password)

    client = Elasticsearch(**es_kwargs)
    for result in result_data:
        client.index(
            index='{0}_elastic_benchmark_results'.format(cl_args.environment),
            doc_type='elasic_benchmark_result',
            body=result)
