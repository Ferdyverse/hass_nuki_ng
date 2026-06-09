#!/usr/bin/env python3
"""Standalone debug CLI for the Nuki NG integration.

Usage:
    python debug.py [--bridge IP] [--token TOKEN] [--web-token TOKEN] <command> [args]

Config can also come from environment variables:
    NUKI_BRIDGE, NUKI_TOKEN, NUKI_WEB_TOKEN

Commands:
    list                       List all devices (bridge or web)
    info                       Bridge info
    log <dev_id>               Last log entry for a device (web)
    unlock_log <dev_id>        Last unlock log entry for a device (web)
    auths <dev_id>             List all authorizations for a device (web)
    action <dev_id> <action>   Perform a lock action via bridge or web
                               Actions: lock, unlock, open, lock_n_go,
                                        activate_rto, deactivate_rto,
                                        electric_strike_actuation,
                                        activate_continuous_mode,
                                        deactivate_continuous_mode
"""

import asyncio
import argparse
import json
import os
import sys
import types


# ---------------------------------------------------------------------------
# Minimal Home Assistant stubs so nuki.py can be imported without full HA
# ---------------------------------------------------------------------------

def _install_ha_stubs():
    class HomeAssistantError(Exception):
        pass

    class UpdateFailed(Exception):
        pass

    class _CoordinatorEntity:
        def __init__(self, coordinator, *a, **kw):
            self.coordinator = coordinator

        @property
        def available(self):
            return True

    class DataUpdateCoordinator:
        pass

    class EntityCategory:
        DIAGNOSTIC = "diagnostic"
        CONFIG = "config"

    class ConfigEntry:
        pass

    class HomeAssistant:
        pass

    stub_map = {
        "homeassistant":                              {"HomeAssistant": HomeAssistant},
        "homeassistant.exceptions":                   {"HomeAssistantError": HomeAssistantError},
        "homeassistant.core":                         {"HomeAssistant": HomeAssistant},
        "homeassistant.helpers":                      {},
        "homeassistant.helpers.update_coordinator":   {"DataUpdateCoordinator": DataUpdateCoordinator,
                                                       "UpdateFailed": UpdateFailed,
                                                       "CoordinatorEntity": _CoordinatorEntity},
        "homeassistant.helpers.event":                {"async_call_later": lambda *a, **kw: None},
        "homeassistant.helpers.network":              {"get_url": lambda *a, **kw: ""},
        "homeassistant.helpers.entity":               {"EntityCategory": EntityCategory},
        "homeassistant.helpers.service":              {},
        "homeassistant.components":                   {},
        "homeassistant.components.webhook":           {"async_unregister": lambda *a, **kw: None,
                                                       "async_register":   lambda *a, **kw: None,
                                                       "async_generate_path": lambda hook_id: f"/{hook_id}"},
        "homeassistant.config_entries":               {"ConfigEntry": ConfigEntry,
                                                       "SOURCE_INTEGRATION_DISCOVERY": "integration_discovery"},
    }

    for name, attrs in stub_map.items():
        if name not in sys.modules:
            mod = types.ModuleType(name)
            for k, v in attrs.items():
                setattr(mod, k, v)
            sys.modules[name] = mod


try:
    import homeassistant.exceptions  # noqa: F401
except ImportError:
    _install_ha_stubs()


# ---------------------------------------------------------------------------
# Import NukiInterface from the local custom_components
# ---------------------------------------------------------------------------

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "custom_components"))

from nuki_ng.nuki import NukiInterface  # noqa: E402


# ---------------------------------------------------------------------------
# Minimal hass mock — only async_add_executor_job is needed by NukiInterface
# ---------------------------------------------------------------------------

class MockHass:
    async def async_add_executor_job(self, fn, *args):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, fn, *args)


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def _print_json(data):
    print(json.dumps(data, indent=2, default=str))


def _build_api(args) -> NukiInterface:
    bridge    = args.bridge    or os.environ.get("NUKI_BRIDGE")
    token     = args.token     or os.environ.get("NUKI_TOKEN")
    web_token = args.web_token or os.environ.get("NUKI_WEB_TOKEN")

    if not token and not web_token:
        print("ERROR: provide at least --token or --web-token (or env vars NUKI_TOKEN / NUKI_WEB_TOKEN)")
        sys.exit(1)

    return NukiInterface(
        MockHass(),
        bridge=bridge,
        token=token,
        web_token=web_token,
    )


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------

async def cmd_list(api: NukiInterface, _args):
    if api.can_bridge():
        print("=== Bridge device list ===")
        _print_json(await api.bridge_list())
    if api.can_web():
        print("=== Web API device list ===")
        _print_json(await api.web_list())


async def cmd_info(api: NukiInterface, _args):
    if not api.can_bridge():
        print("ERROR: bridge not configured")
        sys.exit(1)
    _print_json(await api.bridge_info())


async def cmd_log(api: NukiInterface, args):
    if not api.can_web():
        print("ERROR: web token not configured")
        sys.exit(1)
    _print_json(await api.web_get_last_log(args.dev_id))


async def cmd_unlock_log(api: NukiInterface, args):
    if not api.can_web():
        print("ERROR: web token not configured")
        sys.exit(1)
    _print_json(await api.web_get_last_unlock_log(args.dev_id))


async def cmd_auths(api: NukiInterface, args):
    if not api.can_web():
        print("ERROR: web token not configured")
        sys.exit(1)
    _print_json(await api.web_list_all_auths(args.dev_id))


async def cmd_sync(api: NukiInterface, args):
    if not api.can_web():
        print("ERROR: web token not configured")
        sys.exit(1)
    print(f"Syncing device {args.dev_id} ...")
    await api.web_sync(args.dev_id)
    print("OK — state synced from lock to cloud")


async def cmd_action(api: NukiInterface, args):
    if api.can_bridge():
        print(f"Executing '{args.action}' via bridge for device {args.dev_id}")
        result = await api.bridge_lock_action(args.dev_id, args.action, device_type=0)
        _print_json(result)
    elif api.can_web():
        print(f"Executing '{args.action}' via web API for device {args.dev_id}")
        await api.web_lock_action(args.dev_id, args.action)
        print("OK")
    else:
        print("ERROR: no API configured")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Nuki NG debug CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--bridge",    help="Bridge IP or IP:port  (or NUKI_BRIDGE env var)")
    parser.add_argument("--token",     help="Bridge API token       (or NUKI_TOKEN env var)")
    parser.add_argument("--web-token", dest="web_token",
                        help="Web API token            (or NUKI_WEB_TOKEN env var)")

    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list",       help="List devices")
    sub.add_parser("info",       help="Bridge info")

    p = sub.add_parser("log",        help="Last log entry (web)")
    p.add_argument("dev_id", help="Device / smartlock ID")

    p = sub.add_parser("unlock_log", help="Last unlock log entry (web)")
    p.add_argument("dev_id", help="Device / smartlock ID")

    p = sub.add_parser("auths",      help="List authorizations (web)")
    p.add_argument("dev_id", help="Device / smartlock ID")

    p = sub.add_parser("sync",        help="Sync state from physical lock to cloud (web)")
    p.add_argument("dev_id", help="Device / smartlock ID")

    p = sub.add_parser("action",     help="Perform a lock action")
    p.add_argument("dev_id", help="Device / smartlock ID")
    p.add_argument("action", help="Action name (lock, unlock, open, …)")

    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

COMMANDS = {
    "list":       cmd_list,
    "info":       cmd_info,
    "log":        cmd_log,
    "unlock_log": cmd_unlock_log,
    "auths":      cmd_auths,
    "sync":       cmd_sync,
    "action":     cmd_action,
}


def main():
    parser = build_parser()
    args = parser.parse_args()
    api = _build_api(args)

    handler = COMMANDS[args.command]
    asyncio.run(handler(api, args))


if __name__ == "__main__":
    main()
