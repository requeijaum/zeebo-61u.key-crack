#!/usr/bin/env python3
"""
Zeebo 61u.key Validation Logic Reimplementation
Based on RE of OEM_LCTSystemCtl.c in APPS.bin (Thumb function at 0x1078c8d0)
"""

import os
import struct
from pathlib import Path

# Known validation strings from the binary
KEY_PATHS = [
    "fs:/mcp/61u.key",
    "fs:/card0/61u.key",
    "/61u.key",           # fallback?
    "lctsys/61s.dat",     # related file
]

EXPECTED_KEY_LENGTH = 14  # 14 alphanumeric chars
VALID_CHARS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789")

def validate_key_format(key: str) -> bool:
    """Check if key matches expected format: 14 alphanumeric chars"""
    if not key or len(key) != EXPECTED_KEY_LENGTH:
        return False
    return all(c in VALID_CHARS for c in key)

def find_key_file(nand_mount: str | None = None) -> str | None:
    """
    Simulates the boot-time key search logic.
    Checks both internal NAND (/mcp) and SD card (/card0).
    """
    # In real console: fs:/mcp/61u.key and fs:/card0/61u.key
    # For testing with extracted NAND:
    search_paths = []
    
    if nand_mount:
        search_paths = [
            os.path.join(nand_mount, "mcp", "61u.key"),
            os.path.join(nand_mount, "card0", "61u.key"),
        ]
    else:
        # Default locations relative to extraction
        search_paths = [
            "/home/rafaelfrequiao/projects/zeebo-61u.key-crack/firmware/mcp/61u.key",
            "/home/rafaelfrequiao/projects/zeebo-61u.key-crack/firmware/card0/61u.key",
        ]
    
    for path in search_paths:
        if os.path.exists(path):
            with open(path, 'r') as f:
                key = f.read().strip()
            if validate_key_format(key):
                return key
    return None

def read_61s_dat(nand_mount: str | None = None) -> bytes | None:
    """Read the lctsys/61s.dat file if it exists"""
    paths = []
    if nand_mount:
        paths = [
            os.path.join(nand_mount, "mcp", "lctsys", "61s.dat"),
            os.path.join(nand_mount, "card0", "lctsys", "61s.dat"),
        ]
    
    for path in paths:
        if os.path.exists(path):
            with open(path, 'rb') as f:
                return f.read()
    return None

# ---- Hypothesis Testing Framework ----

def hypothesis_batch_lot(imei: str, batch_db: dict) -> str:
    """
    Batch/lot hypothesis: key is determined by manufacturing batch, not IMEI.
    batch_db maps IMEI prefix/range → key.
    """
    # Try exact IMEI match first
    if imei in batch_db:
        return batch_db[imei]
    # Try prefix matches (first 8 digits = TAC + FAC)
    for prefix_len in [8, 6, 4]:
        prefix = imei[:prefix_len]
        for db_prefix, key in batch_db.items():
            if db_prefix.startswith(prefix) or prefix.startswith(db_prefix):
                return key
    return "A" * 14  # fallback

def hypothesis_hmac_sha1(imei: str, secret: bytes) -> str:
    """HMAC-SHA1(IMEI, secret)[:14] mapped to alphanumeric"""
    import hmac
    import hashlib
    import base64
    
    hmac_digest = hmac.new(secret, imei.encode(), hashlib.sha1).digest()
    # Take first 14 bytes and map to alphanumeric
    b64 = base64.b64encode(hmac_digest).decode()
    alnum = ''.join(c for c in b64 if c in VALID_CHARS)
    return alnum[:14].ljust(14, 'A')

def hypothesis_aes_ecb(imei: str, key: bytes) -> str:
    """AES-ECB(IMEI padded, key)[:14] mapped to alphanumeric"""
    try:
        from Crypto.Cipher import AES
    except ImportError:
        return "A" * 14  # placeholder if pycryptodome not installed
    import base64
    
    # Pad IMEI to 16 bytes
    data = imei.encode().ljust(16, b'\x00')[:16]
    cipher = AES.new(key, AES.MODE_ECB)
    encrypted = cipher.encrypt(data)
    b64 = base64.b64encode(encrypted).decode()
    alnum = ''.join(c for c in b64 if c in VALID_CHARS)
    return alnum[:14].ljust(14, 'A')

def hypothesis_sha1_salt(imei: str, salt: bytes) -> str:
    """SHA1(IMEI + salt)[:14] mapped to alphanumeric"""
    import hashlib
    import base64
    
    digest = hashlib.sha1(imei.encode() + salt).digest()
    b64 = base64.b64encode(digest).decode()
    alnum = ''.join(c for c in b64 if c in VALID_CHARS)
    return alnum[:14].ljust(14, 'A')

def test_hypothesis(imei_key_pairs: list, hypothesis_fn, **kwargs) -> tuple[int, int]:
    """Test a hypothesis against known pairs. Returns (matches, total)"""
    matches = 0
    for imei, expected_key in imei_key_pairs:
        generated = hypothesis_fn(imei, **kwargs)
        if generated == expected_key:
            matches += 1
    return matches, len(imei_key_pairs)

def build_batch_db(pairs: list) -> dict:
    """Build batch database from IMEI→Key pairs, grouping by key"""
    batch_db = {}
    key_to_imeis = {}
    for imei, key in pairs:
        key_to_imeis.setdefault(key, []).append(imei)
    # For each key, use the first IMEI as representative
    for key, imeis in key_to_imeis.items():
        batch_db[imeis[0]] = key
    return batch_db

# ---- Statistical Analysis ----

def analyze_keys(keys: list[str]) -> dict:
    """Statistical analysis of key character distribution"""
    from collections import Counter
    
    pos_counts = [Counter() for _ in range(14)]
    all_chars = Counter()
    
    for key in keys:
        if len(key) == 14:
            for i, c in enumerate(key):
                pos_counts[i][c] += 1
                all_chars[c] += 1
    
    return {
        'positional': pos_counts,
        'overall': all_chars,
        'unique_chars': len(all_chars),
        'sample_size': len(keys)
    }

def analyze_batch_hypothesis(pairs: list) -> dict:
    """Analyze if keys correlate with IMEI batches/ranges"""
    from collections import defaultdict
    
    key_to_imeis = defaultdict(list)
    for imei, key in pairs:
        key_to_imeis[key].append(imei)
    
    results = {
        'duplicate_keys': {k: v for k, v in key_to_imeis.items() if len(v) > 1},
        'total_unique_keys': len(key_to_imeis),
        'total_pairs': len(pairs),
    }
    
    # For each duplicate key, check IMEI prefix similarity
    for key, imeis in results['duplicate_keys'].items():
        prefixes_8 = set(i[:8] for i in imeis)
        prefixes_6 = set(i[:6] for i in imeis)
        results[f'key_{key}_prefixes_8'] = prefixes_8
        results[f'key_{key}_prefixes_6'] = prefixes_6
    
    return results

def print_analysis(analysis: dict):
    print(f"Sample size: {analysis['sample_size']}")
    print(f"Unique characters used: {analysis['unique_chars']}")
    print("\nPositional character frequency:")
    for i, counter in enumerate(analysis['positional']):
        top5 = counter.most_common(5)
        print(f"  Pos {i:2d}: {top5}")

def print_batch_analysis(batch_analysis: dict):
    print(f"Total pairs: {batch_analysis['total_pairs']}")
    print(f"Unique keys: {batch_analysis['total_unique_keys']}")
    dup = batch_analysis['duplicate_keys']
    print(f"Duplicate keys: {len(dup)}")
    for key, imeis in dup.items():
        print(f"  Key {key}: {len(imeis)} IMEIs -> {imeis}")
        prefixes_8 = batch_analysis.get(f'key_{key}_prefixes_8', set())
        prefixes_6 = batch_analysis.get(f'key_{key}_prefixes_6', set())
        print(f"    8-digit prefixes: {prefixes_8}")
        print(f"    6-digit prefixes: {prefixes_6}")

# ---- Main ----

def load_spreadsheet(csv_path: str) -> list[tuple[str, str]]:
    """Load IMEI,Key pairs from CSV export of Google Sheet"""
    import csv
    pairs = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Try common column names
            imei = row.get('IMEI') or row.get('imei') or row.get('Imei') or ''
            key = row.get('Key') or row.get('key') or row.get('61u.key') or ''
            if imei and key:
                pairs.append((imei.strip(), key.strip()))
    return pairs

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python validate.py <command> [args]")
        print("Commands:")
        print("  check <key>           - Validate key format")
        print("  find [nand_path]      - Find key in extracted NAND")
        print("  read61s [nand_path]   - Read 61s.dat")
        print("  analyze <csv>         - Statistical analysis of spreadsheet")
        print("  batch <csv>           - Batch/lot hypothesis analysis")
        print("  test <csv>            - Test hypotheses against pairs")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "check":
        key = sys.argv[2] if len(sys.argv) > 2 else ""
        print(f"Key: {key}")
        print(f"Valid format: {validate_key_format(key)}")
        print(f"Length: {len(key)} (expected {EXPECTED_KEY_LENGTH})")
        print(f"Charset: {set(key) <= VALID_CHARS}")
        
    elif cmd == "find":
        nand_path = sys.argv[2] if len(sys.argv) > 2 else None
        key = find_key_file(nand_path)
        print(f"Found key: {key}" if key else "No valid key found")
        
    elif cmd == "read61s":
        nand_path = sys.argv[2] if len(sys.argv) > 2 else None
        data = read_61s_dat(nand_path)
        print(f"61s.dat: {data.hex() if data else 'Not found'} ({len(data) if data else 0} bytes)")
        
    elif cmd == "analyze":
        csv_path = sys.argv[2]
        pairs = load_spreadsheet(csv_path)
        keys = [k for _, k in pairs]
        analysis = analyze_keys(keys)
        print_analysis(analysis)
        
    elif cmd == "batch":
        csv_path = sys.argv[2]
        pairs = load_spreadsheet(csv_path)
        print(f"Loaded {len(pairs)} IMEI->Key pairs")
        batch_analysis = analyze_batch_hypothesis(pairs)
        print_batch_analysis(batch_analysis)
        
    elif cmd == "test":
        csv_path = sys.argv[2]
        pairs = load_spreadsheet(csv_path)
        print(f"Loaded {len(pairs)} IMEI->Key pairs")
        
        # Test batch hypothesis first
        if pairs:
            batch_db = build_batch_db(pairs)
            matches, total = test_hypothesis(pairs, hypothesis_batch_lot, batch_db=batch_db)
            print(f"Batch/lot hypothesis (self-test): {matches}/{total} matches")
        
        # Test some common secrets
        if pairs:
            # Try common Qualcomm secrets
            test_secrets = [
                b'',  # empty
                b'\x00'*20,
                b'\xff'*20,
                b'QUALCOMM',
                b'TecToy',
                b'Zeebo',
                b'BREW',
                b'12345678901234567890',
            ]
            
            for secret in test_secrets:
                matches, total = test_hypothesis(pairs, hypothesis_hmac_sha1, secret=secret)
                if matches > 0:
                    print(f"HMAC-SHA1 with secret {secret[:20]!r}: {matches}/{total} matches")
            
            # Test SHA1+salt
            from itertools import product
            found = False
            for salt_len in range(1, 5):
                for salt_bytes in product(b'\x00\xff\xaa\x55', repeat=salt_len):
                    salt = bytes(salt_bytes)
                    matches, total = test_hypothesis(pairs, hypothesis_sha1_salt, salt=salt)
                    if matches > 0:
                        print(f"SHA1+salt {salt.hex()}: {matches}/{total} matches")
                        found = True
                        break
                if found:
                    break