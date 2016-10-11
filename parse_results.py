import argparse
import datetime
import dateutil.parser
import json
import re
import sys
import uuid

from elasticsearch import Elasticsearch

client = Elasticsearch()

results = open('results.json').read()
json_results = json.loads(results)

result_data = []
for result in json_results:
    scenario_name = result.get("key").get("kw").get("args").get("alternate_name") or result.get("key").get("name")
    run_id = str(uuid.uuid4())
    for individual_result in result.get('result'):
        run_at = individual_result.get('timestamp')
        duration = individual_result.get('duration')
        result = 'pass' if len(individual_result.get('error')) == 0 else 'fail'
        result_data.append({
                "logs": "",
                "test_type": "benchmark" if result.get('key').get('runner').get('concurrency') != 1 else "stress_test"
                "scenario_name": scenario_name,
                "run_id": run_id,
                "run_at": datetime.datetime.fromtimestamp(int(run_at)).strftime("%Y-%m-%dT%H:%M:%S%z"),
                "runtime": duration,
                "atomic_actions": {key.replace(".", ":"): val for key, val in individual_result.get("atomic_actions").items()},
                "result": result})


for result in result_data:
    client.index(index='elastic_bench_results', doc_type='elasic_bench_result', body=result)