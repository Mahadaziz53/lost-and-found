"""
Advanced AI Matching Engine
============================
Text (TF-IDF) 50% + Location 20% + Image (ORB) 30%
+ Duplicate Detection + Explanation Engine
"""
from __future__ import annotations
import os, re, math, logging
from typing import Any
logger = logging.getLogger(__name__)

try:
    import cv2, numpy as np
    CV2_OK = True
except ImportError:
    CV2_OK = False
    logger.warning("OpenCV unavailable – image matching disabled.")

# ── Stop words ──────────────────────────────────────────────────────────────
SW = {
    "a","an","the","and","or","but","in","on","at","to","for","of","with",
    "is","it","its","this","that","was","are","be","been","have","has","had",
    "i","my","we","our","you","your","he","his","she","her","they","their",
    "what","which","who","if","then","than","so","up","out","about","from",
    "by","as","not","no","can","will","would","could","should","item","lost",
    "found","looking","please","help","need","want","very","some","just","got",
}

# ── Weights ──────────────────────────────────────────────────────────────────
W_TEXT = 0.50
W_LOC  = 0.20
W_IMG  = 0.30
THRESH = 0.25          # minimum combined score to surface
DUP_THRESH = 0.88      # above this → duplicate warning


class MatchingEngine:

    # ── text helpers ─────────────────────────────────────────────────────────
    @staticmethod
    def _clean(text: str) -> str:
        text = text.lower()
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        return " ".join(t for t in text.split() if t not in SW and len(t) > 1)

    @staticmethod
    def _tokens(text: str) -> list[str]:
        return text.split()

    @staticmethod
    def _tf(tokens: list[str]) -> dict[str, float]:
        tf: dict[str, float] = {}
        for t in tokens:
            tf[t] = tf.get(t, 0) + 1
        total = len(tokens) or 1
        return {k: v / total for k, v in tf.items()}

    @staticmethod
    def _cos(a: dict, b: dict) -> float:
        common = set(a) & set(b)
        if not common:
            return 0.0
        dot  = sum(a[k] * b[k] for k in common)
        magA = math.sqrt(sum(v**2 for v in a.values()))
        magB = math.sqrt(sum(v**2 for v in b.values()))
        return dot / (magA * magB) if magA * magB else 0.0

    def text_score(self, a: str, b: str) -> float:
        ta = self._tokens(self._clean(a))
        tb = self._tokens(self._clean(b))
        if not ta or not tb:
            return 0.0
        # TF-IDF cosine
        cos = self._cos(self._tf(ta), self._tf(tb))
        # Jaccard keyword boost
        sa, sb = set(ta), set(tb)
        jac = len(sa & sb) / len(sa | sb) if (sa | sb) else 0.0
        return min(1.0, cos * 0.7 + jac * 0.3)

    # ── location score ───────────────────────────────────────────────────────
    def loc_score(self, a: str, b: str) -> float:
        if not a or not b:
            return 0.0
        wa = set(re.findall(r"\w+", a.lower()))
        wb = set(re.findall(r"\w+", b.lower()))
        if not wa or not wb:
            return 0.0
        return len(wa & wb) / max(len(wa), len(wb))

    # ── ORB image score ──────────────────────────────────────────────────────
    def img_score(self, pa: str | None, pb: str | None) -> float | None:
        if not CV2_OK or not pa or not pb:
            return None
        fa = os.path.join("static", pa)
        fb = os.path.join("static", pb)
        if not os.path.isfile(fa) or not os.path.isfile(fb):
            return None
        try:
            ia = cv2.imread(fa, cv2.IMREAD_GRAYSCALE)
            ib = cv2.imread(fb, cv2.IMREAD_GRAYSCALE)
            if ia is None or ib is None:
                return None
            ia = cv2.resize(ia, (256, 256))
            ib = cv2.resize(ib, (256, 256))
            orb = cv2.ORB_create(nfeatures=500)
            kpA, desA = orb.detectAndCompute(ia, None)
            kpB, desB = orb.detectAndCompute(ib, None)
            if desA is None or desB is None or len(desA) < 2 or len(desB) < 2:
                return self._hist_score(ia, ib)
            bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
            matches = bf.match(desA, desB)
            if not matches:
                return self._hist_score(ia, ib)
            good = [m for m in matches if m.distance < 60]
            orb_s = len(good) / max(len(kpA), len(kpB), 1)
            return min(1.0, orb_s * 3)
        except Exception as e:
            logger.warning("ORB error: %s", e)
            return None

    @staticmethod
    def _hist_score(ia, ib) -> float:
        score = 0.0
        for img in [ia, ib]:
            pass
        ha = cv2.calcHist([ia], [0], None, [64], [0, 256])
        hb = cv2.calcHist([ib], [0], None, [64], [0, 256])
        cv2.normalize(ha, ha)
        cv2.normalize(hb, hb)
        return max(0.0, cv2.compareHist(ha, hb, cv2.HISTCMP_CORREL))

    # ── Explanation engine ───────────────────────────────────────────────────
    def explain(self, src: dict, cand: dict, ts: float, ls: float, ims: float | None) -> list[str]:
        reasons = []
        sa = self._clean(f"{src.get('title','')} {src.get('description','')}")
        sb = self._clean(f"{cand.get('title','')} {cand.get('description','')}")
        common_kw = set(sa.split()) & set(sb.split())
        if common_kw:
            top = sorted(common_kw, key=len, reverse=True)[:4]
            reasons.append(f"Shared keywords: <strong>{', '.join(top)}</strong>")
        if ts >= 0.6:
            reasons.append("Very similar item descriptions (high text overlap)")
        elif ts >= 0.35:
            reasons.append("Moderately similar descriptions")
        if ls >= 0.5:
            reasons.append(f"Same or overlapping location: <em>{cand.get('location','')}</em>")
        elif ls > 0:
            reasons.append(f"Nearby location mentioned")
        if ims is not None and ims >= 0.4:
            reasons.append("Visual similarity detected by image analysis (ORB)")
        # title word match
        ta = set(self._clean(src.get('title','')).split())
        tb = set(self._clean(cand.get('title','')).split())
        if ta & tb:
            reasons.append(f"Item type match: <strong>{', '.join(ta & tb)}</strong>")
        return reasons or ["General similarity detected by AI engine"]

    # ── Duplicate check ──────────────────────────────────────────────────────
    def is_duplicate(self, new_item: dict, existing: list[dict]) -> dict | None:
        txt_new = f"{new_item.get('title','')} {new_item.get('description','')}"
        for ex in existing:
            txt_ex = f"{ex.get('title','')} {ex.get('description','')}"
            ts = self.text_score(txt_new, txt_ex)
            ls = self.loc_score(new_item.get('location',''), ex.get('location',''))
            combined = ts * 0.6 + ls * 0.4
            if combined >= DUP_THRESH:
                return ex
        return None

    # ── Smart description enhancer ───────────────────────────────────────────
    @staticmethod
    def enhance_description(title: str, description: str, location: str) -> str:
        """Rule-based smart description enhancement (no API needed)."""
        t = title.lower()
        desc = description.strip()
        loc  = location.strip()

        # Category hints
        CATEGORIES = {
            "wallet":    "leather wallet possibly containing ID cards, cash, and credit cards",
            "phone":     "smartphone device with potential contacts, data, and personal apps",
            "bag":       "bag or backpack which may contain personal belongings",
            "key":       "key or keychain, possibly for a vehicle or property",
            "laptop":    "laptop computer containing important files and data",
            "watch":     "wristwatch, possibly with sentimental or monetary value",
            "card":      "ID card, debit/credit card, or membership card",
            "glasses":   "eyeglasses or sunglasses",
            "earphone":  "wireless earphones or headphones",
            "ring":      "ring or jewelry with possible sentimental value",
            "book":      "book or notebook containing personal notes",
            "umbrella":  "umbrella, typically found in public transport or buildings",
        }
        hint = ""
        for kw, h in CATEGORIES.items():
            if kw in t or kw in desc.lower():
                hint = h
                break

        parts = []
        if hint:
            parts.append(f"This appears to be a {hint}.")
        if desc:
            parts.append(desc[0].upper() + desc[1:] + ("." if not desc.endswith(".") else ""))
        if loc:
            parts.append(f"Last seen / found in the area of {loc}.")
        parts.append("If you have any information, please contact the reporter immediately.")

        enhanced = " ".join(parts)
        return enhanced if enhanced.strip() != description.strip() else description

    # ── NLP chat query parser ─────────────────────────────────────────────────
    @staticmethod
    def parse_query(query: str) -> dict[str, str]:
        """Extract intent, object, color, and location from a natural language query."""
        q = query.lower()
        intent = "lost" if any(w in q for w in ["lost","lose","missing","dropped","can't find"]) else \
                 "found" if any(w in q for w in ["found","picked up","saw","discovered"]) else "both"
        COLORS = ["black","white","red","blue","green","yellow","brown","grey","gray","silver","golden","pink","purple"]
        color = next((c for c in COLORS if c in q), "")
        ITEMS = ["wallet","phone","bag","key","laptop","watch","card","glasses","earphone",
                 "ring","book","umbrella","jacket","shoes","camera","passport","purse","backpack"]
        obj = next((i for i in ITEMS if i in q), "")
        # Location: everything after "near", "at", "in", "from"
        loc_match = re.search(r"(?:near|at|in|from|around|by)\s+([\w\s]+?)(?:\s*$|,|\.|and)", q)
        loc = loc_match.group(1).strip() if loc_match else ""
        return {"intent": intent, "object": obj, "color": color, "location": loc, "raw": query}

    # ── Main match finder ────────────────────────────────────────────────────
    def find_matches(self, source: dict[str, Any], candidates: list[dict[str, Any]]) -> list[dict]:
        if not candidates:
            return []
        src_txt = f"{source.get('title','')} {source.get('description','')}"
        src_loc = source.get("location", "")
        src_img = source.get("image_path")
        results = []
        for c in candidates:
            if c.get("id") == source.get("id"):
                continue
            c_txt = f"{c.get('title','')} {c.get('description','')}"
            ts = self.text_score(src_txt, c_txt)
            ls = self.loc_score(src_loc, c.get("location",""))
            ims = self.img_score(src_img, c.get("image_path"))
            if ims is not None:
                final = ts * W_TEXT + ls * W_LOC + ims * W_IMG
            else:
                # re-normalise weights without image
                final = ts * (W_TEXT + W_IMG * 0.5) + ls * (W_LOC + W_IMG * 0.5)
            final = min(final, 1.0)
            if final < THRESH:
                continue
            reasons = self.explain(source, c, ts, ls, ims)
            results.append({
                **c,
                "score":          round(final * 100, 1),
                "score_raw":      final,
                "tfidf_score":    round(ts  * 100, 1),
                "keyword_score":  round(ts  * 100, 1),
                "location_score": round(ls  * 100, 1),
                "image_score":    round(ims * 100, 1) if ims is not None else None,
                "label":          self._label(final),
                "badge_color":    self._badge(final),
                "reasons":        reasons,
                "high_alert":     final >= 0.70,
            })
        return sorted(results, key=lambda x: x["score_raw"], reverse=True)

    @staticmethod
    def _label(s: float) -> str:
        pct = s * 100
        if pct >= 80: return "Excellent Match"
        if pct >= 60: return "Strong Match"
        if pct >= 40: return "Possible Match"
        if pct >= 25: return "Weak Match"
        return "Low Similarity"

    @staticmethod
    def _badge(s: float) -> str:
        pct = s * 100
        if pct >= 80: return "success"
        if pct >= 60: return "primary"
        if pct >= 40: return "warning"
        return "secondary"
