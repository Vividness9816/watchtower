# tests/test_linux_parsers.py — fixture tests for the two Linux collector parsers that have
# real structure but have never run on live hardware (WSL has no lm-sensors chips and no
# SMART drives): LINUX_SENSORS and LINUX_STORAGE, which live as string constants in
# docs/gen_recreate.py. Fixtures model real psutil/hwmon shapes and real smartmontools
# `--scan` / `-H -A -j` JSON. This proves the PARSING; live-hardware behavior stays
# unverified (caveat in RECREATE-LINUX.md §4).
import contextlib, io, json, pathlib, sys, types
from collections import namedtuple
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import importlib.util

_spec = importlib.util.spec_from_file_location("gen_recreate", ROOT / "docs" / "gen_recreate.py")
gen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gen)          # import-safe: writing the guides is behind __main__


def run_collector(src, psutil_stub=None, run_stub=None):
    """Exec a Linux-collector string constant with stubbed psutil / subprocess.run,
    return its parsed JSON stdout."""
    out = io.StringIO()
    saved = sys.modules.get("psutil")
    if psutil_stub is not None:
        sys.modules["psutil"] = psutil_stub
    try:
        ctx = patch("subprocess.run", run_stub) if run_stub else contextlib.nullcontext()
        with ctx, contextlib.redirect_stdout(out):
            try:
                exec(compile(src, "<linux-collector>", "exec"), {"__name__": "__main__"})
            except SystemExit:
                pass
    finally:
        if psutil_stub is not None:
            if saved is None:
                del sys.modules["psutil"]
            else:
                sys.modules["psutil"] = saved
    return json.loads(out.getvalue())


# ---------------------------------------------------------------- sensors fixtures
# Shapes mirror psutil.sensors_temperatures()/sensors_fans() over lm-sensors hwmon.
Temp = namedtuple("shwtemp", "label current high critical")
Fan = namedtuple("sfan", "label current")


def psutil_with(temps, fans):
    m = types.ModuleType("psutil")
    m.sensors_temperatures = lambda: temps
    m.sensors_fans = lambda: fans
    return m


def test_sensors_intel_kraken():
    # Intel coretemp + NVMe composite + an NZXT Kraken exposing coolant temp and pump RPM
    temps = {"coretemp": [Temp("Package id 0", 47.0, 80.0, 100.0),
                          Temp("Core 0", 45.0, 80.0, 100.0), Temp("Core 1", 44.0, 80.0, 100.0)],
             "nvme": [Temp("Composite", 38.9, 84.8, 84.8)],
             "kraken3": [Temp("Coolant temp", 29.4, None, None)]}
    fans = {"nct6798": [Fan("fan1", 812), Fan("fan2", 1043)],
            "kraken3": [Fan("Pump speed", 2210)]}
    s = run_collector(gen.LINUX_SENSORS, psutil_stub=psutil_with(temps, fans))["sensors"]
    assert s["cpu_temp"] == 47, s                       # max of the coretemp entries, int()
    assert s["liquid_temp"] == 29.4, s                  # "coolant" matched
    assert s["pump_rpm"] == 2210, s                     # "pump" matched
    assert s["fans"]["nct6798: fan2"] == 1043, s
    assert "nvme: Composite" in s["temps"], s


def test_sensors_amd_k10temp():
    temps = {"k10temp": [Temp("Tctl", 61.5, None, None), Temp("Tccd1", 55.0, None, None)]}
    s = run_collector(gen.LINUX_SENSORS, psutil_stub=psutil_with(temps, {}))["sensors"]
    assert s["cpu_temp"] == 61 and s["liquid_temp"] is None and s["pump_rpm"] is None, s


def test_sensors_no_chips_and_broken_psutil():
    s = run_collector(gen.LINUX_SENSORS, psutil_stub=psutil_with({}, {}))["sensors"]
    assert s["cpu_temp"] is None and s["fans"] == {} and s["temps"] == {}, s
    broken = types.ModuleType("psutil")

    def boom():
        raise OSError("no /sys/class/hwmon")
    broken.sensors_temperatures = boom
    broken.sensors_fans = lambda: {}
    s = run_collector(gen.LINUX_SENSORS, psutil_stub=broken)["sensors"]
    assert "error" in s, s                              # degrades, never crashes


# ---------------------------------------------------------------- storage fixtures
# Realistic smartmontools JSON (smartctl 7.x -j): NVMe has NO rotation_rate key and
# protocol "NVMe"; SATA SSD reports rotation_rate 0; HDD reports its RPM.
SCAN = ("/dev/sda -d sat # /dev/sda [SAT], ATA device\n"
        "/dev/sdb -d sat # /dev/sdb [SAT], ATA device\n"
        "/dev/nvme0 -d nvme # /dev/nvme0, NVMe device\n")

NVME_OK = {"json_format_version": [1, 0],
           "smartctl": {"version": [7, 4], "exit_status": 0},
           "device": {"name": "/dev/nvme0", "info_name": "/dev/nvme0",
                      "type": "nvme", "protocol": "NVMe"},
           "model_name": "Samsung SSD 980 PRO 2TB", "serial_number": "S69ENF0R000000",
           "firmware_version": "5B2QGXA7",
           "smart_status": {"passed": True, "nvme": {"value": 0}},
           "nvme_smart_health_information_log": {
               "critical_warning": 0, "temperature": 38, "available_spare": 100,
               "available_spare_threshold": 10, "percentage_used": 3,
               "power_on_hours": 4211, "unsafe_shutdowns": 12, "media_errors": 0},
           "temperature": {"current": 38}, "power_on_time": {"hours": 4211}}

HDD_OK = {"device": {"name": "/dev/sda", "type": "sat", "protocol": "ATA"},
          "model_name": "WDC WD40EFRX-68N32N0", "rotation_rate": 5400,
          "smart_status": {"passed": True}, "temperature": {"current": 34}}

SSD_FAILING = {"device": {"name": "/dev/sdb", "type": "sat", "protocol": "ATA"},
               "model_name": "Samsung SSD 860 EVO 1TB", "rotation_rate": 0,
               "smart_status": {"passed": False}, "temperature": {"current": 41}}

DEVICES = {"/dev/sda": HDD_OK, "/dev/sdb": SSD_FAILING, "/dev/nvme0": NVME_OK}


def smartctl_stub(devices, scan=SCAN):
    def run(args, **kw):
        assert args[0] == "smartctl", args
        if args[1] == "--scan":
            return types.SimpleNamespace(stdout=scan, stderr="", returncode=0)
        return types.SimpleNamespace(stdout=json.dumps(devices[args[-1]]), stderr="",
                                     returncode=0)
    return run


def test_storage_media_health_temp():
    d = run_collector(gen.LINUX_STORAGE, run_stub=smartctl_stub(DEVICES))["storage"]
    by = {x["name"]: x for x in d["drives"]}
    nvme = by["Samsung SSD 980 PRO 2TB"]
    assert nvme["media"] == "SSD", nvme                 # no rotation_rate key: protocol decides
    assert nvme["health"] == "Healthy" and nvme["temp"] == 38, nvme
    hdd = by["WDC WD40EFRX-68N32N0"]
    assert hdd["media"] == "HDD" and hdd["health"] == "Healthy" and hdd["temp"] == 34, hdd
    bad = by["Samsung SSD 860 EVO 1TB"]
    assert bad["media"] == "SSD", bad                   # rotation_rate 0 = SATA SSD
    assert bad["health"] == "Failed", bad               # failed SMART must NOT read "Unknown"
    # end-to-end: a failed drive must actually fire the CRIT drive-health rule
    import rules
    findings = rules.diagnose({"storage": d})
    assert any(f["level"] == "CRIT" and "drive health" in f["what"] for f in findings), findings


def test_storage_degrades():
    # smartctl not installed -> present:false, never a crash
    def missing(args, **kw):
        raise FileNotFoundError("smartctl")
    d = run_collector(gen.LINUX_STORAGE, run_stub=missing)["storage"]
    assert d.get("present") is False, d
    # one device answering garbage (unreadable / needs root) -> Unknown entry, others still parse
    devs = dict(DEVICES)
    garbage = types.SimpleNamespace(stdout="Smartctl open device failed", stderr="", returncode=2)

    def run(args, **kw):
        if args[1] == "--scan":
            return types.SimpleNamespace(stdout=SCAN, stderr="", returncode=0)
        if args[-1] == "/dev/sdb":
            return garbage
        return types.SimpleNamespace(stdout=json.dumps(devs[args[-1]]), stderr="", returncode=0)
    d = run_collector(gen.LINUX_STORAGE, run_stub=run)["storage"]
    by = {x["name"]: x for x in d["drives"]}
    assert by["/dev/sdb"]["health"] == "Unknown", by    # degraded, not crashed
    assert by["Samsung SSD 980 PRO 2TB"]["media"] == "SSD", by


if __name__ == "__main__":
    for fn in (test_sensors_intel_kraken, test_sensors_amd_k10temp,
               test_sensors_no_chips_and_broken_psutil,
               test_storage_media_health_temp, test_storage_degrades):
        fn()
        print(f"  ok  {fn.__name__}")
    print("linux parsers ok")
