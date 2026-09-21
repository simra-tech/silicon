Runner failed before managed completion: the shared watchdog installs process
signal handlers and cannot run inside a thread pool. Some children launched
before the exception; their container exited and no owned container remains.
Incomplete run.json files say running because the watchdog exception bypassed
completion. Treat every r1 check as **not run to verified completion**. Logs,
source and partial records are preserved. Sequential r2 is a fresh run with
unchanged circuit intent and correct main-thread watchdog use.
