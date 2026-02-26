import logging
import threading

from fs.services.software_bus import SoftwareBus
#https://www.perplexity.ai/search/design-a-cfs-style-flight-soft-M.mvoJg1RdO7AEjor6FtUw

class ExecutiveServices:
    _log = logging.getLogger("fs.es")
    _lock: threading.RLock

    evs: None
    sb: SoftwareBus
    ts: None
    tbl: None

    app_record: None
    state: None
    reset_type: int

    def __init__(self) -> None:
        self._log.info("es initialized")

    def run(self, reset_type: int) -> None:
        """
        if PROCESSOR reset: load_cds() from disk
        init_evs()
        init_sb()
        init_time(met_offset from cds)
        init_tbl()
        set running = True
        return SUCCESS
        """

    def register_app(self, app) -> None:
        """
        look up AppRecord, fail if not found
        import module by module_path
        call module.create_app() to get instance
        inject self into instance.es
        set state = LATE_INIT
        spawn daemon thread calling instance.main_task()
        thread wrapper catches all exceptions:
            on exception: set state = ERROR, store exception string
        set state = RUNNING when main_task() begins
        return SUCCESS
        """

    def start_app(self, app) -> None:
        """
        look up AppRecord, fail if not found
        import module by module_path
        call module.create_app() to get instance
        inject self into instance.es
        set state = LATE_INIT
        spawn daemon thread calling instance.main_task()
        thread wrapper catches all exceptions:
            on exception: set state = ERROR, store exception string
        set state = RUNNING when main_task() begins
        return SUCCESS
        """

    def stop_app(self, app) -> None:
        """
        stop_app(name)
        wait briefly
        increment restart_count
        start_app(name)
        return SUCCESS
        """

    def heartbeat(self) -> None:
        """
        update AppRecord.last_hb = now    ← apps call this every loop
        no return value
        """

    def get_app_state(self, name: str) -> None:
        """return state int"""

    def get_app_registry(self) -> None:
        """return dict snapshot of all app states + last_hb"""

    def start_all_apps(self) -> None:
        """
        load all apps
        """

    def load_startup_file(self) -> None:
        """
        parse JSON file
        sort entries by priority
        for each entry: register_app(name, module, priority)
        return SUCCESS or ERR_PARSE_FAIL
        """