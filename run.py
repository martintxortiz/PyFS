import logging
import sys

from fs.services.executive_services import ExecutiveServices

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d | %(levelname)-8s | %(name)-20s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    stream=sys.stdout
)

if __name__ == "__main__":
    es = ExecutiveServices()
    raise SystemExit(es.run())