# Chapter 9.2 — Server and Connection Layer

## Purpose

The `[OrderManager](../appendices/Appendix_A_Glossary.md)` ([Part 9.1 — OrderManager and Lockstep Foundation](Part_09_Chapter_01_OrderManager.md)) coordinates the client side of the [lockstep](../appendices/Appendix_A_Glossary.md) loop. The server and connection layer handles the actual network transport: accepting client connections, relaying order packets, recording replays, and managing game state transitions. This chapter covers the server architecture, the connection abstractions, and how packets are framed and dispatched.

## Learning Objectives


After studying this chapter, you should be able to:

- Explain the server roles: lobby host, order relay, sync aggregator, replay recorder, and game save manager.
- Describe the server trait system and how it allows custom server behavior.
- Trace the connection establishment and order packet framing process.
- Understand OrderBuffer scheduling and OrderLatency.
- Configure server settings, game speeds, and server traits in YAML.
- Implement a custom server trait for match commands or tournaments.

## Files

| File | Responsibility |
| :---- | :---- |
| `OpenRA.Game/Server/Server.cs` | Main server class: lobby, game start, order relay, game saves. |
| `OpenRA.Game/Server/Connection.cs` | Server-side connection wrapper. |
| `OpenRA.Game/Server/OrderBuffer.cs` | Buffers and schedules order packets per frame. |
| `OpenRA.Game/Network/Connection.cs` | Client-side `IConnection` implementations (`EchoConnection`, `NetworkConnection`). |
| `OpenRA.Game/Network/OrderIO.cs` | Low-level packet framing. |
| `OpenRA.Game/Network/ReplayConnection.cs` | Replays a recorded game as a fake connection. |
| `OpenRA.Game/Network/ReplayRecorder.cs` | Records game packets to a replay file. |
| `OpenRA.Game/Server/ProtocolVersion.cs` | Handshake protocol version constants. |
| `OpenRA.Game/Settings.cs` | Contains the nested `ServerSettings` class for server configuration (ports, name, dedicated mode, etc.). |
| `OpenRA.Game/Server/TraitInterfaces.cs` | Server trait interfaces (e.g., `IStartGame`, `IInterpretCommand`). |

![Architecture diagram](images/Part_09_Chapter_02_Server_Connection-architecture-diagram-showing-the-main-classes-interfaces-and-9161e6.svg)

## Architecture


### Server roles

The OpenRA server is a lightweight relay with some game-state awareness:

- **Lobby host:** validates clients, assigns player indices, enforces game settings, and synchronizes lobby state.
- **Order relay:** receives order packets from each client and forwards them to every other client.
- **Sync aggregator:** receives sync hashes from clients and forwards them so each client can detect desyncs.
- **Replay recorder:** records all dispatched packets so the game can be replayed later.
- **Game save manager:** stores game state so clients can resume a saved multiplayer game.

### Server trait system

The server uses a small trait system similar to the game world. [Server Traits](../appendices/Appendix_A_Glossary.md) are loaded from the mod manifest and implement interfaces such as `IStartGame`, `INotifySyncLobbyInfo`, and `IInterpretCommand`. This allows mods to add custom server behavior (e.g., match commands, auto-balance, tournaments) without modifying the core server.

### Client connection abstraction

`IConnection` is the client-side interface to the network:

```csharp
public interface IConnection : IDisposable
{
    int LocalClientId { get; }
    void StartGame();
    void Send(int frame, IEnumerable<Order> orders);
    void SendImmediate(IEnumerable<Order> orders);
    void SendSync(int frame, int syncHash, ulong defeatState);
    void Receive(OrderManager orderManager);
}
```

Two main implementations are provided:

- `NetworkConnection` — connects to a remote server over TCP.
- `EchoConnection` — local loopback used for single-player and skirmish games.

### Replay connection

`ReplayConnection` reads a recorded replay file and feeds the saved packets into the `OrderManager` as if they came from the network. This makes replays deterministic: the simulation is replayed from the same order stream.

![Data flow  code path diagram](images/Part_09_Chapter_02_Server_Connection-sequence-flow-diagram-tracing-the-execution-path-from-trigge-035864.svg)

## Data Flow / Code Path


### Connection establishment

1. The server listens on TCP sockets.
2. A client creates a `NetworkConnection` with the server's `ConnectionTarget`.
3. The client spins up connect threads for each endpoint and keeps the first successful connection.
4. After connecting, the server sends a handshake: protocol version and client ID.
5. The client enters the `Connected` state and starts a receive thread.

### Lobby setup and game start

The lobby is the phase between a successful handshake and the first simulation frame. It is coordinated by `Server` on the host side and mirrored in every client by `OrderManager` through a shared `LobbyInfo` state.

#### Lobby lifecycle

A typical lobby flows as follows:

1. **Create or join.** The host client selects "Create Game" and starts a local server, or a dedicated server is started from the command line. Other clients select "Join Game" and provide the server's address. See `OpenRA.Game/Server/Server.cs` for the server initialization path and `OpenRA.Game/Network/Connection.cs` for the client join path.
2. **Handshake and slot assignment.** After the TCP connection and protocol handshake, the server assigns a unique client index and broadcasts a `SyncLobbyInfo` order so every client sees the current list of players and slots. The server owns the authoritative `LobbyInfo`; clients apply updates sent by the server and may locally predict small changes such as selecting a color before the server confirms them.
3. **Map selection.** The host chooses a map from the map cache. The server validates the selected map by loading a `MapPreview` from the mod's map cache and checking that the map exists and is supported by the current mod and game version. Clients receive the map UID and metadata through the lobby sync; if a client does not have the map, the server may offer a map transfer via the `MapTransfer` server trait, or the client must download the map manually before the game can start.
4. **Game options.** The host sets game speed, crate frequency, starting units, and other mod-defined options. These are stored in `LobbyInfo.GlobalSettings` and synchronized with each lobby update. Clients render the options in the lobby UI but cannot change them unless the server grants them permission.
5. **Faction, team, and color selection.** Each client picks a faction, team, and color from the values allowed by the selected map and the server rules. The choices are sent to the server as lobby orders, validated (e.g., no duplicate color), and then broadcast. The server maps each client to a `Slot`; the slot determines the in-game player index, spawn point, and initial faction/team/color.
6. **Ready state.** Clients toggle a ready flag. The server may require all clients to be ready before starting, or the host may force a start. Bots are always considered ready.
7. **Game start.** When the start command is issued, the server transitions to `Launching`, runs `IStartGame` server traits, finalizes the `Session` data, and then broadcasts a `StartGame` order. Clients create a `[World](../appendices/Appendix_A_Glossary.md)` from the selected map and ruleset, and the server enters the `Playing` state. From this point on, orders are treated as simulation inputs and buffered by `OrderBuffer` for lock-step execution (see [Part 9.1 — OrderManager and Lockstep Foundation](Part_09_Chapter_01_OrderManager.md)).

#### Lobby state machine

`Server` tracks the current phase of a multiplayer session through a small state machine. The main states are:

- **Waiting.** The server is accepting connections and clients can modify lobby settings. The server listens for new connections, validates orders such as `SyncLobbyInfo`, `SetTeam`, and `SetReady`, and periodically broadcasts the lobby state to all clients.
- **Launching.** The server has received a valid start command and is finalizing the session before the first frame. New clients are rejected during this state, and lobby changes are blocked. The server runs `IStartGame` traits and prepares the initial order stream so all clients begin the simulation deterministically.
- **Playing.** The game is running. The server no longer accepts lobby changes; instead, it relays simulation orders via `OrderBuffer` and forwards sync packets. Clients drive their local `World` with the orders they receive.
- **ShuttingDown.** The server is closing, either because the host quit, the game ended, or a fatal error occurred. Existing connections are closed and no new connections are accepted.

![Server Connection State Machine](images/Part_09_Chapter_02_Server_Connection-server-state-machine.svg)

In the `Waiting` state, the server accepts connections and applies lobby changes. The `Launching` state locks the lobby and prepares the synchronized start. Once every client has created a `World` and the first frame begins, the server enters `Playing` and switches to relaying simulation orders. `ShuttingDown` ends the session and closes connections.

Key server traits that participate in the lobby are defined by the interfaces in `OpenRA.Game/Server/TraitInterfaces.cs` and implemented in `OpenRA.Game/Server/` and `OpenRA.Mods.Common/ServerTraits/`:

- `IStartGame` — called when the game is about to start; can finalize or reject the start.
- `INotifySyncLobbyInfo` — called when the lobby state is updated, allowing traits to enforce rules or inject additional state.
- `IInterpretCommand` — parses chat commands such as `/kick`, `/lock`, or `/start` and returns server orders that apply the result.
- `IClientJoined` — responds to a client joining before the game starts. (Client disconnects are handled by the server's connection-drop logic and `INotifyServerEmpty`, not a dedicated lobby trait.)

#### Slot and spawn assignment

The `Slot` class (`OpenRA.Game/Network/Session.cs`, nested `Slot` class) describes one playable position on the map. Each slot is tied to a `PlayerReference` from the map YAML and carries fields such as `PlayerReference`, `Closed`, `AllowBots`, `LockFaction`, `LockColor`, and `LockSpawn`. The client occupying a slot is a separate `Client` record whose `Slot` field holds the slot ID and which carries the per-player `Color`, `Faction`, `SpawnPoint`, and `Bot` values. A slot can be in one of several states:

| Slot state | Meaning |
| :---- | :---- |
| **Open** | Available for a human client to join. |
| **Occupied** | A human client has claimed the slot; the client's `Slot` field references this slot's ID in `LobbyInfo`. |
| **Bot** | The slot is filled by a bot; the occupying client's `Bot` field names the bot controller type. |
| **Closed** | The slot is disabled by the host and will not be used in the match. |
| **Spectator** | The client is not assigned to a slot; spectators observe the game and do not own actors. |

When a client claims a slot, the server sets that client's `Slot` field to the slot ID, assigns its `SpawnPoint`, and broadcasts the new lobby state. The spawn point for each player is derived from the map's `Spawn` actors and the slot order; the server does not send a separate spawn list but relies on every client resolving the same `SpawnPoint` index from the agreed slot assignment. Because the slot assignment is deterministic and synchronized before start, every client creates the same `Player` array in `World` and assigns actors to the same owners.

#### Map selection and validation

The map is the most important piece of shared state in the lobby. On the client side, `MapPreview` (`OpenRA.Game/Map/MapPreview.cs`) is a lightweight, cacheable summary of a map that includes the title, author, size, player count, spawn points, and a minimap thumbnail. On the server side, the host's map selection is converted to a `MapPreview` UID, and the server loads the full map rules to verify that the requested player count and slot layout match the connected clients.

When the host changes the map:

1. The server looks up the map UID in the mod map cache.
2. The server validates that the map supports the current number of human and bot players, that no required asset is missing, and that the map's ruleset version matches the mod.
3. The server sends a `SyncLobbyInfo` order containing the new map UID, title, and player-count information.
4. Each client checks whether it already has the map in its local cache. If not, the client requests the map data from the server using the `MapTransfer` order flow if the server supports it, or the client is forced to leave the lobby and acquire the map externally.
5. The game cannot start until every client has a validated copy of the selected map, because even tiny differences in map YAML or tile definitions would cause an immediate desync.

#### Chat and orders during the lobby

Lobby chat uses the same `Order` system as gameplay chat, but with `IsImmediate = true`. When a player types a message, the client creates a `Chat` order and sends it via `Connection.SendImmediate`. The server receives it, optionally runs it through `IInterpretCommand` traits (for slash commands), and forwards the chat order to all clients. Clients display the text in the lobby UI and, if the command was interpreted by the server, apply the resulting server orders such as `SetTeam` or `KickClient`.

Pre-game lobby actions are also represented as orders. Examples include:

- `SyncLobbyInfo` — server-to-client broadcast of the entire lobby state.
- `SetTeam` — a client asks to change team.
- `SetReady` — a client toggles ready state.
- `SetFaction` / `SetColor` — cosmetic and strategic choices assigned to a slot.
- `StartGame` — server-to-client signal that the world should be created.
- `MapTransfer` — server-to-client transfer of missing map data.

These orders are handled by `UnitOrders.ProcessOrder` on the client side, while the server validates them in `OpenRA.Game/Server/Server.cs` and the relevant server traits before relaying them.

### Order packet framing

Each packet sent over TCP is length-prefixed:

```csharp
ms.Write(packet.Length);
ms.Write(packet);
```

The receive thread reads the 4-byte length, then the payload bytes, then enqueues the packet for processing.

### Server order relay

When a client sends an order packet:

1. The server receives the length, client ID, and payload.
2. The server asks `OrderBuffer` to schedule the packet for the appropriate frame.
3. When the frame is due, the server dispatches the packet to every other client.
4. The server also records the packet in the replay recorder.

```csharp
public void DispatchOrdersToClients(Connection conn, int frame, byte[] data)
{
    var from = conn.PlayerIndex;
    var frameData = CreateFrame(from, frame, data);
    foreach (var c in Conns)
        if (c != conn)
            DispatchFrameToClient(c, from, frameData);

    RecordOrder(frame, data, from);
}
```

### Order latency

The server uses a fixed `OrderLatency` (in frames) to give all clients time to receive and process orders. At game start, the server injects empty order packets for the first few frames so the client can begin simulation immediately.

```csharp
for (var i = 0; i < OrderLatency; i++)
{
    from.LastOrdersFrame = firstFrame + i;
    var frameData = CreateFrame(from.PlayerIndex, from.LastOrdersFrame, []);
    foreach (var to in conns)
        DispatchFrameToClient(to, from.PlayerIndex, frameData);

    RecordOrder(from.LastOrdersFrame, [], from.PlayerIndex);
}
```

### OrderBuffer

`OrderBuffer` is the server-side scheduler. It keeps a per-client queue of incoming packets and releases them on the correct frame. This ensures that clients receive orders in the same order and at the same logical time.

### Sync packet relay

Sync packets are not sent as separate packets. Instead, they are bundled with the next order packet sent by the client:

```csharp
void Send(byte[] packet)
{
    var ms = new MemoryStream();
    ms.Write(packet.Length);
    ms.Write(packet);

    foreach (var s in queuedSyncPackets)
    {
        var q = OrderIO.SerializeSync(s);
        ms.Write(q.Length);
        ms.Write(q);
        sentSync.Enqueue(s);
    }

    queuedSyncPackets.Clear();
    ms.WriteTo(tcp.GetStream());
}
```

The server forwards these sync packets to all clients.

### Game save

When a game save is created, the server records the state and the current order stream. On restart, the server replays the saved orders up to the last sync frame and then resumes normal relay. This allows multiplayer campaigns or long games to be resumed.

![Configuration (yaml) diagram](images/Part_09_Chapter_02_Server_Connection-annotated-yaml-snippet-diagram-showing-the-key-fields-and-ho-6a1b98.svg)

## Configuration (YAML)


### Server settings

Server settings are loaded from `settings.yaml` and include:

- `Name` — server name shown in the lobby browser.
- `ListenPort` — TCP port(s) to listen on.
- `Dedicated` — whether the server runs in dedicated mode.
- `EnableSingleplayer` — allow single-player games hosted on the server.
- `EnableSyncReports` — forward detailed sync reports to clients.
- `EnableGameSaves` — allow multiplayer game saves.

### Game speed

Game speed is defined in the mod's `GameSpeeds` YAML:

```yaml
GameSpeeds:
    DefaultSpeed: normal
    Speeds:
        normal:
            Name: Normal
            Timestep: 40
            OrderLatency: 3
```

`Timestep` is the frame interval in milliseconds; `OrderLatency` is the number of frames the server buffers orders.

### Server traits

Server traits are declared in the mod manifest:

```yaml
ServerTraits:
    - OpenRA.Mods.Common.ServerTraits.PlayerMessageTracker
    - OpenRA.Mods.Common.ServerTraits.VoteKickTracker
    - OpenRA.Mods.Common.ServerTraits.MasterServerPinger
```

## Interconnectivity

- **Depends on:** [Part 9.1 — OrderManager and Lockstep Foundation](Part_09_Chapter_01_OrderManager.md) (OrderManager, lockstep, and order relay), [Part 1.3 — World, OrderManager, and Orders](Part_01_Chapter_03_World_Orders.md) (World, Order, and the order pipeline), [Part 2.1 — MiniYaml Parser](Part_02_Chapter_01_MiniYaml.md) (MiniYaml for lobby and game settings), [Part 3.1 — Mod SDK and Project Structure](Part_03_Chapter_01_Mod_SDK.md) (ModData and manifest).
- **Used by:** [Part 9.3 — Sync Hashing and Determinism](Part_09_Chapter_03_Sync_Hashing.md) (sync packets are relayed), [Part 8.1 — Bot Architecture and IBot](Part_08_Chapter_01_IBot.md) (bot orders are relayed like human orders), [Part 10.2 — Online Services and References](Part_10_Chapter_02_Online_References.md) (multiplayer ecosystem).
- **Lobby flow:** The lobby lifecycle described in this chapter is the bridge between the connection handshake in `OpenRA.Game/Server/Server.cs` and the lockstep simulation in `OrderManager`. Slot assignment and map validation happen in the server; the resulting `StartGame` order triggers the `World` creation and order processing described in [Part 1.3 — World, OrderManager, and Orders](Part_01_Chapter_03_World_Orders.md) and [Part 9.1 — OrderManager and Lockstep Foundation](Part_09_Chapter_01_OrderManager.md).

![Algorithms diagram](images/Part_09_Chapter_02_Server_Connection-algorithm-diagram-or-pseudocode-flowchart-for-the-non-trivia-5983ed.svg)

## Algorithms


### Frame creation

`CreateFrame` wraps a client ID, frame number, and payload into a single byte array:

```csharp
void DispatchOrdersToClient(Connection c, int client, int frame, byte[] data)
{
    DispatchFrameToClient(c, client, CreateFrame(client, frame, data));
}
```

The frame format is read by `OrderIO` and `Order.Deserialize` on the client.

### Connection quality tracking

The server periodically sends `SyncConnectionQuality` orders to clients with ping and connection quality data. This is used by the UI to display latency indicators.

### Vote kick and chat

Server traits such as `VoteKickTracker` and `PlayerMessageTracker` handle chat commands and vote kicks. They interpret chat messages and dispatch server orders to enforce the result.

### Master server pinger

`MasterServerPinger` is a server trait that registers the server with the public master server list and periodically updates its status. This is how the in-game server browser discovers dedicated servers.

![Extension points diagram](images/Part_09_Chapter_02_Server_Connection-extension-hook-diagram-showing-the-interface-s-to-implement-b4a27b.svg)

## Extension Points


### Add a server trait

Implement one of the server trait interfaces (e.g., `IStartGame`, `IInterpretCommand`, `INotifySyncLobbyInfo`) and register the trait in the mod manifest. The server will call it at the appropriate lifecycle points.

### Custom network connection

Implement `IConnection` to add a new transport (e.g., WebSockets, UDP-based protocol). The rest of the game does not need to change because `OrderManager` only depends on `IConnection`.

### Custom replay format

`ReplayRecorder` and `ReplayConnection` define the replay format. A custom replay format would require subclassing or replacing these, but the in-game replay format is well-established.

### Custom game save logic

`GameSave` is managed by the server. Mods can extend the saved state by adding server-side traits that participate in the save/load lifecycle.

![Common pitfalls  guardrails diagram](images/Part_09_Chapter_02_Server_Connection-checklist-infographic-style-diagram-summarizing-the-top-pitf-fb069e.svg)

## Common Pitfalls / Guardrails


- **Protocol version:** the server and client must agree on `ProtocolVersion.Handshake`. A mismatch causes immediate disconnect.
- **Order latency:** latency must be high enough to cover network jitter but low enough to feel responsive. Too low causes frequent stalls; too high adds input lag.
- **Empty packets:** clients require an order packet every frame, even if empty. The server must inject empty packets when a client has nothing to send.
- **Disconnect markers:** client disconnects are handled as special disconnect packets so all clients process the disconnect on the same frame.
- **Replay recording:** the server records packets it relays. If the server does not relay a packet (e.g., a direct server order), it must record it separately.
- **Dedicated server state:** dedicated servers have no local world; they only relay and record. They must not run simulation logic.

### Common lobby issues

- **Version mismatch.** The client and server must agree on `ProtocolVersion.Handshake` and the mod version. If a client joins with a different release, the server rejects the connection during the handshake. Keep all clients on the same mod and engine version.
- **Map not found.** If a client joins a lobby whose selected map is not in the local map cache, the client cannot start the game. The server may offer a map transfer if the `MapTransfer` server trait is enabled; otherwise, the client must download the map manually and rejoin.
- **Slot mismatch.** A map may not have enough slots for all human and bot players, or the host may have closed slots after a client joined. The server validates slot counts before starting and will refuse to launch until the configuration matches the map's player layout.
- **NAT / firewall blocking.** OpenRA uses direct TCP connections between clients and the server. If the server is behind NAT or a firewall without port forwarding, remote clients cannot connect. Dedicated servers typically need the `ListenPort` forwarded; local hosts can use UPnP or the OpenRA master server relay if available in the mod.
- **Player dropping before start.** If a ready player disconnects while the server is in the `Launching` state, the server may abort the start and return to `Waiting`, or it may fall back to a bot if the slot supports it. Hosts should confirm all players are stable before starting, especially on large maps or with many spectators.

## What to read next

- [Part 9.1 — OrderManager and Lockstep Foundation](Part_09_Chapter_01_OrderManager.md) for the client-side lockstep loop that consumes server-relayed orders.
- [Part 9.3 — Sync Hashing and Determinism](Part_09_Chapter_03_Sync_Hashing.md) for the sync packets the server forwards after each frame.
- [Part 10.2 — Online Services and References](Part_10_Chapter_02_Online_References.md) for master server advertisement and server browser integration.

## Summary

This chapter explains the server and connection layer that transports [orders](../appendices/Appendix_A_Glossary.md) and game state between clients during a multiplayer match.

After reading this chapter, you should be able to:

- The server listens on TCP sockets.
- A client creates a `NetworkConnection` with the server's `ConnectionTarget`.
- The client spins up connect threads for each endpoint and keeps the first successful connection.
- After connecting, the server sends a handshake: protocol version and client ID.
- The client enters the `Connected` state and starts a receive thread.

If any of the concepts above feel unclear, review the relevant section before continuing. For source files and further reading, see the References section.


## References

- `OpenRA.Game/Server/Server.cs` — main server; lobby state machine, handshake, slot and map validation, order relay, and game start.
- `OpenRA.Game/Server/Connection.cs` — server-side connection wrapper.
- `OpenRA.Game/Network/Session.cs` — lobby `Client` metadata, `Slot` definitions, and spawn assignment.
- `OpenRA.Game/Player.cs` — runtime player object created after the game starts.
- `OpenRA.Game/Server/OrderBuffer.cs` — server-side order scheduling.
- `OpenRA.Game/Network/Connection.cs` — client-side `IConnection` implementations (`EchoConnection`, `NetworkConnection`).
- `OpenRA.Game/Network/OrderManager.cs` — client-side coordinator for lobby and in-game orders; see [Part 9.1 — OrderManager and Lockstep Foundation](Part_09_Chapter_01_OrderManager.md).
- `OpenRA.Game/Network/Order.cs` — `Order` object, serialization, and immediate vs. gameplay orders.
- `OpenRA.Game/Network/OrderIO.cs` — packet framing.
- `OpenRA.Game/Network/UnitOrders.cs` — system-level order handlers for chat, lobby sync, and game state.
- `OpenRA.Game/Network/ReplayConnection.cs` — replay playback.
- `OpenRA.Game/Network/ReplayRecorder.cs` — replay recording.
- `OpenRA.Game/Server/ProtocolVersion.cs` — handshake protocol.
- `OpenRA.Game/Settings.cs` — nested `ServerSettings` class for server configuration.
- `OpenRA.Game/Server/TraitInterfaces.cs` — server trait interfaces (`IStartGame`, `IInterpretCommand`, `INotifySyncLobbyInfo`, etc.).
- `OpenRA.Mods.Common/ServerTraits/*.cs` — common server trait implementations (`LobbyCommands`, `MasterServerPinger`, `PlayerPinger`, `SkirmishLogic`).
- `OpenRA.Game/Server/` — additional server-side trackers such as `VoteKickTracker` and `PlayerMessageTracker`.
- `OpenRA.Game/Map/MapPreview.cs` — lightweight, cacheable map summary used by clients and the server for validation.