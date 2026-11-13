"""Start and stop the six isolated Linux/FRRouting nodes."""
import argparse
from contextlib import contextmanager
import fcntl
import grp
import os
from pathlib import Path
import pwd
import shutil
import signal
import subprocess
import sys
import time
from uuid import uuid4

from .model import DATA, HOSTS, L3_BRIDGE, L3_VNI, LAB, LEAVES, LINKS, NODES, ROUTERS, STATE, VLANS, VRF
from .model import address, interfaces, leaf_vlans, local_prefix

SOCKETS = Path("/run/frr")
HISTORY = Path("/var/lib/frr")
DAEMONS = ("mgmtd", "zebra", "bgpd")
ERRORS = (OSError, ValueError, RuntimeError, subprocess.SubprocessError)


def run(*argv, timeout=5, check=True, env=None):
    return subprocess.run(argv, capture_output=True, text=True, timeout=timeout, check=check, env=env)


def ns(node):
    if node not in NODES:
        raise ValueError(f"Unknown lab node: {node}")
    return f"idc-{node}"


def ip(node, *argv, **kwargs):
    return run("ip", "-n", ns(node), *argv, **kwargs)


def net(node, *argv, **kwargs):
    return run("ip", "netns", "exec", ns(node), *argv, **kwargs)


def vty_args(node):
    return ("vtysh", "--vty_socket", str(SOCKETS / ns(node)), "--config_dir", str(STATE / node))


def vty(node, *commands, **kwargs):
    return run(*vty_args(node), *(word for cmd in commands for word in ("-c", cmd)), **kwargs)


def require_root():
    if os.geteuid() != 0:
        raise RuntimeError("Run this command with sudo in a dedicated Linux lab VM.")


def require_ready():
    require_root()
    if not (STATE / "ready").is_file():
        raise RuntimeError("Start with sudo python3 tools/idc.py fabric up.")


@contextmanager
def lab_lock():
    require_root()
    with open("/run/lock/idc-resilience.lock", "a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RuntimeError("Another IDC lab change is in progress.") from error
        yield


def link_state(node, port, state):
    ip(node, "link", "set", "dev", port, state)


def wire():
    for link in LINKS:
        a, ap, ac = link["a"]
        b, bp, bc = link["b"]
        run("ip", "link", "add", ap, "netns", ns(a), "type", "veth",
            "peer", "name", bp, "netns", ns(b))
        for node, port, cidr in ((a, ap, ac), (b, bp, bc)):
            if cidr:
                ip(node, "link", "set", "dev", port, "mtu", str(DATA["fabric_mtu"]))
                ip(node, "addr", "add", cidr, "dev", port)
            link_state(node, port, "up")


def vni_bridge(node, bridge, vni, mac):
    vx = f"vx{vni}"
    ip(node, "link", "add", bridge, "type", "bridge", "stp_state", "0")
    ip(node, "link", "set", bridge, "master", VRF, "addrgenmode", "none", "address", mac)
    ip(node, "link", "add", vx, "type", "vxlan", "id", str(vni),
       "local", ROUTERS[node]["loopback"], "dstport", "4789", "nolearning")
    ip(node, "link", "set", vx, "master", bridge, "addrgenmode", "none")
    ip(node, "link", "set", vx, "type", "bridge_slave", "neigh_suppress", "on", "learning", "off")
    link_state(node, vx, "up")
    link_state(node, bridge, "up")


def configure_leaf(node):
    ip(node, "link", "add", VRF, "type", "vrf", "table", str(DATA["vrf_table"]))
    link_state(node, VRF, "up")
    ip(node, "route", "add", "vrf", VRF, "unreachable", "default", "metric", "4278198272")
    edge = next(port for port, cidr, *_ in interfaces(node) if cidr is None)
    for vlan in leaf_vlans(node):
        bridge, iface = f"br{vlan}", f"{edge}.{vlan}"
        info = VLANS[vlan]
        vni_bridge(node, bridge, info["vni"], f"02:00:00:00:00:{int(vlan):02x}")
        ip(node, "link", "add", "link", edge, "name", iface, "type", "vlan", "id", vlan)
        ip(node, "link", "set", iface, "master", bridge)
        link_state(node, iface, "up")
        ip(node, "addr", "add", info["gateway"], "dev", bridge)
    vni_bridge(node, L3_BRIDGE, L3_VNI, f"02:00:00:00:fe:0{node[-1]}")


def configure_host(node):
    port = next(interfaces(node))[0]
    mac = f"02:00:00:00:01:0{node[-1]}"
    ip(node, "link", "set", port, "address", mac)
    for vlan, cidr in HOSTS[node].items():
        iface = f"{port}.{vlan}"
        ip(node, "link", "add", "link", port, "name", iface, "type", "vlan", "id", vlan)
        ip(node, "link", "set", iface, "address", mac)
        ip(node, "addr", "add", cidr, "dev", iface)
        link_state(node, iface, "up")
    local, remote = LEAVES if node == "host1" else LEAVES[::-1]
    vlan = ROUTERS[local]["local_vlan"]
    ip(node, "route", "add", local_prefix(remote), "via", address(VLANS[vlan]["gateway"]),
       "dev", f"{port}.{vlan}")


def checked_cli(result):
    output = result.stdout + result.stderr
    if "% " in output:
        raise RuntimeError(output.strip())


def start_router(node):
    startup = STATE / node / "startup.log"
    for daemon in DAEMONS:
        command = ["ip", "netns", "exec", ns(node), f"/usr/lib/frr/{daemon}",
                   "-N", ns(node), "-d", "-A", "127.0.0.1", "-P", "0"]
        if daemon != "mgmtd":
            command += ["-f", "/dev/null"]
        socket = SOCKETS / ns(node) / f"{daemon}.vty"
        socket.unlink(missing_ok=True)
        with startup.open("ab") as log:
            try:
                subprocess.run(command, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                               timeout=12, check=True, env={**os.environ, "TZ": "UTC"})
            except subprocess.SubprocessError as error:
                raise RuntimeError(f"{node} {daemon}: {startup.read_text()[-1600:]}") from error
        deadline = time.monotonic() + 4
        while not socket.is_socket():
            if time.monotonic() >= deadline:
                raise RuntimeError(f"{node} {daemon}: VTY socket missing. {startup.read_text()[-1600:]}")
            time.sleep(0.05)
    checked_cli(run(*vty_args(node), "-f", LAB / "configs/frr" / f"{node}.conf", timeout=12))


def processes(node):
    return [int(pid) for pid in run("ip", "netns", "pids", ns(node)).stdout.split()]


def stop_processes(node):
    for sig in (signal.SIGTERM, signal.SIGKILL):
        for pid in processes(node):
            try:
                os.kill(pid, sig)
            except ProcessLookupError:
                pass
        deadline = time.monotonic() + 1
        while time.monotonic() < deadline:
            if not processes(node):
                return
            time.sleep(0.05)
    raise RuntimeError(f"{node}: processes remain after shutdown")


def up():
    for executable in ("ip", "bridge", "vtysh", "ping", "curl", "sysctl"):
        if not shutil.which(executable):
            raise RuntimeError(f"Missing executable: {executable}")
    uid, gid = pwd.getpwnam("frr").pw_uid, grp.getgrnam("frr").gr_gid
    reserved = [Path("/run/netns") / ns(node) for node in NODES]
    reserved += [parent / ns(node) for parent in (SOCKETS, HISTORY) for node in ROUTERS]
    if STATE.exists() or any(path.exists() or path.is_symlink() for path in reserved):
        raise RuntimeError("An IDC lab runtime or reserved namespace already exists.")
    STATE.mkdir(mode=0o755)
    try:
        SOCKETS.mkdir(mode=0o775, exist_ok=True)
        HISTORY.mkdir(mode=0o755, exist_ok=True)
        for node in NODES:
            path = STATE / node
            path.mkdir(mode=0o755)
            run("ip", "netns", "add", ns(node))
            (path / "owned").touch()
            link_state(node, "lo", "up")
            if node in ROUTERS:
                for parent in (SOCKETS, HISTORY):
                    router_dir = parent / ns(node)
                    router_dir.mkdir(mode=0o775)
                    os.chown(router_dir, uid, gid)
                os.chown(path, uid, gid)
                (path / "vtysh.conf").write_text("service integrated-vtysh-config\n")
                net(node, "sysctl", "-q", "-w", "net.ipv4.ip_forward=1",
                    "net.ipv4.conf.all.rp_filter=0", "net.ipv4.conf.default.rp_filter=0")
                ip(node, "addr", "add", ROUTERS[node]["loopback"] + "/32", "dev", "lo")
        wire()
        for node in LEAVES:
            configure_leaf(node)
        for node in HOSTS:
            configure_host(node)
        for node in ROUTERS:
            start_router(node)
        with (STATE / "host2/service.log").open("ab") as log:
            subprocess.Popen(
                ["ip", "netns", "exec", ns("host2"), sys.executable,
                 str(LAB / "idc_lab/service.py"), str(DATA["service_port"])],
                stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True,
            )
        (STATE / "ready").write_text(uuid4().hex + "\n", encoding="utf-8")
    except BaseException:
        down()
        raise


def down():
    if not STATE.is_dir():
        return
    errors = []
    for node in reversed(NODES):
        if not (STATE / node / "owned").is_file():
            continue
        try:
            if (Path("/run/netns") / ns(node)).exists():
                stop_processes(node)
                run("ip", "netns", "delete", ns(node))
            if node in ROUTERS:
                for parent in (SOCKETS, HISTORY):
                    path = parent / ns(node)
                    if path.is_dir():
                        shutil.rmtree(path)
        except ERRORS as error:
            errors.append(f"{node}: {describe(error)}")
    if errors:
        raise RuntimeError("Teardown incomplete: " + "; ".join(errors))
    shutil.rmtree(STATE)


def describe(error):
    if isinstance(error, subprocess.CalledProcessError):
        return (error.stderr or error.stdout or str(error)).strip()
    return str(error)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("up", "down"))
    args = parser.parse_args()
    try:
        with lab_lock():
            (up if args.action == "up" else down)()
    except (*ERRORS, KeyError) as error:
        parser.exit(1, describe(error) + "\n")
    print("IDC fabric started" if args.action == "up" else "IDC fabric stopped")


if __name__ == "__main__":
    main()
