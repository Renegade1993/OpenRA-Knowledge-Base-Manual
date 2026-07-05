# Chapter 10.2 — Online Services and References

## Purpose

OpenRA includes several online services: the master server browser, LAN advertisement, player authentication, replay metadata, and map download. This chapter explains how the game discovers, lists, and connects to servers, and how it interacts with the OpenRA web services.

## Learning Objectives


After studying this chapter, you should be able to:

- Explain the online services: master server, LAN advertisement, authentication, map download, and replay upload.
- Describe the WebServices global mod data and its endpoints.
- Trace server advertisement, server list fetch, and map download flows.
- Configure server and client settings for online play.
- Implement custom [server traits](../appendices/Appendix_A_Glossary.md) or custom web service endpoints.
- Understand server compatibility checks and joinability requirements.

## Files

| File | Responsibility |
| :---- | :---- |
| `OpenRA.Mods.Common/WebServices.cs` | Global mod data for web service endpoints (master server, replays, map download, badges). |
| `OpenRA.Mods.Common/ServerTraits/MasterServerPinger.cs` | Advertises servers to the master server and LAN. |
| `OpenRA.Game/Network/GameServer.cs` | `GameServer` data class for server listings. |
| `OpenRA.Game/Network/GameServer.cs` | `GameClient` data class for players in a server. |
| `OpenRA.Mods.Common/Widgets/Logic/ServerListLogic.cs` | Multiplayer server browser UI logic. |
| `OpenRA.Game/Network/Session.cs` | Lobby session and client data. |
| `OpenRA.Game/ExternalMods.cs` | Installed mod registry for server compatibility. |
| `OpenRA.Game/Network/Connection.cs` | Network connection used to join servers. |
| `OpenRA.Game/Map/MapCache.cs` | Map download and cache management; queries remote map details. |
| `OpenRA.Mods.Common/Widgets/Logic/Lobby/MapPreviewLogic.cs` | UI logic for map download progress and installation. |
| `OpenRA.Game/Server/Server.cs` | Dedicated server that advertises itself. |

![Architecture diagram](images/Part_10_Chapter_02_Online_References-architecture-diagram-showing-the-main-classes-interfaces-and-9161e6.svg)

## Architecture


### Master server

The master server is a web service that maintains a list of public game servers. A dedicated or hosted server pings the master server periodically with its status. The client fetches the list and displays it in the multiplayer browser.

### LAN advertisement

Servers can also advertise on the local network using a UDP beacon (`BeaconLib`). Clients on the same LAN can see these games without going through the master server.

### Server listing fields

The `GameServer` class contains:

- `Name` — server name.
- `Address` — `ip:port`.
- `Mod` / `Version` — mod ID and version.
- `Map` — current map UID.
- `State` — waiting/playing/completed.
- `MaxPlayers` — total slots.
- `Protected` — password protected.
- `Authentication` — requires forum authentication.
- `Clients` — list of players.
- `DisabledSpawnPoints` — spawn points disabled by the host.
- `Location` — GeoIP-resolved location.

### Server compatibility

When a client receives a server list, it checks each entry against `Game.ExternalMods` to determine if the [mod](../appendices/Appendix_A_Glossary.md) and version are installed. If not, the server may be joinable after mod switching or map download.

### Web service endpoints

`WebServices` is a global mod data object that stores URLs:

- `ServerAdvertise` — master server ping endpoint.
- `ServerList` — master server list endpoint.
- `MapRepository` — map download endpoint.
- `ReplayServer` — replay upload endpoint.
- `BadgeRepository` — player badge endpoint.

![Data flow  code path diagram](images/Part_10_Chapter_02_Online_References-sequence-flow-diagram-tracing-the-execution-path-from-trigge-035864.svg)

## Data Flow / Code Path


### Server advertisement

```csharp
public void Tick(S server)
{
    if (!server.IsMultiplayer)
        return;

    if ((server.Settings.AdvertiseOnline || server.Settings.AdvertiseOnLocalNetwork)
        && !isBusy && ((lastChanged > lastPing && Game.RunTime - lastPing > RateLimitInterval) || isInitialPing))
    {
        var gs = new GameServer(server);
        if (server.Settings.AdvertiseOnline)
            UpdateMasterServer(server, gs.ToPOSTData(false));

        if (server.Settings.AdvertiseOnLocalNetwork && lanGameBeacon != null)
            lanGameBeacon.BeaconData = gs.ToPOSTData(true);

        lastPing = Game.RunTime;
    }
}
```

### Master server ping

```csharp
void UpdateMasterServer(S server, string postData)
{
    isBusy = true;
    Task.Run(async () =>
    {
        var endpoint = server.ModData.GetOrCreate<WebServices>().ServerAdvertise;
        var client = HttpClientFactory.Create();
        var response = await client.PostAsync(endpoint, new StringContent(postData));
        var masterResponseText = await response.Content.ReadAsStringAsync();
        ...
        isBusy = false;
    });
}
```

### Server list fetch

The server browser UI (`ServerListLogic`) fetches the server list from the master server endpoint, parses each entry into a `GameServer`, and displays them grouped by mod. The client can query server details and join compatible games.

### Map download

If a server is running a map the client does not have, the client can download it from the map repository. `MapDownload` performs the HTTP request and adds the map to the `MapCache`.

### Replay upload

After a game, the replay file can be uploaded to the replay server. The server stores metadata (`ReplayMetadata`) such as players, map, duration, and mod.

![Configuration (yaml) diagram](images/Part_10_Chapter_02_Online_References-annotated-yaml-snippet-diagram-showing-the-key-fields-and-ho-6a1b98.svg)

## Configuration (YAML)


### Web services

```yaml
WebServices:
    ServerAdvertise: https://master.openra.net/games
    ServerList: https://master.openra.net/games
    MapRepository: https://resource.openra.net/map/
    ReplayServer: https://replay.openra.net/
```

### Server settings

```yaml
ServerSettings:
    Name: My OpenRA Server
    ListenPort: 1234
    AdvertiseOnline: true
    AdvertiseOnLocalNetwork: true
    RequireAuthentication: false
    Password: ""
```

### Client settings

```yaml
Game:
    AllowDownloading: true
    FilterGamesInServerList: false
```

## Interconnectivity

- **Depends on:** [Part 3.1 — Mod SDK and Project Structure](Part_03_Chapter_01_Mod_SDK.md) (global mod data), [Part 3.3 — Build Pipeline and Packaging](Part_03_Chapter_03_Build_Packaging.md) (packaging), [Part 6.4 — Crypto Utilities and Player Authentication](Part_06_Chapter_04_Crypto.md) (crypto for authentication), [Part 9.2 — Server and Connection Layer](Part_09_Chapter_02_Server_Connection.md) (server network), [Part 2.2 — Manifest and Mod Metadata](Part_02_Chapter_02_Manifest.md) (maps and map cache).
- **Used by:** [Part 10.1 — Official Mods](Part_10_Chapter_01_Official_Mods.md) (official mods use the master server), [Part 9.2 — Server and Connection Layer](Part_09_Chapter_02_Server_Connection.md) (server advertises), [Part 4.3 — Widgets and Chrome](Part_04_Chapter_03_Widgets.md) (server browser UI).

![Algorithms diagram](images/Part_10_Chapter_02_Online_References-algorithm-diagram-or-pseudocode-flowchart-for-the-non-trivia-5983ed.svg)

## Algorithms


### Server compatibility check

```csharp
var externalKey = ExternalMod.MakeKey(Mod, Version);
if (Game.ExternalMods.TryGetValue(externalKey, out var external) && external.Version == Version)
    IsCompatible = true;

var mapAvailable = Game.Settings.Game.AllowDownloading || Game.ModData.MapCache[Map].Status == MapStatus.Available;
IsJoinable = IsCompatible && State == 1 && mapAvailable;
```

A server is joinable only if the mod is installed (or switchable) and the map is available (or downloadable).

### Rate-limited pings

The master server pinger waits at least 1 second between pings and sends a full ping every 3 minutes to prevent the advertisement from expiring.

### LAN beacon

`BeaconLib.Beacon` broadcasts a UDP packet on the LAN with a game identifier and payload. Clients listen for beacons from `OpenRALANGame`.

### GeoIP resolution

The server uses the GeoIP database to resolve the location of connected clients. This is used for the server list's location column.

![Extension points diagram](images/Part_10_Chapter_02_Online_References-extension-hook-diagram-showing-the-interface-s-to-implement-b4a27b.svg)

## Extension Points


### Run a custom master server

Change `ServerAdvertise` and `ServerList` in `WebServices` to point to your own server listing service. The POST format is defined by `GameServer.ToPOSTData`.

### Add custom server traits

Implement server trait interfaces such as `INotifyServerStart` and `ITick` to add custom server behavior, such as auto-kick, tournaments, or stats collection.

### Custom map repository

Host a map repository compatible with the OpenRA map download API and set `MapRepository` in `WebServices`.

### Custom replay server

Host a replay upload endpoint and set `ReplayServer` in `WebServices`. Implement replay upload logic in a server trait or post-game UI.

![Common pitfalls  guardrails diagram](images/Part_10_Chapter_02_Online_References-checklist-infographic-style-diagram-summarizing-the-top-pitf-fb069e.svg)

## Common Pitfalls / Guardrails


- **Master server rate limits:** do not ping too frequently. The built-in rate limit is 1 second minimum and 3 minutes maximum TTL.
- **Server name blacklist:** the master server may reject servers with inappropriate names. Error codes are shown in the server console.
- **Port forwarding:** advertising online requires the server's port to be reachable from the internet. The master server returns an error if it cannot connect.
- **Mod compatibility:** clients must have the exact mod version. Minor differences prevent joining.
- **Map download:** ensure `AllowDownloading` is enabled and the map repository is reachable. Large maps may take time to download.
- **Authentication:** requiring authentication limits the server to players with forum accounts. Use `ProfileIDWhitelist` for private tournaments.
- **LAN beacon:** LAN games may not be visible across subnets or VPNs. The beacon uses UDP broadcast.

## What to read next

- [Part 9.2 — Server and Connection Layer](Part_09_Chapter_02_Server_Connection.md) for the underlying server and connection layer that online services use.
- [Part 3.1 — Mod SDK and Project Structure](Part_03_Chapter_01_Mod_SDK.md) for how `WebServices` is declared as global mod data.
- [Part 10.1 — Official Mods](Part_10_Chapter_01_Official_Mods.md) for the official mod structure that configures these services.

## Summary

This chapter explains how OpenRA discovers and connects to servers, authenticates players, and downloads maps and replays through its online services.

If any of the concepts above feel unclear, review the relevant section before continuing. For source files and further reading, see the References section.


## References

- `OpenRA.Mods.Common/WebServices.cs` — web service endpoints.
- `OpenRA.Mods.Common/ServerTraits/MasterServerPinger.cs` — server advertisement.
- `OpenRA.Game/Network/GameServer.cs` — server listing data.
- `OpenRA.Mods.Common/Widgets/Logic/ServerListLogic.cs` — server browser UI.
- `OpenRA.Game/Map/MapCache.cs` — map cache and remote map queries.
- `OpenRA.Mods.Common/Widgets/Logic/Lobby/MapPreviewLogic.cs` — map download/install UI logic.
- `OpenRA.Game/FileFormats/ReplayMetadata.cs` — replay metadata.