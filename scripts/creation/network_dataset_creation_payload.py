from __future__ import annotations
import hashlib
import tempfile
import zipfile
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Tuple
from PIL import Image
from tqdm import tqdm
from scapy.all import PcapReader, IP, IPv6, TCP, UDP, Raw  # type: ignore

# Hyperparameter Section
INPUT_ROOTS = [
    "/Users/jabir/Project/Malware Classification/Preprocessing/Malware Reports"
]
OUTPUT_DIRECTORY = "./dataset_network_packets"
REQUIRED_PCAP_NAME = "dump.pcap"

IMG_SIDE = 28
DATA_TYPE = "session_largest_payload"  # Now we process the session with the largest payload
CLEANING_ON = True
ERROR_POLICY = "skip"

# Utility functions
def _to_paths(items: List[str]) -> List[Path]:
    return [Path(p).expanduser().resolve() for p in items]

def _find_zips(roots: List[Path]) -> List[Path]:
    zips: List[Path] = []
    for r in roots:
        if r.is_file() and r.suffix.lower() == ".zip":
            zips.append(r)
        elif r.is_dir():
            zips.extend(sorted(r.rglob("*.zip")))
    return sorted(set(zips))

def _family_from_zip(zip_path: Path) -> str:
    return zip_path.parent.name or "Unknown"

def _safe_extract(zip_path: Path, tmp_dir: Path) -> Path:
    out_dir = tmp_dir / zip_path.stem
    out_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.infolist():
            target = (out_dir / member.filename).resolve()
            if not str(target).startswith(str(out_dir.resolve())):
                continue
            zf.extract(member, out_dir)
    return out_dir

def _iter_required_pcap_files(extracted_dir: Path, required_name: str) -> Iterable[Path]:
    yield from (p for p in extracted_dir.rglob(required_name) if p.name == required_name)

# Sessionization core
Endpoint = Tuple[str, int]
SessionKey = Tuple[str, Endpoint, Endpoint]

def _endpoint(ip_layer, l4_layer) -> Endpoint:
    return ip_layer.src, int(getattr(l4_layer, "sport", 0))

def _key(proto: str, ep1: Endpoint, ep2: Endpoint) -> SessionKey:
    return (proto, ep1, ep2) if ep1 <= ep2 else (proto, ep2, ep1)

def build_sessions(pcap_path: Path) -> Dict[SessionKey, bytearray]:
    sessions: Dict[SessionKey, bytearray] = defaultdict(bytearray)
    with PcapReader(str(pcap_path)) as pcap:
        for pkt in pcap:
            ip = pkt.getlayer(IP) or pkt.getlayer(IPv6)
            if ip is None:
                continue
            l4 = pkt.getlayer(TCP) or pkt.getlayer(UDP)
            if l4 is None:
                continue
            proto = "TCP" if TCP in pkt else "UDP"
            ep_src = _endpoint(ip, l4)
            ep_dst = (ip.dst, int(getattr(l4, "dport", 0)))
            key = _key(proto, ep_src, ep_dst)

            raw = pkt.getlayer(Raw)
            if raw and raw.load:
                sessions[key] += bytes(raw.load)
    return sessions

def to_784(buf: bytes, side: int = IMG_SIDE) -> bytes:
    target = side * side
    if len(buf) >= target:
        return buf[:target]
    return buf + b"\x00" * (target - len(buf))

def write_png(out_path: Path, b784: bytes, side: int = IMG_SIDE) -> None:
    img = Image.frombytes("L", (side, side), b784)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, format="PNG")

# Main method (this is where stuff happens :)
def main() -> None:
    roots = _to_paths(INPUT_ROOTS)
    out_root = Path(OUTPUT_DIRECTORY).resolve()
    out_images = out_root / "images"
    log_path = out_root / "processing_overview.log"

    out_root.mkdir(parents=True, exist_ok=True)
    stats = Counter()
    errors: List[str] = []
    per_family = defaultdict(Counter)

    # Discover ZIP files
    start_ts = datetime.now()
    zip_files = _find_zips(roots)
    stats["zip_found"] = len(zip_files)

    # Process the ZIP files
    with tempfile.TemporaryDirectory(prefix="pcap_proc_") as temporary_directory_str:
        temporary_directory = Path(temporary_directory_str)
        for z in tqdm(zip_files, desc="Processing ZIP reports", unit="zip", ncols=80):
            fam = _family_from_zip(z)
            try:
                extracted = _safe_extract(z, temporary_directory)
                pcap_files = list(_iter_required_pcap_files(extracted, REQUIRED_PCAP_NAME))
                stats["zip_with_required_pcap"] += int(len(pcap_files) > 0)
                if not pcap_files:
                    stats["required_pcap_missing"] += 1
                    errors.append(f"No {REQUIRED_PCAP_NAME} in ZIP: {z}")
                    continue

                for pcap_path in pcap_files:
                    stats["pcap_total"] += 1
                    try:
                        sessions = build_sessions(pcap_path)

                        # Cleaning: drop byte-identical duplicates (within this PCAP).
                        seen = set()
                        cleaned: List[bytes] = []
                        for _, buf in sessions.items():
                            b = bytes(buf)
                            if CLEANING_ON:
                                h = hashlib.sha1(b).hexdigest()
                                if h in seen:
                                    stats["duplicates_dropped"] += 1
                                    continue
                                seen.add(h)
                            cleaned.append(b)

                        # Select the session with the largest payload
                        if cleaned:
                            largest_session = max(cleaned, key=len)  # Choose the largest payload session
                            b784 = to_784(largest_session, side=IMG_SIDE)
                            out_dir = out_images / fam / z.stem
                            out_png = out_dir / f"{pcap_path.stem}_largest_session.png"
                            write_png(out_png, b784, side=IMG_SIDE)
                            stats["images_written"] += 1
                            per_family[fam]["images"] += 1
                            per_family[fam]["sessions"] += 1

                        stats["pcap_success"] += 1

                    except Exception as e:
                        stats["pcap_errors"] += 1
                        if ERROR_POLICY == "raise":
                            raise
                        errors.append(f"PCAP error in {z} -> {pcap_path}: {e}")

            except Exception as e:
                stats["zip_errors"] += 1
                if ERROR_POLICY == "raise":
                    raise
                errors.append(f"ZIP error: {z} — {e}")

    end_ts = datetime.now()

    # Create the overview log
    lines: List[str] = ["Network Session Imaging Overview",
                        f"Started : {start_ts.isoformat(timespec='seconds')}",
                        f"Finished: {end_ts.isoformat(timespec='seconds')}", "", "Input roots:"]
    for r in roots:
        lines.append(f"  - {r}")
    lines.append(f"Output root: {out_root}")
    lines.append(f"Required PCAP: {REQUIRED_PCAP_NAME}")
    lines.append(f"Image spec   : {IMG_SIDE}×{IMG_SIDE} (784 bytes: trim/pad)")
    lines.append(f"Cleaning     : {'ON' if CLEANING_ON else 'OFF'} (drop exact duplicates)")
    lines.append("")
    lines.append("Global stats:")
    for k in sorted(stats.keys()):
        lines.append(f"  {k:26s} {stats[k]}")
    if per_family:
        lines.append("")
        lines.append("Per-family counts:")
        for fam, c in sorted(per_family.items()):
            lines.append(f"  [{fam}] images={c['images']} sessions={c['sessions']}")
    if errors:
        lines.append("")
        lines.append("Errors / Warnings:")
        for e in errors:
            lines.append(f"  - {e}")
    lines.append("")

    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    # Final output summary
    summary = [
        f"ZIPs found: {stats['zip_found']} | with {REQUIRED_PCAP_NAME}: {stats['zip_with_required_pcap']} | ZIP errors: {stats['zip_errors']}",
        f"PCAPs: total {stats['pcap_total']} | success {stats['pcap_success']} | errors {stats['pcap_errors']}",
        f"Cleaning (duplicates dropped): {stats['duplicates_dropped']}",
        f"Images written: {stats['images_written']} → {(out_root/'images').resolve()}",
        f"Log: {(out_root/'processing_overview.log').resolve()}",
    ]
    print("\n".join(summary))
    with open(log_path, "a", encoding="utf-8") as f:
        f.write("\n".join(["Final Summary:"] + ["  " + s for s in summary] + [""]))


if __name__ == "__main__":
    main()
