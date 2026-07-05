# Chapter 6.4 — Crypto Utilities and Player Authentication

## Purpose

OpenRA uses a small set of cryptographic utilities for player authentication, server verification, and replay/game-save integrity. The operations are deliberately simple: RSA public-key signing, SHA1 hashing, and PEM key encoding. This chapter covers the `CryptoUtil` class and how the player profile system uses these primitives.

## Learning Objectives


After studying this chapter, you should be able to:

- Explain the cryptographic primitives used by OpenRA (RSA, SHA1, PEM).
- Describe how player identity is derived from a public key fingerprint.
- Trace the authentication flow from handshake to signature verification.
- Encode and decode PEM public keys and compute SHA1 fingerprints.
- Configure PlayerDatabase and ServerSettings authentication options.
- Recognize the security limitations of SHA1 and the appropriate use cases for crypto in OpenRA.

## Files

| File | Responsibility |
| :---- | :---- |
| `OpenRA.Game/CryptoUtil.cs` | RSA key encoding/decoding, signing, verification, SHA1 hashing, PEM helpers. |
| `OpenRA.Game/PlayerProfile.cs` | Player profile data including fingerprint, public key, and badges. |
| `OpenRA.Game/PlayerDatabase.cs` | Loads player badges and profile data from the forum server. |
| `OpenRA.Game/Network/Handshake.cs` | Server handshake that exchanges public keys and signatures. |
| `OpenRA.Game/Network/Session.cs` | Lobby session containing client public keys and fingerprints. |
| `OpenRA.Game/Server/Server.cs` | Server-side validation of signed client data. |
| `OpenRA.Game/Network/GameServer.cs` | Game server listing with optional fingerprint/signature fields. |
| `OpenRA.Test/OpenRA.Game/Sha1Tests.cs` | Unit tests for SHA1 hashing. |

![Architecture diagram](images/Part_06_Chapter_04_Crypto-architecture-diagram-showing-the-main-classes-interfaces-and-9161e6.svg)

## Architecture


### Crypto primitives

`CryptoUtil` is a static helper class with three categories of functions:

1. **Key encoding** — `EncodePEMPublicKey`, `DecodePEMPublicKey`, `PublicKeyFingerprint`.
2. **Signing/verification** — `Sign`, `VerifySignature` using RSA with SHA1.
3. **Hashing** — `SHA1Hash` for streams, byte arrays, and strings.

All cryptographic operations use .NET's `RSACryptoServiceProvider` with SHA1.

### Player identity

Player identity is based on an RSA public key. The **fingerprint** of a key is the SHA1 hash of the key's modulus and exponent bytes:

```csharp
public static string PublicKeyFingerprint(RSAParameters parameters)
{
    return SHA1Hash(parameters.Modulus.Append(parameters.Exponent).ToArray());
}
```

This fingerprint is used to identify players consistently across sessions and to verify that a player's public key has not changed.

### Authentication flow

1. A player generates or loads an RSA key pair.
2. The client sends the public key to the server during the handshake.
3. The server sends a challenge or a session token.
4. The client signs the challenge with its private key and sends the signature back.
5. The server verifies the signature against the public key and fingerprint.
6. The server can then look up the player's profile in the forum database using the fingerprint.

![Data flow  code path diagram](images/Part_06_Chapter_04_Crypto-sequence-flow-diagram-tracing-the-execution-path-from-trigge-035864.svg)

## Data Flow / Code Path


### RSA key encoding

Public keys are exchanged in PEM format. `EncodePEMPublicKey` builds an ASN.1 DER structure and base64-encodes it with PEM header/footer:

```csharp
public static string EncodePEMPublicKey(RSAParameters parameters)
{
    var data = Convert.ToBase64String(EncodePublicKey(parameters));
    var output = new StringBuilder();
    output.AppendLine("-----BEGIN PUBLIC KEY-----");
    for (var i = 0; i < data.Length; i += 64)
        output.AppendLine(data.Substring(i, Math.Min(64, data.Length - i)));
    output.Append("-----END PUBLIC KEY-----");

    return output.ToString();
}
```

`DecodePEMPublicKey` parses the ASN.1 structure to extract the modulus and exponent.

### Signing data

```csharp
public static string Sign(RSAParameters parameters, byte[] data)
{
    using (var rsa = new RSACryptoServiceProvider())
    {
        rsa.ImportParameters(parameters);
        return Convert.ToBase64String(rsa.SignHash(SHA1.HashData(data), CryptoConfig.MapNameToOID("SHA1")));
    }
}
```

The data is first SHA1-hashed, then signed with RSA PKCS#1 v1.5.

### Verifying a signature

```csharp
public static bool VerifySignature(RSAParameters parameters, byte[] data, string signature)
{
    using (var rsa = new RSACryptoServiceProvider())
    {
        rsa.ImportParameters(parameters);
        return rsa.VerifyHash(SHA1.HashData(data), CryptoConfig.MapNameToOID("SHA1"), Convert.FromBase64String(signature));
    }
}
```

### SHA1 hashing

```csharp
public static string SHA1Hash(byte[] data)
{
    return ToHex(SHA1.HashData(data), true);
}
```

Hashes are returned as lowercase hex strings.

### Player profile lookup

`PlayerProfile` stores the fingerprint and public key for an authenticated player. `PlayerDatabase` loads additional profile data (name, rank, badges) from the OpenRA forum server. Badges are loaded asynchronously and cached in a [sprite](../appendices/Appendix_A_Glossary.md) sheet.

![Configuration (yaml) diagram](images/Part_06_Chapter_04_Crypto-annotated-yaml-snippet-diagram-showing-the-key-fields-and-ho-6a1b98.svg)

## Configuration (YAML)


### Player database endpoint

The `PlayerDatabase` URL is configured in the mod's global mod data:

```yaml
PlayerDatabase:
    Profile: https://forum.openra.net/openra/info/
    IconSize: 24
```

### Server authentication

Server settings in `ServerSettings` control whether authentication is required:

```yaml
ServerSettings:
    RequireAuthentication: false
    EnableGeoIP: true
    ...
```

## Interconnectivity

- **Depends on:** [Part 2.1 — MiniYaml Parser](Part_02_Chapter_01_MiniYaml.md), [Part 3.1 — Mod SDK and Project Structure](Part_03_Chapter_01_Mod_SDK.md), [Part 6.3 — Virtual File System](Part_06_Chapter_03_VFS.md), [Part 4.3 — Widgets and Chrome](Part_04_Chapter_03_Widgets.md).
- **Used by:** [Part 9.2 — Server and Connection Layer](Part_09_Chapter_02_Server_Connection.md), Part 10 (online services and authentication ecosystem).

![Algorithms diagram](images/Part_06_Chapter_04_Crypto-algorithm-diagram-or-pseudocode-flowchart-for-the-non-trivia-5983ed.svg)

## Algorithms


### ASN.1 DER encoding

`EncodePublicKey` manually constructs a DER-encoded SubjectPublicKeyInfo structure:

1. Outer `SEQUENCE`.
2. Algorithm identifier `SEQUENCE` with the RSA OID header.
3. `BIT STRING` containing the inner `SEQUENCE`.
4. Inner `SEQUENCE` with two `INTEGER`s: modulus and exponent.

The modulus and exponent are padded with a leading zero byte to prevent them from being interpreted as negative numbers in ASN.1 INTEGER encoding.

### TLV length encoding

```csharp
static void WriteTLVLength(BinaryWriter writer, int length)
{
    if (length < 0x80)
        writer.Write((byte)length);
    else
    {
        var lengthBytes = BitConverter.GetBytes(length).Reverse().SkipWhile(b => b == 0).ToArray();
        writer.Write((byte)(0x80 | lengthBytes.Length));
        writer.Write(lengthBytes);
    }
}
```

This implements ASN.1 length encoding for DER.

### Fingerprint computation

The public key fingerprint is simply the SHA1 of the concatenated modulus and exponent bytes:

```csharp
return SHA1Hash(parameters.Modulus.Append(parameters.Exponent).ToArray());
```

This is deterministic and stable, so the same key always produces the same fingerprint.

![Extension points diagram](images/Part_06_Chapter_04_Crypto-extension-hook-diagram-showing-the-interface-s-to-implement-b4a27b.svg)

## Extension Points


### Add a new hash algorithm

Add a new helper method to `CryptoUtil`. If the hash is used for sync or file identity, ensure it is deterministic and consistent across platforms.

### Custom authentication providers

`PlayerDatabase` is a global mod data object. A custom mod could replace it with a subclass that loads profiles from a different service.

### Server-side verification

Server traits can use `CryptoUtil.VerifySignature` to validate signed orders or admin commands. This is how vote-kick and authentication commands are verified.

![Common pitfalls  guardrails diagram](images/Part_06_Chapter_04_Crypto-checklist-infographic-style-diagram-summarizing-the-top-pitf-fb069e.svg)

## Common Pitfalls / Guardrails


- **SHA1 is not collision-resistant:** while OpenRA uses SHA1 for fingerprints and signatures, it is not suitable for new security-critical use cases. The existing use is acceptable because the data is not high-value.
- **RSA key size:** `RSACryptoServiceProvider` defaults to a 1024-bit key on older .NET versions. Ensure keys are large enough for your security needs.
- **Private key storage:** private keys are stored on the client machine. They must be protected from unauthorized access by the operating system.
- **Signature verification:** always verify signatures before trusting data from the network. The server does this during authentication.
- **Badges async loading:** badges are loaded asynchronously from the network. UI code must handle the case where a badge is not yet available.
- **Do not use crypto for gameplay:** cryptographic operations are not deterministic enough for the simulation. Never include signature verification or hash results in sync state.

## What to read next

- [Part 6.3 — Virtual File System](Part_06_Chapter_03_VFS.md) for how badge textures and other assets are mounted and loaded.
- [Part 9.2 — Server and Connection Layer](Part_09_Chapter_02_Server_Connection.md) for the handshake that uses the crypto primitives covered here.
- [Part 10.2 — Online Services and References](Part_10_Chapter_02_Online_References.md) for the online-services ecosystem that player authentication plugs into.

## Summary

This chapter explains the cryptographic utilities OpenRA uses for player authentication, server verification, and replay/game-save integrity.

After reading this chapter, you should be able to:

- **Key encoding** — `EncodePEMPublicKey`, `DecodePEMPublicKey`, `PublicKeyFingerprint`.
- **Signing/verification** — `Sign`, `VerifySignature` using RSA with SHA1.
- **Hashing** — `SHA1Hash` for streams, byte arrays, and strings.

If any of the concepts above feel unclear, review the relevant section before continuing. For source files and further reading, see the References section.


## References

- `OpenRA.Game/CryptoUtil.cs` — cryptographic utilities.
- `OpenRA.Game/PlayerProfile.cs` — player profile data.
- `OpenRA.Game/PlayerDatabase.cs` — profile and badge loading.
- `OpenRA.Game/Network/Handshake.cs` — handshake with key exchange.
- `OpenRA.Game/Network/Session.cs` — lobby session keys.
- `OpenRA.Game/Server/Server.cs` — server-side validation.
- `OpenRA.Game/Network/GameServer.cs` — server listings.
- `OpenRA.Test/OpenRA.Game/Sha1Tests.cs` — SHA1 tests.