# a.py
from __future__ import annotations

# -------- Standard library --------
import os
import re
import base64
from io import BytesIO
from functools import lru_cache
from urllib.parse import quote
from typing import (
    List, Dict, Optional, Sequence, Tuple, Union, Iterable
)

# -------- Third-party --------
import boto3
from botocore.config import Config
from botocore import UNSIGNED
from botocore.exceptions import ClientError
from PIL import Image, ImageDraw, ImageFont
import streamlit as st

# -------- Public API --------
__all__ = [
    "get_s3_filenames",
    "list_all_keys_under",
    "build_prefix_index",
    "pick_cover_key",
    "get_index",
]

# -------- Typing aliases --------
SuffixLike = Optional[Union[str, Sequence[str], Tuple[str, ...]]]

# -------- Internal helpers (S3) --------
def _normalize_suffixes(suffixes: SuffixLike) -> Optional[Tuple[str, ...]]:
    if suffixes is None:
        return None
    if isinstance(suffixes, (str, bytes)):
        return (str(suffixes),)
    return tuple(str(x) for x in suffixes)

def _s3_client(allow_unsigned: bool = True):
    """Create an S3 client pinned to the bucket region to avoid redirects."""
    cfg = Config(
        signature_version=UNSIGNED if allow_unsigned else None,
        retries={"max_attempts": 3, "mode": "standard"},
        max_pool_connections=32,
    )
    # Set your bucket's region to avoid region redirect latency.
    return boto3.client("s3", region_name="us-west-2", config=cfg)

# -------- S3 listing primitives --------
def get_s3_filenames(
    bucket: str,
    prefix: str = "",
    *,
    aws_profile: Optional[str] = None,
    suffixes: SuffixLike = None,
    return_full_path: bool = False,
    max_results: Optional[int] = None,
    allow_unsigned: bool = True,
) -> List[str]:
    """
    List object keys under an S3 prefix.

    Returns:
        A list of S3 keys (or S3 URIs if return_full_path=True).
    """
    if not bucket:
        raise ValueError("bucket must be provided")

    suffix_tuple = _normalize_suffixes(suffixes)

    session = boto3.Session(profile_name=aws_profile) if aws_profile else boto3.Session()
    cfg = Config(signature_version=UNSIGNED) if allow_unsigned else Config()
    s3 = session.client("s3", config=cfg)

    results: List[str] = []
    token = None

    while True:
        kwargs = {"Bucket": bucket, "Prefix": prefix, "MaxKeys": 1000}
        if token:
            kwargs["ContinuationToken"] = token

        try:
            resp = s3.list_objects_v2(**kwargs)
        except ClientError:
            raise

        for obj in resp.get("Contents", []):
            key = obj["Key"]
            if suffix_tuple and not key.endswith(suffix_tuple):
                continue

            results.append(f"s3://{bucket}/{key}" if return_full_path else key)

            if max_results is not None and len(results) >= max_results:
                return results[:max_results]

        if not resp.get("IsTruncated"):
            break
        token = resp.get("NextContinuationToken")

    return results

def list_all_keys_under(
    bucket: str,
    prefix: str,
    *,
    suffixes: Optional[Tuple[str, ...]] = None,
) -> List[str]:
    """Paginate and list every key under a prefix (optionally filter by suffix)."""
    s3 = _s3_client(allow_unsigned=True)
    paginator = s3.get_paginator("list_objects_v2")
    page_it = paginator.paginate(Bucket=bucket, Prefix=prefix)
    out: List[str] = []
    for page in page_it:
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if suffixes and not key.endswith(suffixes):
                continue
            out.append(key)
    return out

# -------- Indexed view for any "*topia" (or any folder) --------
@lru_cache(maxsize=64)
def build_prefix_index(
    bucket: str,
    root: str,
    *,
    group_depth: int = 1,
    suffixes: Optional[Tuple[str, ...]] = (".webp", ".jpg", ".jpeg", ".png", ".gif"),
) -> Dict[str, List[str]]:
    """
    Build an index mapping the next path segment(s) under `root` to lists of keys.

    Example:
      root="images/catopia/" with keys like "images/catopia/Appa/a1.webp"
      -> index["Appa"] = ["images/catopia/Appa/a1.webp", ...]
    """
    root = root.rstrip("/") + "/"
    sfx = _normalize_suffixes(suffixes)
    keys = list_all_keys_under(bucket, root, suffixes=sfx)

    idx: Dict[str, List[str]] = {}
    root_parts = root.strip("/").split("/")
    root_len = len(root_parts)

    for k in keys:
        parts = k.strip("/").split("/")
        if len(parts) <= root_len:
            continue
        # Group key = next `group_depth` segments after root
        end = min(len(parts), root_len + group_depth)
        group_key = "/".join(parts[root_len:end])
        idx.setdefault(group_key, []).append(k)

    # Deterministic sort
    for v in idx.values():
        v.sort(key=lambda x: x.lower())

    return idx

def pick_cover_key(keys: List[str], name_hint: Optional[str] = None) -> Optional[str]:
    """
    Choose a 'cover' image from keys using filename heuristics:
      1) <lower(name_hint)>1.webp
      2) a1.webp
      3) <NameHint>1.webp
      4) first .webp (alphabetical by basename)
      5) first key (alphabetical)
    """
    if not keys:
        return None

    by_base = {os.path.basename(k): k for k in keys}

    if name_hint:
        lower = name_hint.lower()
        for candidate in (f"{lower}1.webp", "a1.webp", f"{name_hint}1.webp"):
            if candidate in by_base:
                return by_base[candidate]

    webps = [k for k in keys if os.path.basename(k).lower().endswith(".webp")]
    if webps:
        webps.sort(key=lambda x: os.path.basename(x).lower())
        return webps[0]

    keys_sorted = sorted(keys, key=lambda x: os.path.basename(x).lower())
    return keys_sorted[0] if keys_sorted else None

# -------- Convenience helpers used by pages (optional exports) --------
def _safe_join_url(base: str, key: str) -> str:
    """Join URL base + S3 key, safely percent-encoding path segments."""
    return f"{base.rstrip('/')}/{quote(key.lstrip('/'), safe='/')}"

def encode_image_to_base64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def _name_to_initials(name: str, max_len: int = 2) -> str:
    """
    Derive 1–2 chars for a placeholder:
    - Latin names: initials of first two words ("Milo Cat" -> "MC")
    - CJK/no-spaces: first 1–2 visible chars
    """
    if not name:
        return "C"
    s = str(name).strip()
    if not s:
        return "C"
    # CJK ranges and related punctuation
    if re.search(r"[\u3000-\u303F\u3040-\u30FF\u31F0-\u31FF\u3400-\u9FFF\uF900-\uFAFF]", s):
        core = re.sub(r"\s+", "", s)
        return core[:max_len] or "C"
    parts = [p for p in re.split(r"\s+", s) if p]
    initials = "".join(p[0].upper() for p in parts[:max_len])
    return initials or "C"

def _placeholder_data_url(initials: str = "C") -> str:
    """Create a WEBP placeholder and return it as a data URL."""
    size = (340, 500)
    bg = (200, 161, 143)   # #c8a18f
    txt = (255, 234, 218)  # #ffeada
    im = Image.new("RGB", size, bg)
    draw = ImageDraw.Draw(im)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", size=120)
    except Exception:
        font = ImageFont.load_default()
    w, h = draw.textbbox((0, 0), initials, font=font)[2:]
    draw.text(((size[0] - w) / 2, (size[1] - h) / 2), initials, fill=txt, font=font)
    buf = BytesIO()
    im.save(buf, format="WEBP", quality=85)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/webp;base64,{b64}"

@lru_cache(maxsize=512)
def _placeholder_for(name: str) -> str:
    """LRU-cached placeholder data URL for a given name."""
    return _placeholder_data_url(initials=_name_to_initials(name, max_len=2))

@st.cache_data(ttl=600, show_spinner=False)
def get_index(bucket: str, root: str) -> Dict[str, List[str]]:
    """Streamlit-cached wrapper around build_prefix_index (reusable across pages)."""
    return build_prefix_index(bucket, root, group_depth=1)
