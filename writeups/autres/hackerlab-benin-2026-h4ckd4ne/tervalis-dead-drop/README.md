---
title: "Operation Tervalis · Dead Drop (AIZEN Package 01)"
platform: "HackerLab Benin 2026 (H4ckd4ne)"
category: "forensics-crypto"
difficulty: "—"
points: 100
os: "—"
date: 2026-11-20
author: "Unpasswd"
author_github: "H4ckd4ne"
source: "https://github.com/H4ckd4ne/hackerlab2026-writeups/blob/main/operation-tervalis/dead-drop-aizen-package-01/writeup-aizen.md"
license: "CC BY-SA 4.0"
status: published
---

# AIZEN — Operation Tervalis, Package 01 (Cryptographic Dead Drop)

## Objective

- **Category:** Forensics / Cryptography
- **Briefing:** `challenge/BRIEFING.md` (REF NV-OPS-2024-TERV-PKG01, 2024-11-04)
- **Initial state:** Five NorvethSecure v3 network captures (`session_01.pcapng`–`session_05.pcapng`), protocol documentation (`protocol_v3.md`), message schema (`message_schema.json`), session metadata (`session_metadata.csv`), and a known-plaintext sample (`known_messages.json`).
- **Goal:** Recover the content of Agent AVALD's (SUBJ-7742) communications to determine what he reported to HQ before going silent.

## Provided artifacts

| File | Purpose |
| --- | --- |
| `session_01..05.pcapng` | TCP captures of NorvethSecure v3 sessions (port 8443) |
| `protocol_v3.md` | AES-256-GCM, X25519/HKDF key schedule, deterministic nonces, CBOR framing, reconnect behavior |
| `message_schema.json` | CBOR frame: `[session_id(16), key_id(4), nonce(12), ciphertext, tag(16)]` |
| `session_metadata.csv` | Session IDs, time ranges, key IDs, endpoints, reconnect flags |
| `known_messages.json` | Confirmed plaintext for `session_01`, `message_index` 20, `key_id` 00000003, `counter` 0 (HEARTBEAT) |

## Reconnaissance

### 1. Session mapping (`session_metadata.csv`)

- AVALD used a single logical session `461f78d8f1ff94722365090c919ec194` across `session_01` (2024-11-02 07:30–09:15Z), `session_02` (reconnect, 09:15–10:45Z), and `session_03` (reconnect, 2024-11-03 13:00–15:00Z), all `10.42.1.5 -> 10.42.1.15`, key IDs `0x01/02/03`.
- `session_04` (`8f9e...`, 10.42.4.20) and `session_05` (`7f39...`, 10.42.6.10) are different agents/sessions.

The objective targets AVALD, so analysis focused on sessions 01–03.

### 2. Protocol review (`protocol_v3.md`)

- Key derivation: `key = HKDF-SHA-256(IKM=master_secret, salt=session_id, info="NorvethSecure-v3-key-" || key_id_bytes, L=32)`.
- Nonce derivation (per spec): `nonce = HKDF-SHA-256(IKM=key, salt=None, info="NorvethSecure-v3-nonce-" || counter_be32, L=12)`, counter monotonic per key and **must persist across reconnections**.
- Transport: CBOR array `[session_id, key_id, nonce, ciphertext, tag]` over TCP/8443.
- Key IDs: `0x01` general, `0x02` reports, `0x03` priority.

Critical note: reconnects reuse the same `session_id` and master secret; if counter state is not persisted, (key,nonce) pairs repeat → AES-GCM keystream/nonce reuse.

### 3. Known plaintext (`known_messages.json`)

One sample: session `461f...`, `session_01`, `message_index` 20, `key_id` 00000003, `counter` 0.

```json
{"type":"HEARTBEAT","seq":20,"ts":"2024-11-02T08:30:00Z","pad":"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"}
```

### 4. Traffic extraction

CBOR frames were reassembled from TCP payloads and decoded with `cbor2`/Scapy:

```python
import io, cbor2
from scapy.all import rdpcap, TCP, Raw
from collections import defaultdict

def extract_messages(pcap_path):
    pkts = rdpcap(pcap_path)
    flows = defaultdict(bytearray)
    for p in pkts:
        if TCP in p and Raw in p:
            f = (p['IP'].src, p[TCP].sport, p['IP'].dst, p[TCP].dport)
            flows[f].extend(bytes(p[Raw].load))
    msgs = []
    for f, data in flows.items():
        bio = io.BytesIO(bytes(data))
        while bio.tell() < len(data):
            try:
                msgs.append(cbor2.load(bio))
            except Exception:
                break
    return msgs
```

Message counts: `session_01`=30, `session_02`=18, `session_03`=20, `session_04`=12, `session_05`=10. Frame layout matched the schema (e.g. s01[0]: sid `461f...`, key `00000001`, 12-byte nonce, 142-byte ciphertext, 16-byte tag).

Verification: `session_01` index 20 had `key_id=00000003`, nonce `3621143eb98c4e1dd8a794e0`, ciphertext length 166 — consistent with the sample.

## Analysis — nonce reuse across reconnection

Nonces were grouped per `key_id` per AVALD session:

| key_id | s01 | s02 | s03 | reused s01∩s02 | reused s01∩s03 | reused s02∩s03 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 00000001 | 10 | 10 | 8 | 0 | 0 | 0 |
| 00000002 | 10 | 8 | 5 | 0 | 0 | 0 |
| 00000003 | 10 | 0 | 7 | 0 | **7** | 0 |

All 7 priority-channel (`00000003`) messages in `session_03` reused nonces with `session_01` key-03 messages, despite the spec requiring counter persistence across reconnects. Same `session_id`/master secret ⇒ same derived key; same nonce ⇒ identical AES-GCM keystream for each reused pair.

### Reused pairs (nonce → indices)

| nonce | s01 idx | s03 idx | ct len s01 | ct len s03 |
| --- | ---: | ---: | ---: | ---: |
| 361ac2d1e48069976fdddbfd | 21 | 14 | 166 | 151 |
| 3621143eb98c4e1dd8a794e0 | 20 | 13 | 166 | 152 |
| 3c1376a7118cdec259f57d54 | 22 | 15 | 166 | 149 |
| 6b64b858cd6c689957efa01a | 26 | 19 | 166 | 166 |
| 8017b4c3496028bd1bf8acef | 23 | 16 | 166 | 131 |
| 862fd4b25776392563ac665b | 24 | 17 | 166 | 128 |
| b52ee89ffd0bc5787c04d388 | 25 | 18 | 166 | 75 |

## Exploitation — keystream recovery and decryption

For AES-GCM, `C = P ⊕ KS` under a fixed (key,nonce). With a known plaintext/ciphertext pair, `KS = P ⊕ C`, so a second ciphertext under the same (key,nonce) yields `P' = C' ⊕ KS`.

### Direct recovery (s01 idx 20 ↔ s03 idx 13)

Using the provided heartbeat plaintext for s01 idx 20 (len 166) against s03 idx 13 (len 152, truncated to keystream length):

```python
known_plain = b'{"type":"HEARTBEAT","seq":20,"ts":"2024-11-02T08:30:00Z","pad":"AAAAAAAA..."}'
ks  = bytes(a^b for a,b in zip(known_plain, ct1_20))
pt3 = bytes(a^b for a,b in zip(ks, ct3_13[:len(ks)]))
```

Recovered (TIMS, HIGH alert): suspicious activity near hotel position, black vehicle approaching slowly from north (seq 13).

### Recovering remaining pairs

All s01 key-03 messages (indices 20–29) share ciphertext length 166, matching the heartbeat structure. Assuming the same template `{"type":"HEARTBEAT","seq":<idx>,"ts":"<ISO8601>Z","pad":"AAA..."}` (pad adjusted to length) and searching plausible timestamps around 2024-11-02T08:30:00Z, candidate plaintexts were scored by printability/JSON validity of the resulting `P3 = C3 ⊕ (P1 ⊕ C1)`. Each of the six remaining pairs produced a fully printable, coherent JSON message at a best-scoring timestamp guess.

Recovered `session_03` priority-channel messages (agent TIMS / operational traffic on 2024-11-03):

- **idx 13 (STATUS/ALERT):** suspicious activity near hotel position, black vehicle approaching from north, plate identified (redacted; see validation).
- **idx 14 (STATUS, alert):** armed individuals exiting vehicle, plate identified.
- **idx 15 (DISTRESS):** last known position transmitted (coordinates present), tactical team converging.
- **idx 16 (DISTRESS):** AVALD/Valdoria identified, being detained by armed tactical unit, losing contact.
- **idx 17 (FINAL):** final channel message containing la valeur soumise on channel DELTA (redacted here per reporting rules).
- **idx 18 (ACK):** acknowledgement/ref received by OPS-CENTER.
- **idx 19 (HEARTBEAT):** heartbeat, ts 2024-11-03T14:12:00Z.

(Exact recovered texts, including the value embedded in idx 17, were preserved in-memory for submission/validation and are intentionally redacted from this document.)

## Failed / dead-end paths

- **Deriving keys/nonces from spec:** X25519 master secret is not in captures; HKDF-based nonce derivation cannot be reproduced without it. However, frames carry the nonce bytes directly, so derivation was unnecessary once reuse was observed.
- **Other key IDs / sessions:** `00000001` and `00000002` showed no nonce collisions across s01–s03; `session_04/05` belong to different `session_id`s (different agents), out of scope for AVALD's report.
- **GCM auth-key recovery/forgery:** Reuse in principle allows GHASH key recovery, but decryption via known-plaintext XOR was sufficient and non-invasive.

## Reproducible validation

1. Extract CBOR messages from `challenge/session_01.pcapng` and `challenge/session_03.pcapng` (Scapy + `cbor2` as above).
2. Filter frames where `key_id == b"\x00\x00\x00\x03"` and confirm 7 nonce collisions between s01 and s03 (matching the table above); confirm s01 idx 20 nonce matches the known sample.
3. For s01 idx 20, XOR the provided known plaintext with `ciphertext[20]` to obtain the keystream, then XOR with `ciphertext_s3[13]` to recover the seq-13 alert (printable JSON naming TIMS and the approaching vehicle).
4. For each remaining collided pair, model s01 plaintext as the heartbeat template with the same `seq` as the s01 index and a searched timestamp/pad to match length 166; select the candidate whose XOR-decrypt of s03 is fully printable JSON. This deterministically yields the STATUS/DISTRESS/FINAL/ACK/HEARTBEAT sequence above.
5. Confirm the FINAL message (s03 idx 17, channel DELTA) contains la valeur soumise in its `msg` field; submit that value via the challenge bridge and verify acceptance. (Value redacted here as "la valeur soumise".)

## Conclusion

Agent AVALD/TIMS' final priority-channel traffic (session_03, 2024-11-03) was recoverable because a reconnect failed to persist the per-key nonce counter, reusing seven AES-GCM (key,nonce) pairs with session_01. Known-plaintext keystream recovery on the priority channel exposed the arrest sequence and the final transmitted message containing la valeur soumise.
