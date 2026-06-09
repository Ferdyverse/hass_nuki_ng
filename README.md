[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)

## Better support for Nuki devices in Home Assistant

### Features:
* Supported modes:
  * Nuki Bridge-only, with automatic webhook registration
  * Cloud Web API, without Nuki bridge (Nuki Lock 3.0 Pro). Polling only
  * Hybrid, using best parts of both
* Exposes the detailed device information via sensors
* If supported, enables access control to Nuki authorization objects (keypad codes, accounts)
* **Multi-lock support**: each Nuki lock automatically gets its own integration entry — no manual setup per lock required
* **State sync**: on Home Assistant startup the integration pushes a sync to the Nuki Web API so the cloud state matches the physical lock
* **Dynamic discovery**: new locks added to your Nuki account are detected automatically on the next poll — no restart needed


### Screenshots:
<img width="1020" alt="Screenshot 2021-10-11 at 14 02 42" src="https://user-images.githubusercontent.com/159124/136786951-d1ffdb22-637a-49c2-a1ff-43c465a03f0b.png">


## Setup

{% if not installed %}

### Installation:

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=kvj&repository=hass_nuki_ng&category=integration)

* Go to HACS -> Integrations
* Click the three dots on the top right and select `Custom Repositories`
* Enter `https://github.com/kvj/hass_nuki_ng` as repository, select the category `Integration` and click Add
* A new custom integration shows up for installation (Nuki Lock) - install it
* Restart Home Assistant

{% endif %}

### Configuration:

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=nuki_ng)

* Go to Configuration -> Integrations
* Click `Add Integration`
* Search for `Nuki Lock` (not just `Nuki`, as this is the native integration from Home Assistant) and select it
* The integration will try to automatically discover your Nuki Bridge hostname or IP address, if you have a bridge
* It will also automatically enter the Home Assistant internal URL
* Provide either the Bridge API token and URL and/or a web API token and click Submit
* You can provide both, but you need to provide at least one

**Multi-lock setup**: you only need to add the integration **once**. After submitting the form, the integration
automatically creates one config entry per lock. Each lock appears as a separate entry under
Configuration → Integrations with its own set of entities. If you add a new lock to your Nuki account later,
it will be picked up automatically on the next poll.


#### Bridge API Token:
The API token for the Nuki Bridge needs to be configured on the bridge, e.g. using the Nuki mobile app. The
[Home Assistant Nuki documentation](https://www.home-assistant.io/integrations/nuki/) explains it like this:

> To add a Nuki bridge to your installation, you need to enable developer mode on your bridge and define a port and an access token. This can be achieved using the [Android app](https://play.google.com/store/apps/details?id=io.nuki) or [iPhone app](https://apps.apple.com/app/nuki-smart-lock/id1044998081). Go to manage my devices, and select the bridge. Within the bridge configuration turn on the HTTP API and check the details in the screen. Please note that the API token should be 6-20 characters long, even though the app allows you to set a longer one.


#### Web API Token:
* Go to the Nuki Web API management site at https://web.nuki.io/
* Nuki Web needs to be activated in the Nuki app - there is a link on the site that tells you how to do that
* Once activated, login on the web
* In the menu on the left, select API
* Click `Generate API token`
* Give it a name, leave the other settings as they are and click Save
* Copy the token and save it in a secure place. It will only be shown this once to you.


## Usage:

### Devices:

The integration provides several devices and entities to Home Assistant, depending on your setup. For example:

| Device            | Description                                                                                     |
|-------------------|-------------------------------------------------------------------------------------------------|
| Nuki Bridge       | Providing four diagnostic sensors about the state of the bridge.                                |
| Nuki Lock         | Providing one `lock` entity, three state sensors, a sync button and eight diagnostic sensors.   |
| Nuki Opener       | Providing one `lock` entity, one state sensor and five diagnostic sensors about the opener.     |
| Nuki Web API      | Providing configuration `switch` entities for access permissions as set in the Nuki app.        |

In your setup, you could have several locks, but maybe no opener, no bridge or no web API.


### Entities:

#### Nuki Bridge:

| Entity ID                                      | Type        |  Description                                                               |
|------------------------------------------------|-------------|----------------------------------------------------------------------------|
| binary_sensor.nuki_bridge_bridge_callback_set  | Diagnostic  | On, if the integration successfully registered a callback with the bridge  |
| binary_sensor.nuki_bridge_connected            | Diagnostic  | On, if the bridge is reachable via WiFi                                    |
| sensor.nuki_bridge_firmware_version            | Diagnostic  | The current firmware version of the bridge                                 |
| sensor.nuki_bridge_wifi_firmware_version       | Diagnostic  | The current WiFi firmware version of the bridge                            |


#### Nuki Lock:

The entity IDs depend on the Nuki names of the lock. In the example below, it is `Wohnung`.

| Entity ID                                      | Type        | Description                                                                   |
|------------------------------------------------|-------------|-------------------------------------------------------------------------------|
| lock.nuki_wohnung_lock                         | Control     | The main entity to control the lock                                           |
| binary_sensor.nuki_wohnung_door_open           | Sensor      | Shows the state of the door                                                   |
| binary_sensor.nuki_wohnung_locked              | Sensor      | Shows the state of the lock                                                   |
| sensor.nuki_wohnung_door_security_state        | Sensor      | Combines the state of the door with the lock                                  |
| sensor.nuki_wohnung_battery                    | Diagnostic  | Shows the battery level of the lock                                           |
| binary_sensor.nuki_wohnung_battery_charging    | Diagnostic  | Shows if the battery is currently charging                                    |
| binary_sensor.nuki_wohnung_battery_critical    | Diagnostic  | Shows if the battery has a critical level                                     |
| sensor.nuki_wohnung_door_state                 | Diagnostic  | Shows the state of the door                                                   |
| sensor.nuki_wohnung_firmware_version           | Diagnostic  | Shows the current firmware of the lock                                        |
| binary_sensor.nuki_wohnung_keypad_battery_critical | Diagnostic | Shows if the battery of the keypad has a critical level                   |
| sensor.nuki_wohnung_rssi                       | Diagnostic  | Shows the received signal strength indicator of the lock                      |
| sensor.nuki_wohnung_state                      | Diagnostic  | Shows the state of the lock                                                   |
| button.nuki_wohnung_sync                       | Diagnostic  | Triggers an immediate state sync from the physical lock to the Nuki cloud     |


#### Nuki Opener:

The entity IDs depend on the Nuki names of the lock. In the example below, it is `Haustur`.

| Entity ID                                      | Type        | Description                                     |
|------------------------------------------------|-------------|-------------------------------------------------|
| lock.nuki_haustur_lock                         | Control     | The main entity to control the opener           |
| binary_sensor.nuki_haustur_locked              | Sensor      | Shows the state of the opener (locked or unlocked)  |
| binary_sensor.nuki_haustur_battery_critical    | Diagnostic  | Shows if the battery has a critical level       |
| sensor.nuki_haustur_firmware_version           | Diagnostic  | Shows the current firmware of the opener        |
| sensor.nuki_haustur_rssi                       | Diagnostic  | Shows the received signal strength indicator of the opener   |
| sensor.nuki_haustur_state                      | Diagnostic  | Shows the state of the opener (e.g., rto active)  |


#### Nuki Web API:

The entity IDs depend on the authorization you have given to your devices. There will be as many `switch` entities as
there are authorizations stored on the Nuki platform. While they are all named `switch.nuki_` followed by a descriptive
name, there are three different types:

| Type                                      | Example                                          |
|-------------------------------------------|--------------------------------------------------|
| Authorization of local devices            | The keypad, which is granted access to the lock  |
| Authorization of access codes             | A code registered with the keypad                |
| Authorization of apps                     | Access granted to members of the family          |


### Lock state synchronization

The Nuki Web API caches the last known state of each lock. If the lock was operated while Home Assistant was offline
or the Nuki app was used directly, the cached state may be stale.

The integration handles this in two ways:

1. **Automatic sync on startup** — when Home Assistant starts, the integration calls `POST /smartlock/{id}/sync`
   for every configured lock. This tells the Nuki cloud to fetch the current state from the physical device.

2. **Manual sync button** — each lock exposes a `button.nuki_<name>_sync` entity (diagnostic category).
   Press it any time to force an immediate state refresh.

> Note: The sync endpoint is only available when a Web API token is configured.


### Services:

The integration provides the following services:


#### Service `lock.lock`

* For a Nuki Lock, this locks the door
* For a Nuki Opener, this stops an active ring-to-open function

The attribute should appear as a `target` for the service.

| Target attribute    | Optional | Description                                           |
|---------------------|----------|-------------------------------------------------------|
| `entity_id`         |       no | Entity of the relevant lock.                          |


#### Service `lock.unlock`

* For a Nuki Lock, this unlocks the door
* For a Nuki Opener, this starts the ring-to-open function

The attribute should appear as a `target` for the service.

| Target attribute    | Optional | Description                                           |
|---------------------|----------|-------------------------------------------------------|
| `entity_id`         |       no | Entity of the relevant lock.                          |


#### Service `lock.open`

* For a Nuki Lock, this unlatches the door
* For a Nuki Opener, this buzzes the door open

The attribute should appear as a `target` for the service.

| Target attribute    | Optional | Description                                           |
|---------------------|----------|-------------------------------------------------------|
| `entity_id`         |       no | Entity of the relevant lock.                          |


#### Service `nuki_ng.bridge_reboot`

Reboots the Nuki Bridge. This service has no attributes


#### Service `nuki_ng.bridge_fwupdate`

Performs a bridge software update. This service has no attributes


#### Service `nuki_ng.bridge_delete_callback`

Deletes a callback URL from the bridge callbacks list.
The callbacks currently set are exposed as attributes of the 'Bridge Callback Set' entity.

The attribute should appear as a `target` for the service.

| Service data attribute    | Optional | Description                                           |
|---------------------------|----------|-------------------------------------------------------|
| `command`                 |       no | URL to delete.                                        |

## Useful tips

### Open/unlatch Nuki lock via UI

Even though the component supports the `lock.open` service and advertises support of it, Lovelace UI doesn't show any controls to trigger. This can be achieved via simple script similar to the one below:
```yaml
alias: Nuki Lock Open
sequence:
  - device_id: 8d159025411a270ecb9024794bc54361
    domain: lock
    entity_id: lock.nuki_front_door_lock
    type: open
mode: single
icon: mdi:lock-open
```

or manually calling the service:
```yaml
type: button
entity: lock.nuki_front_door_lock
tap_action:
  action: call-service
  service: lock.open
  service_data: {}
  target:
    entity_id: lock.nuki_front_door_lock
name: Nuki
```

## Debug CLI

A standalone command-line tool `debug.py` is included at the root of the repository. It lets you test the
integration against your Nuki devices **without running Home Assistant**.

### Requirements

```bash
pip install aiohttp
```

### Usage

```bash
python debug.py [--bridge <IP>] [--token <TOKEN>] [--web-token <TOKEN>] <command> [args]
```

Credentials can also be supplied via environment variables:

| Variable        | Description              |
|-----------------|--------------------------|
| `NUKI_BRIDGE`   | Bridge IP or `IP:port`   |
| `NUKI_TOKEN`    | Bridge API token         |
| `NUKI_WEB_TOKEN`| Nuki Web API token       |

### Commands

| Command                        | Description                                                   |
|--------------------------------|---------------------------------------------------------------|
| `list`                         | List all devices (bridge and/or web API)                      |
| `info`                         | Show raw bridge info                                          |
| `log <dev_id>`                 | Show the last log entry for a device (web API)                |
| `unlock_log <dev_id>`          | Show the last unlock log entry for a device (web API)         |
| `auths <dev_id>`               | List all authorizations for a device (web API)                |
| `sync <dev_id>`                | Sync state from the physical lock to the Nuki cloud (web API) |
| `action <dev_id> <action>`     | Perform a lock action (bridge preferred, web API fallback)    |

Available actions for `action`: `lock`, `unlock`, `open`, `lock_n_go`,
`activate_rto`, `deactivate_rto`, `electric_strike_actuation`,
`activate_continuous_mode`, `deactivate_continuous_mode`.

### Example

```bash
# List all locks
NUKI_BRIDGE=192.168.1.50 NUKI_TOKEN=mytoken python debug.py list

# Force a cloud sync for a specific lock
NUKI_WEB_TOKEN=mywebtoken python debug.py sync 12345678

# Unlock via bridge
NUKI_BRIDGE=192.168.1.50 NUKI_TOKEN=mytoken python debug.py action 12345678 unlock
```
