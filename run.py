import logging
import sys

from pyfs.core.executive_services import ExecutiveServices

def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s.%(msecs)03d | %(levelname)-8s | %(name)-20s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        stream=sys.stdout,
        force=True,   # ensures config is applied even if handlers exist
    )

    try:
        es = ExecutiveServices()
        es.run()
        return 0

    except Exception:
        logging.exception("Exception occurred in main fs", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
