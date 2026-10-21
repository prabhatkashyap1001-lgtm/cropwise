"""
Full synthetic dataset for the CropWise MVP.

Adds, ON TOP of the base demo seed (app/seed_data.py) and without changing
any existing account, a connected set of records for every tab in the app so
each table holds 10+ rows wherever the schema allows it (a few tables are
capped by design: one KYC row per buyer, one receipt per transaction, and
there are only two market-data providers -- see the summary printed on run).

The records are linked, not independent. One deal flows through all of:

    farmer -> listing / lot -> buyer offer -> negotiation rounds -> agreement
           -> transaction (+ event timeline) -> transport request (+ quotes,
              chat, reviews) -> payment(s) -> receipt (SHA-256) -> ratings
           -> QoS evidence (pickup / terms records, disputes) -> grievances

Nothing here writes a reputation score. QoS pages are still computed by
app/services/reputation.py from the evidence rows this module inserts.

Everything is fictional. Market prices are NOT touched (the base seed already
holds 60 days of clearly-labelled "demo" prices for every crop x market), and
provider_sync_state is NOT seeded, because a fake "last synced" time would
claim a live data feed that never ran.

Run from backend/:
    python -m app.mock_data.seed_full_demo            # seed (safe to re-run)
    python -m app.mock_data.seed_full_demo --reset    # remove what it added
All demo accounts use the password  demo1234.
"""
from __future__ import annotations

import datetime as dt
import json
import math
import random
import sys
from pathlib import Path
from typing import Dict, List, Optional

from sqlalchemy import func, select

from app import models
from app.mock_data import synthetic_data as S
from app.mock_data.demo_users import DEMO_BUYERS, DEMO_FARMERS, DEMO_PASSWORD
from app.mock_data.locations import MARKET_BY_NAME, distance_between

MANIFEST = Path(__file__).resolve().parents[2] / ".seed_full_demo_manifest.json"
IST = dt.timedelta(hours=5, minutes=30)
ADMIN = "admin@cropwise.demo"

STAGES = ["OFFER_ACCEPTED", "ORDER_CONFIRMED", "LOGISTICS_PENDING", "LOGISTICS_CONFIRMED", "PICKED_UP",
          "IN_TRANSIT", "DELIVERED", "PAYMENT_PENDING", "PAYMENT_INITIATED", "PAYMENT_RECEIVED", "COMPLETED"]

# (name, capacity kg, Rs/km, type) -- same options as app/routers/transport.py
VEHICLES = [("Tata Ace (Chhota Hathi)", 750, 9, "mini-truck"), ("Mahindra Bolero Pickup", 1500, 14, "mini-truck"),
            ("Tata 407 Truck", 2500, 17, "truck"), ("Eicher 14ft Truck", 5000, 22, "truck")]


# ── small helpers ────────────────────────────────────────────────────────────
def _hash_pw(password: str) -> str:
    from app.auth_utils import hash_password
    return hash_password(password)


def _vehicle_for(qty: float):
    for v in VEHICLES:
        if v[1] >= qty:
            return v
    return VEHICLES[-1]


def _quality_report(grade: str, q: float) -> dict:
    notes = {"A": ["Uniform size and colour", "Dry and clean", "Minimal foreign matter"],
             "B": ["Acceptable moisture", "Some size variation"],
             "C": ["High moisture", "Visible damage in part of the lot"]}[grade]
    return {"quality_grade": grade, "visual_quality_score": q,
            "moisture_pct": round(9 + (100 - q) * 0.18, 1),
            "foreign_matter_pct": round(0.4 + (100 - q) * 0.07, 1),
            "damaged_pct": round(0.6 + (100 - q) * 0.12, 1),
            "detected_notes": notes,
            "analysis_method": "AI Estimated Quality — image-based analysis only, not lab-certified.",
            "demo_mode": True}


class Seeder:
    def __init__(self, db, now: Optional[dt.datetime] = None):
        self.db = db
        self.now = (now or dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)).replace(microsecond=0)
        self.rng = random.Random(20261015)
        self.manifest: Dict[str, List[int]] = {}
        self.restore: Dict[str, Dict[str, dict]] = {"farmers": {}, "buyers": {}}
        self.ref = 0

    # -- persistence ---------------------------------------------------------
    def add(self, obj):
        self.db.add(obj)
        self.db.flush()
        self.manifest.setdefault(obj.__tablename__, []).append(obj.id)
        return obj

    def T(self, when: dt.datetime) -> dt.datetime:
        """Clamp to 'a few minutes ago' so seeded history never lies in the future."""
        return min(when, self.now - dt.timedelta(minutes=5))

    def days_ago(self, d: float, hour: int = 10) -> dt.datetime:
        base = (self.now - dt.timedelta(days=d)).replace(hour=hour, minute=0, second=0)
        return self.T(base)

    def payment_ref(self) -> str:
        self.ref += 1
        return f"CW-PAY-{self.now.year}-{0xA10000 + self.ref * 7919:08X}"

    # -- phase 0: existing accounts ------------------------------------------
    def resolve_accounts(self):
        db = self.db
        self.farmers = []
        for f in DEMO_FARMERS:
            row = db.query(models.Farmer).filter_by(email=f["email"]).first()
            if row is None:
                raise RuntimeError(f"Base demo farmer {f['email']} missing; run the base seed first.")
            self.farmers.append(row)
        self.buyers = []
        for b in DEMO_BUYERS:
            row = db.query(models.Buyer).filter_by(email=b["email"]).first()
            if row is None:
                raise RuntimeError(f"Base demo buyer {b['email']} missing; run the base seed first.")
            self.buyers.append(row)
        for f in self.farmers:
            self.restore["farmers"][str(f.id)] = {"rating": f.rating,
                                                  "last_login": f.last_login.isoformat() if f.last_login else None}
        for b in self.buyers:
            self.restore["buyers"][str(b.id)] = {"last_login": b.last_login.isoformat() if b.last_login else None}
        self.txn1 = db.query(models.Transaction).filter_by(status="COMPLETED").order_by(models.Transaction.id).first()
        self.txn2 = db.query(models.Transaction).filter_by(status="DELIVERED").order_by(models.Transaction.id).first()

    # -- phase 1-3: buyers, transporters, KYC --------------------------------
    def seed_buyers_transporters(self):
        pw = _hash_pw(DEMO_PASSWORD)
        for b in S.EXTRA_BUYERS:
            self.buyers.append(self.add(models.Buyer(
                company_name=b["company_name"], email=b["email"], password_hash=pw, phone=b["phone"],
                location=b["location"], latitude=b["latitude"], longitude=b["longitude"],
                buyer_type=b["buyer_type"], verification_status="pending",
                reliability_score=b["reliability_score"], payment_history_score=b["payment_history_score"],
                crops_of_interest=b["crops_of_interest"], preferred_language="en",
                created_at=self.days_ago(20))))
        self.transporters = []
        for t in S.TRANSPORTERS:
            self.transporters.append(self.add(models.Transporter(
                name=t["name"], email=t["email"], password_hash=pw, phone=t["phone"],
                business_name=t["business"], service_area=t["area"], vehicle_types=t["vehicles"],
                preferred_language=t["lang"], created_at=self.days_ago(90))))

    def seed_kyc(self):
        db = self.db

        def audit(buyer, old, new, when, reviewer, note):
            self.add(models.BuyerVerificationAuditLog(
                buyer_id=buyer.id, old_status=old, new_status=new, reviewer_admin_id=reviewer,
                note=note, created_at=when))

        # 1) the three base verifications: add the history that led to VERIFIED
        for v in db.query(models.BuyerVerification).filter(
                models.BuyerVerification.buyer_id.in_([b.id for b in self.buyers[:3]])).all():
            buyer = next(b for b in self.buyers if b.id == v.buyer_id)
            done = v.verified_at or self.days_ago(30)
            audit(buyer, None, "UNDER_REVIEW", done - dt.timedelta(days=3), None, "Documents submitted")
            audit(buyer, "UNDER_REVIEW", "VERIFIED", done, ADMIN, "Documents verified")

        # 2) original buyers 3-9
        verified_days = {4: 52, 5: 41, 6: 35, 8: 28, 9: 14}
        for idx, spec in S.BUYER_VERIFICATIONS.items():
            buyer = self.buyers[idx]
            status = spec["status"]
            verified_at = self.days_ago(verified_days[idx]) if idx in verified_days else None
            if idx == 3:
                verified_at = self.days_ago(70)
            submitted = (verified_at - dt.timedelta(days=3)) if verified_at else self.days_ago(14)
            self.add(models.BuyerVerification(
                buyer_id=buyer.id, business_name=spec["name"], business_registration_number=spec["reg"],
                gst_number=spec["gst"], license_number=spec["lic"], document_urls=spec["docs"],
                verification_status=status, verification_method=spec["method"],
                verification_notes=spec["note"], verified_at=verified_at if status in ("VERIFIED", "SUSPENDED") else None,
                rejected_reason=spec["reason"], submitted_at=submitted,
                reviewed_at=(self.days_ago(9) if status == "SUSPENDED" else self.days_ago(11) if status == "REJECTED"
                             else verified_at),
                reviewed_by=ADMIN, created_at=submitted, updated_at=self.days_ago(1)))
            audit(buyer, None, "UNDER_REVIEW", submitted, None, "Documents submitted")
            if status in ("VERIFIED", "SUSPENDED"):
                audit(buyer, "UNDER_REVIEW", "VERIFIED", verified_at, ADMIN, "Documents verified")
            if status == "SUSPENDED":
                audit(buyer, "VERIFIED", "SUSPENDED", self.days_ago(9), ADMIN, "Repeated unresolved payment complaints")
            if status == "REJECTED":
                audit(buyer, "UNDER_REVIEW", "REJECTED", self.days_ago(11), ADMIN, spec["reason"])

        # 3) the three new buyers (two waiting for review, one not yet submitted)
        for i, spec in enumerate(S.EXTRA_BUYERS):
            buyer, ver = self.buyers[10 + i], spec["ver"]
            submitted = self.days_ago(ver["submitted_days_ago"]) if ver["submitted_days_ago"] else None
            self.add(models.BuyerVerification(
                buyer_id=buyer.id, business_name=spec["company_name"], business_registration_number=ver["reg"],
                gst_number=ver["gst"], license_number=ver["lic"], document_urls=ver["docs"],
                verification_status=ver["status"], verification_method=ver["method"],
                verification_notes="Awaiting admin review. (Synthetic demo data)" if submitted else None,
                submitted_at=submitted, created_at=submitted or self.days_ago(5), updated_at=submitted or self.days_ago(5)))
            if submitted:
                audit(buyer, None, "UNDER_REVIEW", submitted, None, "Documents submitted")

    # -- phase 4: demands ----------------------------------------------------
    def seed_demands(self):
        today = self.now.date()
        self.demands = {}
        for d in S.DEMANDS:
            buyer = self.buyers[d["buyer"]]
            m = MARKET_BY_NAME.get(d["loc"], {})
            a_grade = d["grade"] == "A"
            deadline = today + dt.timedelta(days=d["dl"])
            self.demands[d["key"]] = self.add(models.BuyerDemand(
                buyer_id=buyer.id, crop=d["crop"], required_quantity_kg=d["req"], minimum_quantity_kg=d["mn"],
                maximum_quantity_kg=d["mx"], target_price_per_kg=d["target"], quality_grade=d["grade"],
                moisture_limit=12.0 if a_grade else 14.0, foreign_matter_limit=1.5 if a_grade else 3.0,
                damaged_grains_limit=2.0 if a_grade else 4.0, delivery_location=d["loc"],
                delivery_latitude=m.get("latitude"), delivery_longitude=m.get("longitude"),
                delivery_deadline=deadline.isoformat(), payment_terms=d["terms"],
                additional_requirements="(Synthetic demo demand)", status=d["status"],
                expires_at=(deadline + dt.timedelta(days=5)).isoformat(),
                created_at=self.days_ago(d["created_days_ago"]), updated_at=self.days_ago(max(d["created_days_ago"] - 5, 0))))

    # -- supply side: listings and lots --------------------------------------
    def _make_listing(self, farmer, crop, qty_now, grade, q, ask, floor, status, created, avail_days, deadline_days):
        return self.add(models.CropListing(
            farmer_id=farmer.id, crop=crop, quantity_kg=qty_now, quality_grade=grade, quality_score=q,
            expected_price_per_kg=ask, location=farmer.location,
            available_date=(created.date() + dt.timedelta(days=avail_days)).isoformat(), status=status,
            min_acceptable_price=floor,
            bidding_deadline=(created.date() + dt.timedelta(days=deadline_days)).isoformat(),
            image_note=f"{crop} sample photo (synthetic)", note="Synthetic demo listing",
            language=farmer.preferred_language or "en", created_at=created))

    def _make_lot(self, farmer, crop, qty_now, grade, q, ask, floor, status, created, harvest_days_ago, fpo_id, note):
        self.lot_seq = getattr(self, "lot_seq", 0) + 1
        return self.add(models.Lot(
            lot_number=f"CW-SYN-{self.lot_seq:05d}", farmer_id=farmer.id, fpo_id=fpo_id, crop=crop,
            quantity_kg=qty_now, grade=grade, quality_score=q, quality_report=_quality_report(grade, q),
            harvest_date=(created.date() - dt.timedelta(days=harvest_days_ago)).isoformat(),
            available_date=created.date().isoformat(), location=farmer.location,
            latitude=farmer.latitude, longitude=farmer.longitude, expected_price=ask, minimum_price=floor,
            status=status, note=note or f"Synthetic lot - {farmer.location} {crop}", created_at=created, updated_at=created))

    # -- negotiation helpers --------------------------------------------------
    def _terms(self, deal_like, price, qty, mode, pickup_date, delivery_loc, deadline):
        return dict(price_per_kg=price, quantity_kg=qty, quality_grade=deal_like["grade"],
                    quality_notes=f"Grade {deal_like['grade']}, moisture within agreed limit",
                    pickup_mode=mode, pickup_date=pickup_date, delivery_location=delivery_loc,
                    delivery_deadline=deadline)

    def _round(self, offer, no, by, by_id, terms, message, status, created, responded=None, responded_by=None):
        return self.add(models.NegotiationRound(
            offer_id=offer.id, round_no=no, proposed_by=by, proposed_by_id=by_id, message=message, status=status,
            created_at=created, responded_at=responded, responded_by=responded_by, **terms))

    # -- phase 5/6: the deals ------------------------------------------------
    def seed_deals(self):
        from app.services import negotiation_service as neg
        self.deal_rows = {}
        for d in S.DEALS:
            farmer, buyer = self.farmers[d["farmer"]], self.buyers[d["buyer"]]
            qty, final = d["qty"], d["rounds"][-1]
            t0 = self.days_ago(d["days_ago"], hour=self.now.hour)
            t_acc = self.T(t0 + dt.timedelta(hours=3 * len(d["rounds"])))
            pickup_day = (t0 + dt.timedelta(days=d["pu"])).date()
            sched = dt.datetime.combine(pickup_day, dt.time(9, 0)) - IST  # 09:00 IST in UTC
            mode = d["mode"]
            deliver_loc = buyer.location if mode != "BUYER_PICKUP" else None
            deadline = (pickup_day + dt.timedelta(days=2)).isoformat() if mode != "BUYER_PICKUP" else None

            # supply object
            listing = lot = None
            if d["flow"] == "listing":
                remaining = d["listing_remaining"]
                listing = self._make_listing(farmer, d["crop"], remaining, d["grade"], d["q"], d["ask"], d["floor"],
                                             "active" if remaining > 0 else "sold", t0 - dt.timedelta(days=2), 1, 6)
            else:
                remaining = int(round(qty * 0.2 / 50.0)) * 50
                lot_status = {"COMPLETED": "DELIVERED", "IN_TRANSIT": "IN_TRANSIT", "PICKED_UP": "IN_TRANSIT"}.get(
                    d["status"], "AVAILABLE") if d["tr"] else "AVAILABLE"
                fpo_id = self.pools[d["fpo"]].id if d.get("fpo") is not None else None
                lot = self._make_lot(farmer, d["crop"], remaining, d["grade"], d["q"], d["ask"], d["floor"],
                                     lot_status, t0 - dt.timedelta(days=2), 3, fpo_id,
                                     f"Synthetic lot - original size {qty + remaining} kg, {qty} kg sold in deal {d['key']}")

            offer = self.add(models.BuyerOffer(
                buyer_id=buyer.id, listing_id=listing.id if listing else None, lot_id=lot.id if lot else None,
                buyer_demand_id=self.demands[d["demand"]].id if d["demand"] else None,
                offered_price_per_kg=final, quantity_kg=qty,
                message=f"Interested in {qty} kg {d['crop']}.", language="en", status="accepted", created_at=t0))

            # negotiation rounds (buyer, farmer, buyer, ...); last one accepted by the other side
            rounds = []
            for i, price in enumerate(d["rounds"]):
                by = "buyer" if i % 2 == 0 else "farmer"
                is_last = i == len(d["rounds"]) - 1
                other = "farmer" if by == "buyer" else "buyer"
                created = self.T(t0 + dt.timedelta(hours=3 * i))
                nxt = self.T(t0 + dt.timedelta(hours=3 * (i + 1)))
                msg = (f"Offering Rs {price}/kg for {qty} kg." if by == "buyer"
                       else f"Counter at Rs {price}/kg; lot is tested and ready.")
                rounds.append(self._round(
                    offer, i + 1, by, buyer.id if by == "buyer" else farmer.id,
                    self._terms(d, price, qty, mode, pickup_day.isoformat(), deliver_loc, deadline), msg,
                    "ACCEPTED" if is_last else "COUNTERED", created, nxt, other))
            accepted_by = "farmer" if len(d["rounds"]) % 2 == 1 else "buyer"

            txn = self.add(models.Transaction(
                listing_id=listing.id if listing else None, lot_id=lot.id if lot else None, offer_id=offer.id,
                farmer_id=farmer.id, buyer_id=buyer.id, final_price_per_kg=final, quantity_kg=qty,
                total_amount=round(final * qty, 2), market_used=farmer.location, status=d["status"],
                created_at=t_acc, updated_at=t_acc))

            terms = neg.round_terms(rounds[-1])
            self.add(models.NegotiationAgreement(
                offer_id=offer.id, transaction_id=txn.id, round_id=rounds[-1].id, farmer_id=farmer.id,
                buyer_id=buyer.id, accepted_by=accepted_by, terms=terms, terms_hash=neg._canonical_hash(terms),
                rounds_count=len(rounds), agreed_at=t_acc))
            self.deal_rows[d["key"]] = dict(spec=d, farmer=farmer, buyer=buyer, listing=listing, lot=lot, offer=offer,
                                            txn=txn, t0=t0, t_acc=t_acc, sched=sched, pickup_day=pickup_day,
                                            accepted_by=accepted_by, terms=terms)

    # -- transport helpers ---------------------------------------------------
    def _offers_for(self, tr, farmer, transporter, est: int, pattern: str, start: dt.datetime) -> int:
        """Insert the quote history; return the agreed price."""
        r10 = lambda x: int(round(x / 10.0)) * 10
        plans = {"A": [("transporter", r10(est * 1.05))],
                 "B": [("transporter", r10(est * 1.15)), ("farmer", r10(est * 1.0))],
                 "C": [("transporter", r10(est * 1.2)), ("farmer", r10(est * 0.95)), ("transporter", r10(est * 1.05))]}
        plan = plans[pattern]
        msgs = {"transporter": "Quote for the full trip including loading help.",
                "farmer": "Can you do it for this amount? Regular customer."}
        for i, (by, amount) in enumerate(plan):
            last = i == len(plan) - 1
            at = self.T(start + dt.timedelta(hours=2 * i))
            self.add(models.TransportOffer(
                transport_request_id=tr.id, sequence=i + 1, sender_role=by,
                sender_id=transporter.id if by == "transporter" else farmer.id,
                receiver_role="farmer" if by == "transporter" else "transporter",
                receiver_id=farmer.id if by == "transporter" else transporter.id,
                amount=amount, message=msgs[by], status="ACCEPTED" if last else "SUPERSEDED",
                created_at=at, responded_at=self.T(at + dt.timedelta(hours=2))))
        return plan[-1][1]

    def _chat(self, tr, farmer, transporter, start: dt.datetime, delivered: bool):
        lines = [("farmer", f"Produce is ready at {tr.pickup_location}; please arrive at {tr.pickup_time or '09:00'}."),
                 ("transporter", "Understood. The driver will call you from the highway turn-off."),
                 ("farmer", "Please weigh at the farm gate and share the slip.")]
        if delivered:
            lines.append(("transporter", f"Delivered at {tr.destination} and signed by the receiver."))
        for i, (by, text) in enumerate(lines):
            self.add(models.TransportMessage(
                transport_request_id=tr.id, sender_role=by, sender_id=farmer.id if by == "farmer" else transporter.id,
                recipient_role="transporter" if by == "farmer" else "farmer",
                recipient_id=transporter.id if by == "farmer" else farmer.id, message=text,
                created_at=self.T(start + dt.timedelta(hours=3 * i))))

    def _make_tr(self, *, farmer, buyer, lot, txn, transporter, pickup, dest, qty, status, sched, late, dlate, fmult,
                 pattern, created, shared=False, driver_idx=0, cancelled_by=None, negotiation=None):
        dist = distance_between(pickup, dest)
        veh = _vehicle_for(qty)
        est = max(int(round(dist * veh[2] / 10.0)) * 10, 800)
        drv = S.DRIVERS[driver_idx % len(S.DRIVERS)]
        picked = delivered = completed = promised = None
        if status in ("PICKED_UP", "IN_TRANSIT", "DELIVERED", "COMPLETED") and late is not None:
            picked = self.T(sched + dt.timedelta(hours=late))
        promised_day = (sched + IST).date() + dt.timedelta(days=1 if dist < 250 else 2)
        promised = promised_day.isoformat()
        if status in ("DELIVERED", "COMPLETED") and picked:
            if dlate:
                delivered = self.T(dt.datetime.combine(promised_day + dt.timedelta(days=1), dt.time(11, 0)) - IST)
            else:
                delivered = self.T(picked + dt.timedelta(hours=dist / 45.0 + 1.5))
            if status == "COMPLETED":
                completed = self.T(delivered + dt.timedelta(hours=4))
        negotiation = negotiation or ("OPEN" if transporter is None else "AGREED")
        tr = self.add(models.TransportRequest(
            lot_id=lot.id if lot else None, transaction_id=txn.id if txn else None, farmer_id=farmer.id,
            buyer_id=buyer.id if buyer else None, pickup_location=pickup, destination=dest,
            pickup_date=(sched + IST).date().isoformat(), pickup_time="09:00", vehicle_type=veh[0],
            driver_name=drv[0] if transporter else None, driver_contact=drv[1] if transporter else None,
            vehicle_capacity=veh[1], estimated_cost=float(est), shared_transport=shared, quantity_kg=qty,
            status=status, picked_up_at=picked, delivered_at=delivered, transporter_id=transporter.id if transporter else None,
            negotiation_status=negotiation, completed_at=completed, promised_delivery_by=promised,
            cancelled_by=cancelled_by, cancelled_at=self.T(created + dt.timedelta(days=1)) if cancelled_by else None,
            created_at=created, updated_at=completed or delivered or picked or created))
        agreed = None
        if transporter is not None and negotiation in ("AGREED", "NEGOTIATING"):
            if negotiation == "AGREED":
                agreed = self._offers_for(tr, farmer, transporter, est, pattern, created)
                at = self.T(created + dt.timedelta(hours=6))
                tr.claimed_at = created
                tr.transporter_agreed_price = float(agreed)
                tr.transporter_agreed_at = at
                # legacy quote fields mirror the agreed amount so receipts/old screens agree
                tr.quote_status, tr.quoted_price, tr.quoted_at = "ACCEPTED", float(agreed), created
                tr.agreed_price, tr.agreed_at = float(agreed), at
                if fmult and delivered:
                    tr.final_charge = float(round(agreed * fmult))
                    tr.final_charge_recorded_at = self.T(delivered + dt.timedelta(hours=6))
        self.db.flush()
        return tr, agreed

    # -- timeline + payments + receipts + QoS for each deal -------------------
    def seed_deal_lifecycles(self):
        for key, r in self.deal_rows.items():
            d, farmer, buyer, txn = r["spec"], r["farmer"], r["buyer"], r["txn"]
            lot = r["lot"]
            reached = STAGES.index(d["status"])
            t_acc, sched = r["t_acc"], r["sched"]
            tr = None
            # ---- transport leg
            picked = delivered = None
            if d["tr"]:
                spec = d["tr"]
                transporter = self.transporters[spec["t"]] if spec["t"] is not None else None
                created = self.T(t_acc + dt.timedelta(hours=8))
                status = {"COMPLETED": "COMPLETED", "IN_TRANSIT": "IN_TRANSIT", "PICKED_UP": "PICKED_UP",
                          "LOGISTICS_CONFIRMED": "CONFIRMED", "LOGISTICS_PENDING": "REQUESTED"}[d["status"]]
                tr, agreed = self._make_tr(
                    farmer=farmer, buyer=buyer, lot=lot, txn=txn, transporter=transporter, pickup=farmer.location,
                    dest=buyer.location, qty=d["qty"], status=status, sched=sched,
                    late=spec["late"], dlate=spec["dlate"], fmult=spec["fmult"], pattern=spec["neg"] or "A",
                    created=created, driver_idx=list(self.deal_rows).index(key))
                picked, delivered = tr.picked_up_at, tr.delivered_at
                if transporter is not None and status != "REQUESTED":
                    self._chat(tr, farmer, transporter, self.T(created + dt.timedelta(hours=7)), status == "COMPLETED")
                r["tr"], r["agreed_transport"] = tr, agreed
            elif reached >= STAGES.index("PICKED_UP"):
                pickup_late = (d["rec"] or {}).get("pickup") == "LATE"
                picked = self.T(sched + dt.timedelta(hours=5 if pickup_late else 0.3))
                delivered = self.T(picked + dt.timedelta(hours=6))
            # ---- event timeline
            ev = [("OFFER_CREATED", f"Offer of Rs {d['rounds'][0]}/kg submitted by {buyer.company_name}", "buyer", buyer.id, r["t0"]),
                  ("OFFER_ACCEPTED", f"Offer accepted at Rs {d['rounds'][-1]}/kg by {r['accepted_by']}",
                   r["accepted_by"], farmer.id if r["accepted_by"] == "farmer" else buyer.id, t_acc),
                  ("AGREEMENT_RECORDED", f"Terms agreed after {len(d['rounds'])} round(s)", r["accepted_by"],
                   farmer.id if r["accepted_by"] == "farmer" else buyer.id, t_acc)]
            conf_t = self.T(t_acc + dt.timedelta(hours=4))
            log_t = self.T(max(sched - dt.timedelta(hours=18), t_acc + dt.timedelta(hours=10)))
            if reached >= 1:
                ev.append(("ORDER_CONFIRMED", "Order confirmed by buyer", "buyer", buyer.id, conf_t))
            if reached >= 2 and d["mode"] != "BUYER_PICKUP":
                ev.append(("LOGISTICS_PENDING", "Transport requested by farmer", "farmer", farmer.id,
                           self.T(t_acc + dt.timedelta(hours=8))))
            if reached >= 3:
                ev.append(("LOGISTICS_CONFIRMED",
                           "Buyer pickup scheduled" if d["mode"] == "BUYER_PICKUP" else "Transport confirmed with agreed price",
                           "farmer", farmer.id, log_t))
            if reached >= 4 and picked:
                ev.append(("PICKED_UP", f"Produce picked up from {farmer.location}", "system", None, picked))
            if reached >= 5 and picked:
                ev.append(("IN_TRANSIT", f"In transit to {buyer.location}", "system", None, self.T(picked + dt.timedelta(hours=1))))
            if reached >= 6 and delivered:
                ev.append(("DELIVERED", f"Delivered to {buyer.company_name}, {buyer.location}", "buyer", buyer.id,
                           self.T(delivered + dt.timedelta(hours=1))))
            pay_t = self.T(delivered + dt.timedelta(hours=3)) if delivered else None
            if reached >= 7 and pay_t:
                ev.append(("PAYMENT_PENDING", "Payment requested", "buyer", buyer.id, pay_t))
            if reached >= 8 and pay_t:
                ev.append(("PAYMENT_INITIATED", f"Payment of Rs {txn.total_amount:,.0f} initiated via {d['pay'][0]}",
                           "buyer", buyer.id, self.T(pay_t + dt.timedelta(hours=18))))
            if reached >= 9 and pay_t:
                ev.append(("PAYMENT_RECEIVED", "Payment confirmed received by farmer", "farmer", farmer.id,
                           self.T(pay_t + dt.timedelta(days=1, hours=2))))
            if reached >= 10 and pay_t:
                ev.append(("COMPLETED", "Transaction completed successfully", "system", None,
                           self.T(pay_t + dt.timedelta(days=1, hours=3))))
            for etype, desc, by, by_id, when in ev:
                self.add(models.TransactionEvent(transaction_id=txn.id, event_type=etype, description=desc,
                                                 performed_by=by, performed_by_id=by_id, created_at=self.T(when)))
            txn.updated_at = max(self.T(e[4]) for e in ev)
            r["delivered"], r["picked"], r["pay_t"] = delivered, picked, pay_t
            # ---- payments
            if d["pay"] and pay_t:
                self._payments(r)
            # ---- farmer-recorded QoS evidence
            if d["rec"] and delivered:
                for metric, result in (("BUYER_PICKUP", d["rec"].get("pickup")), ("BUYER_TERMS", d["rec"].get("terms"))):
                    if not result:
                        continue
                    note = {"LATE": "Truck arrived well after the agreed slot.", "DEVIATED": "Final weighing differed from the agreed terms.",
                            "ON_TIME": "Arrived within the agreed slot.", "AS_AGREED": "Price, quantity and grade as agreed."}[result]
                    rec = self.add(models.PerformanceRecord(
                        subject_role="buyer", subject_id=buyer.id, transaction_id=txn.id, metric=metric, result=result,
                        note=note, recorded_by_role="farmer", recorded_by_id=farmer.id,
                        created_at=self.T(delivered + dt.timedelta(days=1))))
                    r.setdefault("records", {})[metric] = rec
            # ---- ratings once completed
            if d["rate"] and d["status"] == "COMPLETED":
                self._ratings(txn, farmer, buyer, d["rate"], self.T(pay_t + dt.timedelta(days=2)))
            # ---- reviews of the transport leg
            if tr is not None and tr.status == "COMPLETED":
                self._transport_reviews(tr, farmer, self.transporters[d["tr"]["t"]], d["tr"])

    def _payments(self, r):
        d, farmer, buyer, txn, pay_t = r["spec"], r["farmer"], r["buyer"], r["txn"], r["pay_t"]
        method, plan = d["pay"]
        due = (pay_t + dt.timedelta(days=2)).date().isoformat()

        def pay(status, init=None, recv=None, note="", m=method, when=None):
            return self.add(models.Payment(
                transaction_id=txn.id, buyer_id=buyer.id, farmer_id=farmer.id, amount=txn.total_amount, currency="INR",
                payment_status=status, payment_method=m if status != "DUE" else None,
                payment_reference=self.payment_ref() if status not in ("DUE", "PENDING") else None,
                payment_due_date=due, initiated_at=init, received_at=recv,
                notes=note or "Demo simulated payment — not a real financial transaction.", is_demo=True,
                created_at=when or pay_t, updated_at=recv or init or pay_t))
        init = self.T(pay_t + dt.timedelta(hours=18))
        recv = self.T(pay_t + dt.timedelta(days=1, hours=2))
        if plan == "DUE":
            pay("DUE", note="Demo simulated payment — payment due within 2 days of delivery.")
        elif plan == "FAILED_THEN_PAID":
            pay("FAILED", init=pay_t, note="Demo simulated payment — UPI timeout, buyer asked to retry.", m="UPI")
            pay("PAID", init=init, recv=recv)
        elif plan == "DISPUTED_THEN_PAID":
            pay("DISPUTED", init=pay_t, note="Demo simulated payment — amount disputed over final weighing.")
            pay("PAID", init=init, recv=recv)
        else:
            pay("PAID", init=init, recv=recv)

    def _ratings(self, txn, farmer, buyer, rate, when):
        f2b, b2f = rate
        txt = lambda v, who: {5.0: f"Excellent {who}, smooth and on time.", 4.5: f"Very good {who}, would trade again.",
                              4.0: f"Good {who} overall, minor delays.", 3.5: f"Acceptable {who}; some friction on terms."}.get(
            v, f"Rated {v}/5.")
        self.add(models.Rating(transaction_id=txn.id, rater_role="farmer", rater_id=farmer.id, ratee_role="buyer",
                               ratee_id=buyer.id, rating=f2b, review=txt(f2b, "buyer"), created_at=when))
        self.add(models.Rating(transaction_id=txn.id, rater_role="buyer", rater_id=buyer.id, ratee_role="farmer",
                               ratee_id=farmer.id, rating=b2f, review=txt(b2f, "farmer"),
                               created_at=when + dt.timedelta(hours=5)))

    def _transport_reviews(self, tr, farmer, transporter, spec):
        penalty = (1.0 if (spec.get("late") or 0) > 2 else 0) + (1.0 if spec.get("dlate") else 0) + \
                  (0.5 if (spec.get("fmult") or 1) > 1.05 else 0)
        score = max(2.5, min(5.0, 4.5 - penalty))
        at = self.T((tr.completed_at or self.now) + dt.timedelta(days=1))
        self.add(models.TransportReview(
            transport_request_id=tr.id, reviewer_role="farmer", reviewer_id=farmer.id, reviewee_role="transporter",
            reviewee_id=transporter.id, rating=score, punctuality=max(2.0, score - (0.5 if penalty else 0)),
            communication=min(5.0, score + 0.5), handling=min(5.0, score + 0.5),
            comment="Produce arrived intact." if penalty == 0 else "Delays and a higher final charge than quoted.",
            created_at=at))
        self.add(models.TransportReview(
            transport_request_id=tr.id, reviewer_role="transporter", reviewer_id=transporter.id, reviewee_role="farmer",
            reviewee_id=farmer.id, rating=4.5, punctuality=4.5, communication=4.5, reliability=4.5,
            comment="Produce was ready and loading was quick.", created_at=at + dt.timedelta(hours=2)))

    # -- existing base transactions (txn1 / txn2): fill in the missing legs ---
    def seed_base_transactions(self):
        db = self.db
        for txn, t_idx, pickup, dest, qty, days_pick, days_del, shared in (
                (self.txn1, 0, "Bilaspur", "Raipur", 2000, 7, 5, True),
                (self.txn2, 7, "Raigarh", "Bilaspur", 3000, 2, 1, False)):
            if txn is None:
                continue
            farmer = db.get(models.Farmer, txn.farmer_id)
            buyer = db.get(models.Buyer, txn.buyer_id)
            sched = dt.datetime.combine((self.now - dt.timedelta(days=days_pick)).date(), dt.time(9, 0)) - IST
            tr, _ = self._make_tr(
                farmer=farmer, buyer=buyer, lot=None, txn=txn, transporter=self.transporters[t_idx], pickup=pickup,
                dest=dest, qty=qty, status="COMPLETED", sched=sched, late=0.3, dlate=False, fmult=1.0, pattern="A",
                created=self.T(sched - dt.timedelta(days=3)), shared=shared, driver_idx=t_idx)
            tr.delivered_at = self.T(dt.datetime.combine((self.now - dt.timedelta(days=days_del)).date(), dt.time(15, 0)) - IST)
            tr.completed_at = self.T(tr.delivered_at + dt.timedelta(hours=4))
            tr.final_charge_recorded_at = self.T(tr.delivered_at + dt.timedelta(hours=6))
            self._chat(tr, farmer, self.transporters[t_idx], self.T(sched - dt.timedelta(days=2)), True)
            self._transport_reviews(tr, farmer, self.transporters[t_idx], dict(late=0.3, dlate=False, fmult=1.0))
            self.base_trs = getattr(self, "base_trs", {})
            self.base_trs[txn.id] = tr
        if self.txn1:
            when = self.T(self.now - dt.timedelta(days=3))
            self._ratings(self.txn1, db.get(models.Farmer, self.txn1.farmer_id), db.get(models.Buyer, self.txn1.buyer_id),
                          (4.5, 5.0), when)
            for metric, result, note in (("BUYER_PICKUP", "ON_TIME", "Arrived within the agreed slot."),
                                         ("BUYER_TERMS", "AS_AGREED", "Price, quantity and grade as agreed.")):
                self.add(models.PerformanceRecord(
                    subject_role="buyer", subject_id=self.txn1.buyer_id, transaction_id=self.txn1.id, metric=metric,
                    result=result, note=note, recorded_by_role="farmer", recorded_by_id=self.txn1.farmer_id,
                    created_at=when))

    # -- receipts -------------------------------------------------------------
    def seed_receipts(self):
        from app.services import receipt_service as rs
        db = self.db
        targets = [r["txn"] for r in self.deal_rows.values()
                   if r["spec"]["status"] in ("COMPLETED", "PAYMENT_RECEIVED", "DELIVERED")]
        targets += [t for t in (self.txn1, self.txn2) if t is not None]
        seq = db.query(models.Receipt).count()
        for txn in sorted(targets, key=lambda t: t.id):
            if db.query(models.Receipt).filter_by(transaction_id=txn.id).first():
                continue
            seq += 1
            farmer, buyer = db.get(models.Farmer, txn.farmer_id), db.get(models.Buyer, txn.buyer_id)
            payment = db.query(models.Payment).filter_by(transaction_id=txn.id).order_by(models.Payment.id.desc()).first()
            tr = db.query(models.TransportRequest).filter_by(transaction_id=txn.id).order_by(models.TransportRequest.id.desc()).first()
            transport_cost = None
            if tr is not None:
                transport_cost = tr.agreed_price if tr.agreed_price is not None else tr.estimated_cost
            events = (db.query(models.TransactionEvent).filter_by(transaction_id=txn.id)
                      .order_by(models.TransactionEvent.created_at.asc(), models.TransactionEvent.id.asc()).all())
            crop = None
            if txn.lot_id:
                crop = db.get(models.Lot, txn.lot_id).crop
            elif txn.listing_id:
                crop = db.get(models.CropListing, txn.listing_id).crop
            receipt_id = f"CW-RCPT-{seq:06d}"
            generated = self.T(max(e.created_at for e in events) + dt.timedelta(hours=2))
            payload = {
                "receipt_version": rs.RECEIPT_VERSION, "transaction_id": txn.id,
                "supplier": {"id": txn.farmer_id, "name": farmer.name}, "buyer": {"id": txn.buyer_id, "name": buyer.company_name},
                "commodity": crop, "quantity_kg": txn.quantity_kg, "agreed_price_per_kg": txn.final_price_per_kg,
                "sale_amount": txn.total_amount, "transport_cost": transport_cost,
                "total_amount": round(txn.total_amount + transport_cost, 2) if transport_cost is not None else txn.total_amount,
                "market_used": txn.market_used or None, "transaction_status": txn.status,
                "payment_status": payment.payment_status if payment else None,
                "transaction_created_at": rs._iso(txn.created_at),
                "events": [{"event_type": e.event_type, "performed_by": e.performed_by, "created_at": rs._iso(e.created_at)}
                           for e in events],
                "receipt_id": receipt_id, "generated_at": rs._iso(generated)}
            self.add(models.Receipt(receipt_id=receipt_id, transaction_id=txn.id, receipt_version=rs.RECEIPT_VERSION,
                                    payload=payload, hash_algorithm=rs.HASH_ALGORITHM, hash_value=rs.compute_hash(payload),
                                    generated_at=generated))
            self.add(models.TransactionEvent(
                transaction_id=txn.id, event_type="RECEIPT_GENERATED", description=f"Receipt {receipt_id} generated",
                performed_by="system", event_metadata={"receipt_id": receipt_id, "hash_algorithm": rs.HASH_ALGORITHM},
                created_at=generated))

    # -- unsold supply with live offers --------------------------------------
    def _extra_offer(self, offer_spec, farmer, supply, is_listing, grade, qty_cap, demand=None):
        buyer_idx, qty, price, status, message = offer_spec
        buyer = self.buyers[buyer_idx]
        t = self.days_ago(self.rng.randint(1, 5), hour=self.now.hour)
        live_price = price + 1.0 if status == "counter" else price
        offer_status = {"counter": "pending"}.get(status, status)
        offer = self.add(models.BuyerOffer(
            buyer_id=buyer.id, listing_id=supply.id if is_listing else None, lot_id=None if is_listing else supply.id,
            buyer_demand_id=demand.id if demand else None, offered_price_per_kg=live_price, quantity_kg=qty,
            message=message, language="en", status=offer_status, created_at=t))
        terms = lambda p: dict(price_per_kg=p, quantity_kg=qty, quality_grade=grade,
                               quality_notes=f"Grade {grade} requested", pickup_mode="TO_BE_AGREED",
                               pickup_date=None, delivery_location=None, delivery_deadline=None)
        if status == "pending":
            self._round(offer, 1, "buyer", buyer.id, terms(price), message, "PROPOSED", t)
        elif status == "rejected":
            self._round(offer, 1, "buyer", buyer.id, terms(price), message, "REJECTED", t, self.T(t + dt.timedelta(hours=6)), "farmer")
        elif status == "withdrawn":
            self._round(offer, 1, "buyer", buyer.id, terms(price), message, "WITHDRAWN", t, self.T(t + dt.timedelta(hours=8)), "buyer")
        elif status == "counter":
            self._round(offer, 1, "buyer", buyer.id, terms(price), message, "COUNTERED", t, self.T(t + dt.timedelta(hours=4)), "farmer")
            self._round(offer, 2, "farmer", farmer.id, terms(live_price), "Counter: Grade A, tested lot, delivery extra.",
                        "PROPOSED", self.T(t + dt.timedelta(hours=4)))
        return offer

    def seed_extra_supply(self):
        self.extra_lots = {}
        for spec in S.EXTRA_LISTINGS:
            farmer = self.farmers[spec["farmer"]]
            created = self.days_ago(30 if spec["status"] == "expired" else 3)
            listing = self._make_listing(farmer, spec["crop"], spec["qty"], spec["grade"], spec["q"], spec["ask"],
                                         spec["floor"], spec["status"], created, spec["avail_days"], spec["deadline_days"])
            for o in spec["offers"]:
                self._extra_offer(o, farmer, listing, True, spec["grade"], spec["qty"])
        for spec in S.EXTRA_LOTS:
            farmer = self.farmers[spec["farmer"]]
            fpo_id = self.pools[spec["fpo"]].id if spec["fpo"] is not None else None
            lot = self._make_lot(farmer, spec["crop"], spec["qty"], spec["grade"], spec["q"], spec["price"],
                                 spec["minp"], spec["status"], self.days_ago(2), spec["harvest_days_ago"], fpo_id,
                                 spec.get("note"))
            self.extra_lots[spec["key"]] = lot
            demand = None
            if spec["key"] == "XL8":   # fulfils FarmLink Agro's standing (base-seed) Soybean demand
                demand = (self.db.query(models.BuyerDemand)
                          .filter_by(buyer_id=self.buyers[6].id, crop="Soybean", status="ACTIVE").first())
            for o in spec["offers"]:
                self._extra_offer(o, farmer, lot, False, spec["grade"], spec["qty"], demand if o[0] == 6 else None)

    # -- pools, shared trips, extra transport --------------------------------
    def seed_pools(self):
        self.pools = []
        for i, p in enumerate(S.POOLS):
            pool = self.add(models.GroupSellingPool(crop=p["crop"], fpo_name=p["fpo"], status=p["status"],
                                                    created_at=self.days_ago(40 - i * 3)))
            for j, (fidx, qty) in enumerate(p["members"]):
                self.add(models.GroupPoolMembership(pool_id=pool.id, farmer_id=self.farmers[fidx].id, quantity_kg=qty,
                                                    joined_at=self.days_ago(38 - i * 3 - j)))
            self.pools.append(pool)
        existing = (self.db.query(models.GroupSellingPool)
                    .filter_by(crop="Chana (Gram)", fpo_name="Durg Farmer Collective").first())
        if existing:
            for j, (fidx, qty) in enumerate(S.POOL_EXISTING_EXTRA_MEMBERS):
                if not self.db.query(models.GroupPoolMembership).filter_by(pool_id=existing.id,
                                                                           farmer_id=self.farmers[fidx].id).first():
                    self.add(models.GroupPoolMembership(pool_id=existing.id, farmer_id=self.farmers[fidx].id,
                                                        quantity_kg=qty, joined_at=self.days_ago(6 - j)))

    def seed_shared_trips(self):
        self.shared = []
        for i, st in enumerate(S.SHARED_TRIPS):
            pool = self.pools[st["pool"]]
            members = S.POOLS[st["pool"]]["members"]
            organiser = self.farmers[members[0][0]]
            qty = float(sum(q for _, q in members))
            transporter = self.transporters[st["t"]]
            sched = dt.datetime.combine((self.now - dt.timedelta(days=st["days_ago"])).date(), dt.time(9, 0)) - IST
            tr, _ = self._make_tr(farmer=organiser, buyer=None, lot=None, txn=None, transporter=transporter,
                                  pickup=st["pickup"], dest=st["dest"], qty=min(qty, 5000), status="DELIVERED",
                                  sched=sched, late=0.4, dlate=False, fmult=1.02, pattern="B",
                                  created=self.T(sched - dt.timedelta(days=4)), shared=True, driver_idx=i + 3)
            self._chat(tr, organiser, transporter, self.T(sched - dt.timedelta(days=2)), True)
            self.shared.append(tr)
            when = self.T((tr.delivered_at or self.now) + dt.timedelta(days=1))
            for k, (fidx, t_rating, j_rating) in enumerate(st["reviews"]):
                farmer = self.farmers[fidx]
                base = dict(transport_request_id=tr.id, pool_id=pool.id, reviewer_farmer_id=farmer.id, verified=True,
                            created_at=when + dt.timedelta(hours=k))
                self.add(models.TripReview(review_type="TRANSPORTER", rating=t_rating, punctuality=t_rating,
                                           communication=min(5.0, t_rating + 0.5), handling=t_rating,
                                           comment="Driver was careful with the load.", **base))
                self.add(models.TripReview(review_type="JOURNEY", rating=j_rating, punctuality=j_rating,
                                           coordination=j_rating, communication=j_rating,
                                           comment="Pickup and drop were well coordinated.", **base))
                if k == 0:
                    self.add(models.TripReview(review_type="FPO", rating=4.5, coordination=4.5, communication=4.5,
                                               comment=f"{pool.fpo_name} organised the trip well.", **base))

    def seed_extra_transport(self):
        for i, x in enumerate(S.EXTRA_TRANSPORT):
            farmer = self.farmers[x["farmer"]]
            transporter = self.transporters[x["t"]] if x["t"] is not None else None
            created = self.days_ago(x["days_ago"])
            sched = dt.datetime.combine((created + dt.timedelta(days=x["pu"])).date(), dt.time(9, 0)) - IST
            kind = x["kind"]
            status = {"CANCELLED_BY_FARMER": "CANCELLED", "CANCELLED_BY_TRANSPORTER": "CANCELLED",
                      "NEGOTIATING": "REQUESTED", "OPEN": "REQUESTED"}[kind]
            cancelled_by = {"CANCELLED_BY_FARMER": "farmer", "CANCELLED_BY_TRANSPORTER": "transporter"}.get(kind)
            negotiation = {"NEGOTIATING": "NEGOTIATING", "OPEN": "OPEN"}.get(kind, "AGREED")
            tr, _ = self._make_tr(farmer=farmer, buyer=None, lot=None, txn=None, transporter=transporter,
                                  pickup=x["pickup"], dest=x["dest"], qty=x["qty"], status=status, sched=sched,
                                  late=None, dlate=False, fmult=None, pattern="B", created=created,
                                  driver_idx=i + 5, cancelled_by=cancelled_by, negotiation=negotiation)
            if kind == "NEGOTIATING":
                est = int(tr.estimated_cost)
                tr.claimed_at = created
                for n, (by, amt, st) in enumerate([("transporter", est + 600, "SUPERSEDED"), ("farmer", est - 200, "SUPERSEDED"),
                                                    ("transporter", est + 250, "PENDING")]):
                    at = self.T(created + dt.timedelta(hours=2 * n))
                    self.add(models.TransportOffer(
                        transport_request_id=tr.id, sequence=n + 1, sender_role=by,
                        sender_id=transporter.id if by == "transporter" else farmer.id,
                        receiver_role="farmer" if by == "transporter" else "transporter",
                        receiver_id=farmer.id if by == "transporter" else transporter.id, amount=float(amt),
                        message="Updated quote for the trip." if by == "transporter" else "Please reduce a little.",
                        status=st, created_at=at, responded_at=None if st == "PENDING" else self.T(at + dt.timedelta(hours=2))))
                self._chat(tr, farmer, transporter, created, False)
            if cancelled_by:
                self._chat(tr, farmer, transporter, created, False)
                self.add(models.TransportMessage(
                    transport_request_id=tr.id, sender_role=cancelled_by,
                    sender_id=farmer.id if cancelled_by == "farmer" else transporter.id,
                    recipient_role="transporter" if cancelled_by == "farmer" else "farmer",
                    recipient_id=transporter.id if cancelled_by == "farmer" else farmer.id,
                    message=x["note"], created_at=self.T(created + dt.timedelta(days=1))))

    # -- storage bookings -----------------------------------------------------
    def seed_storage(self):
        today = self.now.date()
        for fidx, facility_name, ref, qty, start_off, nights, status in S.STORAGE_BOOKINGS:
            facility = self.db.query(models.StorageFacility).filter_by(name=facility_name).first()
            if facility is None:
                continue
            lot = self.deal_rows[ref]["lot"] if ref in self.deal_rows else self.extra_lots.get(ref)
            start = today + dt.timedelta(days=start_off)
            end = start + dt.timedelta(days=nights)
            self.add(models.StorageBooking(
                farmer_id=self.farmers[fidx].id, storage_facility_id=facility.id, lot_id=lot.id if lot else None,
                quantity_kg=float(qty), start_date=start.isoformat(), end_date=end.isoformat(),
                estimated_cost=round(qty * facility.price_per_kg_per_day * nights, 2), status=status,
                created_at=self.T(dt.datetime.combine(start, dt.time(8, 0)) - dt.timedelta(days=2)),
                updated_at=self.T(dt.datetime.combine(start, dt.time(8, 0)))))

    # -- grievances + reputation disputes ------------------------------------
    def seed_grievances(self):
        for key, by, category, status, priority, days_ago, desc, resolution in S.GRIEVANCES:
            r = self.deal_rows[key]
            farmer, buyer = r["farmer"], r["buyer"]
            created = self.days_ago(days_ago)
            closed = status in ("RESOLVED", "REJECTED", "CLOSED")
            self.add(models.Grievance(
                transaction_id=r["txn"].id, raised_by=by, raised_by_id=farmer.id if by == "farmer" else buyer.id,
                against_user="buyer" if by == "farmer" else "farmer",
                against_user_id=buyer.id if by == "farmer" else farmer.id, category=category,
                description=f"{desc} (Synthetic demo grievance)",
                evidence_urls=[f"demo://evidence/{key.lower()}_{category.lower()}.jpg"] if status != "OPEN" else [],
                status=status, priority=priority, assigned_to="CropWise Support Desk" if status != "OPEN" else None,
                resolution=resolution if closed else None, created_at=created,
                updated_at=self.T(created + dt.timedelta(days=2)) if status != "OPEN" else created,
                resolved_at=self.T(created + dt.timedelta(days=3)) if closed else None))

    def seed_disputes(self):
        for dsp in S.DISPUTES:
            created = self.days_ago(dsp["days_ago"])
            decided = dsp["status"] in ("UPHELD", "REJECTED")
            if dsp["kind"] == "record":
                r = self.deal_rows[dsp["deal"]]
                target, ttype, role, subject = r["records"][dsp["metric"]], "PERFORMANCE_RECORD", "buyer", r["buyer"]
            else:
                if "shared" in dsp:
                    target = self.shared[dsp["shared"]]
                    subject = self.transporters[S.SHARED_TRIPS[dsp["shared"]]["t"]]
                else:
                    target = self.deal_rows[dsp["deal"]]["tr"]
                    subject = self.transporters[self.deal_rows[dsp["deal"]]["spec"]["tr"]["t"]]
                ttype, role = "TRANSPORT_REQUEST", "transporter"
            self.add(models.ReputationDispute(
                subject_role=role, subject_id=subject.id, target_type=ttype, target_id=target.id, reason=dsp["reason"],
                evidence_urls=[], status=dsp["status"], admin_note=dsp["note"], created_at=created,
                updated_at=self.T(created + dt.timedelta(days=2)),
                resolved_at=self.T(created + dt.timedelta(days=2)) if decided else None))

    # -- notifications + login activity --------------------------------------
    def seed_notifications(self):
        for who, idx, ntype, sev, title, msg, ago, read in S.NOTIFICATIONS:
            user = (self.farmers if who == "farmer" else self.buyers)[idx]
            self.add(models.Notification(
                farmer_id=user.id if who == "farmer" else None, buyer_id=user.id if who == "buyer" else None,
                type=ntype, title=title, message=msg, severity=sev, is_read=read, created_at=self.days_ago(ago, hour=9)))
        for key, r in self.deal_rows.items():
            d, farmer, buyer = r["spec"], r["farmer"], r["buyer"]
            where = "listing" if d["flow"] == "listing" else "lot"
            self.add(models.Notification(
                farmer_id=farmer.id, type="offer_update", severity="info", title="New offer received",
                message=f"{buyer.company_name} offered Rs {d['rounds'][0]}/kg for {d['qty']} kg of {d['crop']} on your {where}.",
                is_read=d["days_ago"] > 5, created_at=r["t0"]))
            self.add(models.Notification(
                buyer_id=buyer.id, type="NEGOTIATION", severity="success", title="Offer accepted",
                message=f"Terms agreed at Rs {d['rounds'][-1]}/kg for {d['qty']} kg of {d['crop']} with {farmer.name}.",
                is_read=d["days_ago"] > 5, created_at=r["t_acc"]))
            if d["pay"] and d["pay"][1] == "DUE":
                self.add(models.Notification(
                    buyer_id=buyer.id, type="payment_due", severity="warning", title="Payment reminder",
                    message=f"Payment of Rs {r['txn'].total_amount:,.0f} to {farmer.name} is overdue.",
                    is_read=False, created_at=self.days_ago(1)))

    def seed_logins(self):
        users = [("farmer", f) for f in self.farmers] + [("buyer", b) for b in self.buyers] + \
                [("transporter", t) for t in self.transporters]
        for n, (role, u) in enumerate(users):
            latest = None
            for k in range(3 + n % 3):
                when = self.T(self.now - dt.timedelta(days=self.rng.randint(0, 29) + k, hours=self.rng.randint(0, 20)))
                self.add(models.LoginEvent(user_id=u.id, role=role, login_time=when, success=True))
                latest = max(latest, when) if latest else when
            u.last_login = latest
            if n % 4 == 0:     # a mistyped password now and then
                self.add(models.LoginEvent(user_id=u.id, role=role, success=False,
                                           login_time=self.T(self.now - dt.timedelta(days=self.rng.randint(0, 20)))))
        for k in range(4):     # attempts that matched no account
            self.add(models.LoginEvent(user_id=None, role="unknown", success=False,
                                       login_time=self.T(self.now - dt.timedelta(days=k * 3, hours=2))))

    # -- derived aggregates ---------------------------------------------------
    def finalize(self):
        db = self.db
        for t in self.transporters:
            rows = (db.query(models.TransportReview)
                    .filter_by(reviewee_role="transporter", reviewee_id=t.id).all())
            trips = db.query(models.TripReview).filter_by(review_type="TRANSPORTER").join(
                models.TransportRequest, models.TransportRequest.id == models.TripReview.transport_request_id
            ).filter(models.TransportRequest.transporter_id == t.id).all()
            vals = [r.rating for r in rows] + [r.rating for r in trips]
            if vals:
                t.rating, t.rating_count = round(sum(vals) / len(vals), 2), len(vals)
        for f in self.farmers:
            got = db.query(models.Rating).filter_by(ratee_role="farmer", ratee_id=f.id).all()
            if got:
                f.rating = round(sum(r.rating for r in got) / len(got), 2)
        db.commit()

    def run(self):
        self.resolve_accounts()
        self.seed_buyers_transporters()
        self.seed_kyc()
        self.seed_pools()
        self.seed_demands()
        self.seed_deals()
        self.seed_deal_lifecycles()
        self.seed_base_transactions()
        self.seed_extra_supply()
        self.seed_shared_trips()
        self.seed_extra_transport()
        self.seed_receipts()
        self.seed_storage()
        self.seed_grievances()
        self.seed_disputes()
        self.seed_notifications()
        self.seed_logins()
        self.finalize()
        return self.manifest


# ── public API ───────────────────────────────────────────────────────────────
def already_seeded(db) -> bool:
    return db.query(models.Transporter).filter_by(email=S.TRANSPORTERS[0]["email"]).first() is not None


def seed(db, now: Optional[dt.datetime] = None) -> Dict[str, List[int]]:
    if already_seeded(db):
        raise RuntimeError("Full synthetic data is already present; run with --reset first.")
    s = Seeder(db, now)
    try:
        s.run()
    except Exception:
        db.rollback()
        raise
    out = dict(s.manifest)
    out["_restore"] = s.restore
    return out


def reset(db, manifest: Dict) -> None:
    from app.database import Base
    restore = manifest.pop("_restore", {})
    for table in reversed(Base.metadata.sorted_tables):
        ids = manifest.get(table.name)
        if ids:
            db.execute(table.delete().where(table.c.id.in_(ids)))
    for fid, vals in restore.get("farmers", {}).items():
        f = db.get(models.Farmer, int(fid))
        if f:
            f.rating = vals["rating"]
            f.last_login = dt.datetime.fromisoformat(vals["last_login"]) if vals["last_login"] else None
    for bid, vals in restore.get("buyers", {}).items():
        b = db.get(models.Buyer, int(bid))
        if b:
            b.last_login = dt.datetime.fromisoformat(vals["last_login"]) if vals["last_login"] else None
    db.commit()


def summary(db) -> List[str]:
    from app.database import Base
    lines = []
    for table in Base.metadata.sorted_tables:
        n = db.execute(select(func.count()).select_from(table)).scalar()
        lines.append(f"  {table.name:34s} {n:6d}")
    return lines


def main(argv: List[str]) -> int:
    from app.database import Base, SessionLocal, engine, run_lightweight_migrations
    Base.metadata.create_all(bind=engine)
    run_lightweight_migrations()
    db = SessionLocal()
    try:
        if "--reset" in argv:
            if not MANIFEST.exists():
                print("Nothing to reset (no manifest found).")
                return 0
            reset(db, json.loads(MANIFEST.read_text()))
            MANIFEST.unlink()
            print("Full synthetic data removed.")
            return 0
        if db.query(models.Farmer).count() == 0:
            from app.seed_data import seed as base_seed
            base_seed()
        if MANIFEST.exists() or already_seeded(db):
            print("Already seeded. Run with --reset to remove it first.")
            return 1
        manifest = seed(db)
        MANIFEST.write_text(json.dumps(manifest))
        print("Seeded full synthetic dataset. Row counts per table:")
        print("\n".join(summary(db)))
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
