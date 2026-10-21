"""
Static tables for the full synthetic dataset (see seed_full_demo.py).

Everything here is invented demo data -- companies, people, GST/CIN numbers,
phone numbers and document links are fictional. Farmers and buyers are NOT
redefined here: they are the accounts already in demo_users.py, referenced by
their position in DEMO_FARMERS / DEMO_BUYERS (0-based). New buyers added here
continue that numbering (indexes 10, 11, 12).

Reference key
-------------
farmers  0 Ramesh(Bilaspur)   1 Sunita(Raigarh)    2 Manoj(Durg)       3 Preeti(Bilaspur)  4 Dilip(Rajnandgaon)
         5 Kavita(Mahasamund) 6 Ganesh(Korba)      7 Anita(Ambikapur)  8 Prakash(Jagdalpur) 9 Meena(Bilha)
buyers   0 FreshFoods(Raipur) 1 GreenBasket(Bilaspur) 2 AgriExport(Durg) 3 Wholesale Traders(Korba)
         4 Kisan Limited(Raipur) 5 KisanKart(Bilaspur) 6 FarmLink(Rajnandgaon) 7 GreenRoute(Mahasamund)
         8 Bharat Harvest(Ambikapur) 9 CropBridge(Korba)   10-12 new buyers below
"""

# ---------------------------------------------------------------------------
# Transport agencies (10). Same demo password as every other demo account.
# ---------------------------------------------------------------------------
TRANSPORTERS = [
    dict(name="Ravi Shrivas", business="Shree Ganesh Roadlines", email="shree.ganesh@cropwise.demo",
         phone="+91 90111 00001", area="Bilaspur - Raipur - Korba corridor",
         vehicles=["mini-truck", "truck"], lang="hi"),
    dict(name="Imran Khan", business="Maa Mahamaya Transport", email="mahamaya.transport@cropwise.demo",
         phone="+91 90111 00002", area="Raipur - Durg - Bhilai",
         vehicles=["truck"], lang="hi"),
    dict(name="Deepak Sahu", business="Chhattisgarh Kisan Carriers", email="kisan.carriers@cropwise.demo",
         phone="+91 90111 00003", area="Durg - Raipur - Ambikapur (long haul)",
         vehicles=["truck", "mini-truck"], lang="hi"),
    dict(name="Lakhan Baghel", business="Bastar Agri Movers", email="bastar.movers@cropwise.demo",
         phone="+91 90111 00004", area="Jagdalpur - Raipur - Durg",
         vehicles=["truck"], lang="en"),
    dict(name="Sanjay Rathore", business="Hasdeo Freight Services", email="hasdeo.freight@cropwise.demo",
         phone="+91 90111 00005", area="Korba - Bilaspur - Raigarh",
         vehicles=["mini-truck", "truck"], lang="hi"),
    dict(name="Bhuneshwar Sahu", business="Mahanadi Cargo", email="mahanadi.cargo@cropwise.demo",
         phone="+91 90111 00006", area="Mahasamund - Raipur - Korba",
         vehicles=["truck"], lang="hi"),
    dict(name="Anil Toppo", business="Surguja Road Haulers", email="surguja.haulers@cropwise.demo",
         phone="+91 90111 00007", area="Ambikapur - Raigarh - Raipur",
         vehicles=["truck", "mini-truck"], lang="en"),
    dict(name="Faizal Ansari", business="Raigarh Cold Chain Logistics", email="raigarh.coldchain@cropwise.demo",
         phone="+91 90111 00008", area="Raigarh - Bilaspur - Raipur (refrigerated)",
         vehicles=["refrigerated", "truck"], lang="hi"),
    dict(name="Pankaj Thakur", business="Kosa City Logistics", email="kosa.logistics@cropwise.demo",
         phone="+91 90111 00009", area="Bilaspur - Bilha - Raipur",
         vehicles=["mini-truck"], lang="hi"),
    dict(name="Narendra Dewangan", business="Rajnandgaon Agro Transport", email="rajnandgaon.agro@cropwise.demo",
         phone="+91 90111 00010", area="Rajnandgaon - Durg - Raipur",
         vehicles=["truck", "mini-truck"], lang="hi"),
]

# Driver names/contacts used on transport requests (rotated).
DRIVERS = [
    ("Ramu Yadav", "+91 97000 10001"), ("Kishore Netam", "+91 97000 10002"),
    ("Sundar Lal", "+91 97000 10003"), ("Mohan Patel", "+91 97000 10004"),
    ("Jagdish Markam", "+91 97000 10005"), ("Santosh Kumar", "+91 97000 10006"),
    ("Hemant Sinha", "+91 97000 10007"), ("Bablu Khan", "+91 97000 10008"),
]

# ---------------------------------------------------------------------------
# Three extra buyers, so the admin KYC queue has live items to review.
# verification: (internal status, method)
# ---------------------------------------------------------------------------
EXTRA_BUYERS = [
    dict(company_name="Mahanadi Fresh Mart", email="mahanadifresh@cropwise.demo", phone="+91 90002 10001",
         location="Raipur", latitude=21.2514, longitude=81.6296, buyer_type="retailer",
         crops_of_interest=["Tomato", "Onion", "Potato"], reliability_score=72.0, payment_history_score=75.0,
         ver=dict(status="UNDER_REVIEW", method="DOCUMENT_VERIFIED", gst="22AAFCM4401D1Z7",
                  reg="CIN-U52100CG2024PTC700101", lic="FSSAI-10024567890123",
                  docs=["demo://mahanadifresh_gst.pdf", "demo://mahanadifresh_fssai.pdf"], submitted_days_ago=2)),
    dict(company_name="Hasdeo Agro Foods", email="hasdeoagro@cropwise.demo", phone="+91 90002 10002",
         location="Korba", latitude=22.3595, longitude=82.7501, buyer_type="processor",
         crops_of_interest=["Wheat", "Maize", "Paddy (Rice)"], reliability_score=70.0, payment_history_score=70.0,
         ver=dict(status="PENDING", method="SELF_DECLARED", gst="22AAHCH7712E1Z2",
                  reg=None, lic=None, docs=[], submitted_days_ago=None)),
    dict(company_name="Satpura Exports", email="satpuraexports@cropwise.demo", phone="+91 90002 10003",
         location="Durg", latitude=21.1904, longitude=81.2849, buyer_type="exporter",
         crops_of_interest=["Soybean", "Groundnut", "Chana (Gram)"], reliability_score=74.0, payment_history_score=78.0,
         ver=dict(status="UNDER_REVIEW", method="DOCUMENT_VERIFIED", gst="22AABCS9023F1Z9",
                  reg="CIN-U51909CG2023PTC700203", lic="APEDA-EXP-2024-017",
                  docs=["demo://satpura_gst.pdf", "demo://satpura_apeda.pdf", "demo://satpura_iec.pdf"],
                  submitted_days_ago=4)),
]

# ---------------------------------------------------------------------------
# KYC / verification for the ORIGINAL buyers that have no verification row yet
# (indexes 3-9; indexes 0-2 already have one in seed_data.py).
# Buyer.verification_status ("verified"/"pending") already set in demo_users.py
# and is kept consistent: only VERIFIED rows belong to "verified" buyers.
# ---------------------------------------------------------------------------
BUYER_VERIFICATIONS = {
    3: dict(status="SUSPENDED", method="PLATFORM_VERIFIED", name="Chhattisgarh Wholesale Traders",
            reg="CIN-U51909CG2016PTC501001", gst="22AABCW3301G1Z4", lic=None,
            docs=["demo://cgwholesale_gst.pdf"], note="Suspended after two unresolved payment complaints. (Synthetic demo data)",
            reason=None),
    4: dict(status="VERIFIED", method="PLATFORM_VERIFIED", name="Kisan Limited",
            reg="CIN-U15400CG2017PLC501002", gst="22AABCK4402H1Z1", lic="FSSAI-10017654321098",
            docs=["demo://kisanlimited_gst.pdf", "demo://kisanlimited_fssai.pdf"], note="Documents verified by CropWise platform team. (Synthetic demo data)",
            reason=None),
    5: dict(status="VERIFIED", method="DOCUMENT_VERIFIED", name="KisanKart",
            reg="CIN-U52100CG2020PTC501003", gst="22AABCK5503J1Z6", lic=None,
            docs=["demo://kisankart_gst.pdf"], note="GST certificate matched to registered address. (Synthetic demo data)",
            reason=None),
    6: dict(status="VERIFIED", method="PLATFORM_VERIFIED", name="FarmLink Agro",
            reg="CIN-U01100CG2019PTC501004", gst="22AABCF6604K1Z8", lic="FSSAI-10019876543210",
            docs=["demo://farmlink_gst.pdf", "demo://farmlink_fssai.pdf"], note="Verified, site visit not required. (Synthetic demo data)",
            reason=None),
    7: dict(status="REJECTED", method="SELF_DECLARED", name="GreenRoute Foods",
            reg="CIN-U51909CG2022PTC501005", gst="22AABCG7705L1Z3", lic=None,
            docs=["demo://greenroute_gst_blurry.jpg"], note="Submitted GST certificate unreadable. (Synthetic demo data)",
            reason="GST certificate image is unreadable and the GSTIN does not match the business name. Please resubmit."),
    8: dict(status="VERIFIED", method="PLATFORM_VERIFIED", name="Bharat Harvest",
            reg="CIN-U01100CG2018PTC501006", gst="22AABCB8806M1Z0", lic="APEDA-EXP-2022-044",
            docs=["demo://bharatharvest_gst.pdf", "demo://bharatharvest_apeda.pdf"], note="Exporter licence verified. (Synthetic demo data)",
            reason=None),
    9: dict(status="VERIFIED", method="DOCUMENT_VERIFIED", name="CropBridge",
            reg="CIN-U51909CG2021PTC501007", gst="22AABCC9907N1Z5", lic=None,
            docs=["demo://cropbridge_gst.pdf"], note="GST verified. (Synthetic demo data)",
            reason=None),
}

# ---------------------------------------------------------------------------
# Buyer demands (12 new). `key` lets deals point back at the demand that
# produced them. status follows buyer_demands.VALID_STATUSES.
# ---------------------------------------------------------------------------
DEMANDS = [
    dict(key="DM_D02", buyer=4, crop="Tomato", req=3000, mn=2000, mx=4000, target=24.5, grade="A",
         loc="Raipur", dl=18, terms="Net 7 days after delivery", status="FULFILLED", created_days_ago=40),
    dict(key="DM_D03", buyer=6, crop="Soybean", req=3200, mn=2000, mx=4000, target=47.0, grade="A",
         loc="Rajnandgaon", dl=20, terms="50% advance, balance on delivery", status="FULFILLED", created_days_ago=36),
    dict(key="DM_D04", buyer=9, crop="Paddy (Rice)", req=5000, mn=3000, mx=6000, target=20.0, grade="B",
         loc="Korba", dl=18, terms="Cash on delivery", status="FULFILLED", created_days_ago=33),
    dict(key="DM_D05", buyer=2, crop="Groundnut", req=2200, mn=1500, mx=3000, target=58.5, grade="A",
         loc="Durg", dl=21, terms="Full payment within 7 days of delivery", status="FULFILLED", created_days_ago=30),
    dict(key="DM_D06", buyer=8, crop="Chana (Gram)", req=1800, mn=1000, mx=2500, target=53.0, grade="A",
         loc="Ambikapur", dl=20, terms="50% advance, balance on delivery", status="FULFILLED", created_days_ago=27),
    dict(key="DM_D07", buyer=0, crop="Onion", req=2800, mn=2000, mx=3500, target=18.5, grade="A",
         loc="Raipur", dl=15, terms="Net 7 days after delivery", status="FULFILLED", created_days_ago=24),
    dict(key="DM_D10", buyer=8, crop="Maize", req=3000, mn=2000, mx=3500, target=20.0, grade="B",
         loc="Ambikapur", dl=12, terms="Payment within 3 days of pickup", status="FULFILLED", created_days_ago=14),
    dict(key="DM_D11", buyer=2, crop="Soybean", req=6000, mn=3000, mx=8000, target=47.5, grade="A",
         loc="Durg", dl=14, terms="Full payment within 7 days of delivery", status="PARTIALLY_FILLED", created_days_ago=10),
    dict(key="DM_D12", buyer=4, crop="Paddy (Rice)", req=8000, mn=4000, mx=10000, target=20.5, grade="B",
         loc="Raipur", dl=14, terms="Net 7 days after delivery", status="PARTIALLY_FILLED", created_days_ago=9),
    dict(key="DM_EXP", buyer=7, crop="Wheat", req=4000, mn=2000, mx=5000, target=23.0, grade="B",
         loc="Mahasamund", dl=-5, terms="Cash on delivery", status="EXPIRED", created_days_ago=45),
    dict(key="DM_CXL", buyer=3, crop="Maize", req=2000, mn=1000, mx=3000, target=19.5, grade="B",
         loc="Korba", dl=7, terms="Advance 30%, rest on delivery", status="CANCELLED", created_days_ago=20),
    dict(key="DM_ACT", buyer=5, crop="Tomato", req=1500, mn=800, mx=2000, target=25.5, grade="A",
         loc="Bilaspur", dl=9, terms="Cash on delivery", status="ACTIVE", created_days_ago=2),
]

# ---------------------------------------------------------------------------
# DEALS -- the connected spine of the dataset. Each one becomes:
#   listing OR lot  ->  buyer offer  ->  negotiation rounds  ->  agreement
#   ->  transaction (+ event timeline)  ->  [transport request]  ->  payment(s)
#   ->  receipt  ->  ratings / QoS records / grievances (where listed).
#
# flow       "listing" (offer on a marketplace listing) or "lot" (offer on a lot,
#            optionally fulfilling a buyer demand).  The API allows exactly one.
# rounds     prices in order; round 1 is the buyer's offer, then they alternate.
#            The last round is the one accepted by the OTHER party.
# mode       BUYER_PICKUP / FARMER_DELIVERY / TO_BE_AGREED
# status     Transaction.status. Everything before it in the lifecycle is
#            reflected in the event timeline.
# pu         days after the offer date that pickup is scheduled.
# tr         transport leg for FARMER_DELIVERY deals:
#              t = transporter index, neg = negotiation pattern (A/B/C),
#              late = hours after scheduled pickup the truck actually left,
#              dlate = delivered after the promised date,
#              fmult = final charge / agreed price
# rec        farmer-recorded buyer outcomes {"pickup": .., "terms": ..}
# rate       (farmer->buyer, buyer->farmer) 1-5 ratings once COMPLETED
# pay        (method, plan) plan: PAID / DUE / FAILED_THEN_PAID / DISPUTED_THEN_PAID
# ---------------------------------------------------------------------------
DEALS = [
    dict(key="D01", flow="listing", farmer=0, buyer=1, crop="Tomato", qty=1500, grade="A", q=89, ask=28.0, floor=23.0,
         rounds=[25.0, 27.5, 26.5], mode="BUYER_PICKUP", status="COMPLETED", days_ago=38, pu=4,
         listing_remaining=700, demand=None, tr=None, rec=dict(pickup="LATE", terms="AS_AGREED"),
         rate=(4.0, 4.5), pay=("UPI", "PAID")),
    dict(key="D02", flow="lot", farmer=3, buyer=4, crop="Tomato", qty=3000, grade="A", q=90, ask=25.0, floor=21.0,
         rounds=[23.0, 25.0, 24.5], mode="FARMER_DELIVERY", status="COMPLETED", days_ago=33, pu=2,
         demand="DM_D02", tr=dict(t=0, neg="A", late=0.3, dlate=False, fmult=1.0),
         rec=dict(terms="AS_AGREED"), rate=(5.0, 5.0), pay=("NEFT", "PAID")),
    dict(key="D03", flow="lot", farmer=4, buyer=6, crop="Soybean", qty=3200, grade="A", q=89, ask=48.0, floor=44.0,
         rounds=[46.0, 47.5], mode="BUYER_PICKUP", status="COMPLETED", days_ago=30, pu=3,
         demand="DM_D03", tr=None, rec=dict(pickup="ON_TIME", terms="AS_AGREED"),
         rate=(4.5, 4.5), pay=("RTGS", "PAID")),
    dict(key="D04", flow="lot", farmer=5, buyer=9, crop="Paddy (Rice)", qty=5000, grade="B", q=80, ask=20.5, floor=18.0,
         rounds=[19.0, 20.5, 20.0], mode="FARMER_DELIVERY", status="COMPLETED", days_ago=27, pu=3,
         demand="DM_D04", tr=dict(t=5, neg="B", late=3.0, dlate=False, fmult=1.03),
         rec=dict(terms="DEVIATED"), rate=(3.5, 4.0), pay=("NEFT", "PAID")),
    dict(key="D05", flow="lot", farmer=8, buyer=2, crop="Groundnut", qty=2200, grade="A", q=88, ask=60.0, floor=55.0,
         rounds=[57.0, 59.0, 58.5], mode="FARMER_DELIVERY", status="COMPLETED", days_ago=24, pu=3,
         demand="DM_D05", tr=dict(t=3, neg="B", late=4.0, dlate=False, fmult=1.12),
         rec=dict(terms="DEVIATED"), rate=(3.5, 4.0), pay=("NEFT", "FAILED_THEN_PAID")),
    dict(key="D06", flow="lot", farmer=2, buyer=8, crop="Chana (Gram)", qty=1800, grade="A", q=86, ask=54.0, floor=49.0,
         rounds=[52.0, 54.0, 53.0], mode="FARMER_DELIVERY", status="COMPLETED", days_ago=21, pu=3,
         demand="DM_D06", tr=dict(t=2, neg="A", late=0.5, dlate=False, fmult=1.09),
         rec=dict(terms="AS_AGREED"), rate=(4.5, 4.5), pay=("RTGS", "PAID")),
    dict(key="D07", flow="lot", farmer=1, buyer=0, crop="Onion", qty=2800, grade="A", q=91, ask=19.0, floor=15.5,
         rounds=[17.5, 19.0, 18.2, 18.5], mode="FARMER_DELIVERY", status="COMPLETED", days_ago=19, pu=2,
         demand="DM_D07", tr=dict(t=7, neg="C", late=0.4, dlate=True, fmult=1.0),
         rec=dict(terms="DEVIATED"), rate=(4.0, 5.0), pay=("NEFT", "DISPUTED_THEN_PAID")),
    dict(key="D08", flow="listing", farmer=9, buyer=5, crop="Tomato", qty=1200, grade="A", q=92, ask=27.0, floor=23.0,
         rounds=[26.5], mode="BUYER_PICKUP", status="COMPLETED", days_ago=16, pu=2,
         listing_remaining=300, demand=None, tr=None, rec=dict(pickup="LATE", terms="AS_AGREED"),
         rate=(4.0, 4.5), pay=("UPI", "PAID")),
    dict(key="D09", flow="listing", farmer=6, buyer=9, crop="Wheat", qty=4000, grade="B", q=78, ask=23.5, floor=21.0,
         rounds=[22.0, 23.5, 23.0], mode="BUYER_PICKUP", status="PAYMENT_RECEIVED", days_ago=12, pu=2,
         listing_remaining=0, demand=None, tr=None, rec=dict(pickup="ON_TIME", terms="DEVIATED"),
         rate=None, pay=("NEFT", "PAID")),
    dict(key="D10", flow="lot", farmer=7, buyer=8, crop="Maize", qty=3000, grade="B", q=76, ask=20.5, floor=18.0,
         rounds=[19.0, 20.0], mode="BUYER_PICKUP", status="DELIVERED", days_ago=8, pu=2,
         demand="DM_D10", tr=None, rec=dict(pickup="ON_TIME", terms="AS_AGREED"),
         rate=None, pay=("UPI", "DUE")),
    dict(key="D11", flow="lot", farmer=4, buyer=2, crop="Soybean", qty=4000, grade="A", q=90, ask=48.0, floor=44.0,
         rounds=[46.5, 47.5], mode="FARMER_DELIVERY", status="IN_TRANSIT", days_ago=4, pu=2, fpo=3,
         demand="DM_D11", tr=dict(t=9, neg="A", late=0.4, dlate=False, fmult=None),
         rec=None, rate=None, pay=None),
    dict(key="D12", flow="lot", farmer=0, buyer=4, crop="Paddy (Rice)", qty=5000, grade="B", q=79, ask=21.0, floor=18.5,
         rounds=[20.0, 21.0, 20.5], mode="FARMER_DELIVERY", status="PICKED_UP", days_ago=3, pu=2,
         demand="DM_D12", tr=dict(t=8, neg="B", late=0.6, dlate=False, fmult=None),
         rec=None, rate=None, pay=None),
    dict(key="D13", flow="lot", farmer=3, buyer=0, crop="Onion", qty=2500, grade="A", q=90, ask=19.0, floor=16.0,
         rounds=[18.0, 18.5], mode="FARMER_DELIVERY", status="LOGISTICS_CONFIRMED", days_ago=3, pu=4,
         demand=None, tr=dict(t=0, neg="A", late=None, dlate=False, fmult=None),
         rec=None, rate=None, pay=None),
    dict(key="D14", flow="listing", farmer=9, buyer=4, crop="Wheat", qty=3500, grade="A", q=85, ask=24.0, floor=21.5,
         rounds=[23.0, 23.5], mode="FARMER_DELIVERY", status="LOGISTICS_PENDING", days_ago=2, pu=5,
         listing_remaining=0, demand=None, tr=dict(t=None, neg=None, late=None, dlate=False, fmult=None),
         rec=None, rate=None, pay=None),
    dict(key="D15", flow="listing", farmer=8, buyer=6, crop="Soybean", qty=2000, grade="A", q=87, ask=47.5, floor=44.0,
         rounds=[46.5], mode="TO_BE_AGREED", status="OFFER_ACCEPTED", days_ago=0, pu=6,
         listing_remaining=1000, demand=None, tr=None, rec=None, rate=None, pay=None),
]

# ---------------------------------------------------------------------------
# Unsold marketplace listings (flow = listing) with live offers.
# offers: (buyer, qty, price, status, message). status: pending / rejected /
# withdrawn. `counter` = a farmer counter-proposal awaiting the buyer.
# ---------------------------------------------------------------------------
EXTRA_LISTINGS = [
    dict(farmer=4, crop="Chana (Gram)", qty=1800, grade="A", q=86, ask=54.0, floor=49.0, status="active",
         avail_days=2, deadline_days=6,
         offers=[(6, 1800, 52.0, "pending", "Can lift within 3 days from Rajnandgaon."),
                 (8, 1000, 51.5, "pending", "Export lot, need A grade only.")]),
    dict(farmer=5, crop="Paddy (Rice)", qty=4500, grade="B", q=78, ask=20.0, floor=18.0, status="active",
         avail_days=3, deadline_days=8,
         offers=[(7, 4500, 18.5, "withdrawn", "Withdrawn - sourced elsewhere."),
                 (9, 3000, 19.5, "pending", "Will send our own truck.")]),
    dict(farmer=6, crop="Wheat", qty=3000, grade="A", q=84, ask=24.0, floor=22.0, status="active",
         avail_days=1, deadline_days=5,
         offers=[(3, 3000, 22.5, "pending", "Mill order, quick payment."),
                 (4, 2000, 23.0, "pending", "Need delivery at Raipur.")]),
    dict(farmer=9, crop="Tomato", qty=900, grade="A", q=90, ask=27.0, floor=23.0, status="active",
         avail_days=1, deadline_days=4,
         offers=[(1, 900, 23.5, "rejected", "Price too low for Grade A."),
                 (5, 900, 25.5, "counter", "Retail chain, daily supply.")]),
    dict(farmer=3, crop="Tomato", qty=1800, grade="A", q=88, ask=25.5, floor=22.0, status="active",
         avail_days=2, deadline_days=5,
         offers=[(4, 1800, 24.0, "pending", "Bulk processing order."),
                 (1, 1000, 24.5, "pending", "Retail, local pickup."),
                 (0, 1000, 22.5, "rejected", "Quantity split not accepted.")]),
    dict(farmer=1, crop="Wheat", qty=3500, grade="A", q=86, ask=24.5, floor=22.0, status="expired",
         avail_days=1, deadline_days=10, offers=[]),
]

# ---------------------------------------------------------------------------
# Unsold lots (flow = lot). offers use the same tuple shape as above.
# fpo = index into POOLS the lot is aggregated under.
# ---------------------------------------------------------------------------
EXTRA_LOTS = [
    dict(key="XL1", farmer=4, crop="Soybean", qty=2500, grade="A", q=88, price=48.0, minp=44.0,
         status="AVAILABLE", harvest_days_ago=4, fpo=3, offers=[]),
    dict(key="XL2", farmer=2, crop="Groundnut", qty=2000, grade="B", q=80, price=58.0, minp=54.0,
         status="UNDER_OFFER", harvest_days_ago=5, fpo=None,
         offers=[(6, 2000, 56.0, "pending", "Oil mill requirement."),
                 (2, 1500, 54.5, "rejected", "Needs advance payment, not acceptable.")]),
    dict(key="XL3", farmer=6, crop="Paddy (Rice)", qty=3000, grade="B", q=79, price=20.0, minp=18.0,
         status="UNDER_OFFER", harvest_days_ago=6, fpo=None,
         offers=[(9, 3000, 19.5, "pending", "Our truck, pickup Thursday."),
                 (3, 2000, 19.0, "pending", "Part load, cash.")]),
    dict(key="XL4", farmer=1, crop="Maize", qty=2800, grade="B", q=77, price=20.0, minp=17.5,
         status="AVAILABLE", harvest_days_ago=7, fpo=4, offers=[]),
    dict(key="XL5", farmer=7, crop="Chana (Gram)", qty=1200, grade="A", q=85, price=54.0, minp=50.0,
         status="DRAFT", harvest_days_ago=2, fpo=None, offers=[]),
    dict(key="XL6", farmer=5, crop="Maize", qty=1500, grade="C", q=58, price=17.0, minp=15.0,
         status="CANCELLED", harvest_days_ago=12, fpo=None, offers=[],
         note="Cancelled - moisture too high after rain, re-drying before relisting."),
    dict(key="XL7", farmer=9, crop="Onion", qty=1800, grade="A", q=89, price=19.0, minp=16.0,
         status="AVAILABLE", harvest_days_ago=3, fpo=1, offers=[]),
    dict(key="XL8", farmer=0, crop="Soybean", qty=3000, grade="A", q=91, price=48.5, minp=45.0,
         status="UNDER_OFFER", harvest_days_ago=4, fpo=3,
         offers=[(6, 3000, 47.0, "pending", "Matches our standing demand."),
                 (2, 2000, 46.5, "pending", "Export grade needed.")]),
]

# ---------------------------------------------------------------------------
# Group-selling pools. members: (farmer index, quantity kg).
# Existing pool in seed_data.py (Chana / Durg Farmer Collective) is topped up
# with POOL_EXISTING_EXTRA_MEMBERS. Pool index is used by lots / shared trips.
# ---------------------------------------------------------------------------
POOLS = [
    dict(crop="Tomato", fpo="Bilaspur Kisan Producer Company", status="open",
         members=[(0, 800), (3, 1200), (9, 600)]),                                    # 0
    dict(crop="Onion", fpo="Bilaspur Kisan Producer Company", status="open",
         members=[(3, 900), (9, 700), (1, 1100)]),                                     # 1
    dict(crop="Paddy (Rice)", fpo="Mahanadi Paddy Growers Collective", status="open",
         members=[(5, 2500), (0, 1800), (6, 2000), (8, 1500)]),                        # 2
    dict(crop="Soybean", fpo="Rajnandgaon Producer Company", status="matched",
         members=[(4, 2500), (8, 1200), (0, 1500)]),                                   # 3
    dict(crop="Maize", fpo="Surguja Maize Growers Group", status="open",
         members=[(7, 1500), (2, 1000), (1, 2800), (5, 900)]),                         # 4
    dict(crop="Wheat", fpo="Korba Farmer Collective", status="closed",
         members=[(6, 2500), (9, 1200), (4, 1000)]),                                   # 5
    dict(crop="Groundnut", fpo="Bastar FPO", status="open",
         members=[(8, 1400), (2, 900), (6, 700)]),                                     # 6
    dict(crop="Tomato", fpo="Raipur Region Tomato Collective", status="closed",
         members=[(0, 1500), (3, 1000)]),                                              # 7
    dict(crop="Onion", fpo="Raigarh Onion Growers", status="matched",
         members=[(1, 1600), (3, 800)]),                                               # 8
    dict(crop="Wheat", fpo="Rajnandgaon Producer Company", status="open",
         members=[(4, 1800), (1, 1200)]),                                              # 9
]
POOL_EXISTING_EXTRA_MEMBERS = [(4, 900), (7, 700)]   # joins the Chana / Durg Farmer Collective pool

# Shared FarmPool trips (shared_transport=True, status DELIVERED) with reviews.
# pool = index into POOLS; reviewers are pool members.
SHARED_TRIPS = [
    dict(pool=0, t=0, pickup="Bilaspur", dest="Raipur", days_ago=26, vehicle="Eicher 14ft Truck",
         reviews=[(0, 5.0, 4.5), (3, 4.5, 4.5), (9, 4.0, 4.0)]),                       # (farmer, transporter rating, journey rating)
    dict(pool=4, t=6, pickup="Ambikapur", dest="Raipur", days_ago=18, vehicle="Eicher 14ft Truck",
         reviews=[(7, 4.5, 4.0), (2, 4.0, 4.0), (1, 4.5, 4.5), (5, 3.5, 3.5)]),
    dict(pool=6, t=3, pickup="Jagdalpur", dest="Raipur", days_ago=11, vehicle="Tata 407 Truck",
         reviews=[(8, 4.0, 4.5), (2, 4.5, 4.0), (6, 3.5, 4.0)]),
]

# Transport requests that are not tied to a deal.
# kind: CANCELLED_BY_FARMER / CANCELLED_BY_TRANSPORTER / NEGOTIATING / OPEN
EXTRA_TRANSPORT = [
    dict(kind="CANCELLED_BY_FARMER", farmer=5, t=5, pickup="Mahasamund", dest="Raipur", crop="Paddy (Rice)",
         qty=2500, days_ago=15, pu=2, note="Buyer postponed; farmer cancelled before pickup."),
    dict(kind="CANCELLED_BY_TRANSPORTER", farmer=3, t=8, pickup="Bilaspur", dest="Raipur", crop="Tomato",
         qty=1500, days_ago=13, pu=2, note="Vehicle breakdown; transporter cancelled the evening before."),
    dict(kind="NEGOTIATING", farmer=1, t=7, pickup="Raigarh", dest="Raipur", crop="Wheat",
         qty=3000, days_ago=2, pu=5, note=None),
    dict(kind="OPEN", farmer=6, t=None, pickup="Korba", dest="Raipur", crop="Paddy (Rice)",
         qty=3500, days_ago=1, pu=6, note=None),
]

# ---------------------------------------------------------------------------
# Storage bookings: (farmer, facility name, lot ref, qty, start offset days
# from today (negative = past), nights, status). lot ref is a DEAL key
# ("D07") or an EXTRA_LOTS key ("XL1").
# ---------------------------------------------------------------------------
STORAGE_BOOKINGS = [
    (1, "Raigarh Grain Godown (Demo)", "D07", 1500, -26, 4, "COMPLETED"),
    (3, "Raipur Cold Storage Pvt. Ltd. (Demo)", "D13", 1200, -4, 7, "ACTIVE"),
    (8, "Jagdalpur Bastar FPO Storage (Demo)", "D05", 1000, -31, 5, "COMPLETED"),
    (2, "Durg FPO Collective Storage (Demo)", "D06", 800, -27, 4, "COMPLETED"),
    (0, "Bilaspur Agri Warehouse (Demo)", "D12", 2000, -9, 6, "COMPLETED"),
    (4, "Rajnandgaon Producer Company Store (Demo)", "D11", 1500, -11, 6, "COMPLETED"),
    (4, "Rajnandgaon Producer Company Store (Demo)", "XL1", 2500, -3, 14, "ACTIVE"),
    (6, "Korba Farmers' Warehouse (Demo)", "XL3", 2000, 1, 10, "CONFIRMED"),
    (1, "Raigarh Grain Godown (Demo)", "XL4", 1800, 3, 12, "REQUESTED"),
    (9, "Bilha Village Grain Store (Demo)", "XL7", 1200, -2, 9, "ACTIVE"),
    (2, "Durg FPO Collective Storage (Demo)", "XL2", 1000, 2, 8, "CONFIRMED"),
    (5, "Mahasamund District Warehouse (Demo)", "XL6", 1500, -10, 5, "CANCELLED"),
    (0, "Bilaspur Agri Warehouse (Demo)", "XL8", 2200, -2, 15, "ACTIVE"),
]

# ---------------------------------------------------------------------------
# Grievances: (deal key, raised_by, category, status, priority, description, resolution)
# against_user is derived from the deal (the other party). category follows
# grievances.VALID_CATEGORIES.
# ---------------------------------------------------------------------------
GRIEVANCES = [
    ("D07", "farmer", "PRICE", "RESOLVED", "MEDIUM", 12,
     "Buyer reduced the price by Rs 0.50/kg at weighing without prior notice.",
     "Both parties agreed to the negotiated Rs 18.5/kg; buyer paid the difference."),
    ("D05", "farmer", "PAYMENT", "RESOLVED", "HIGH", 20,
     "First payment attempt failed and buyer did not retry for 3 days.",
     "Buyer re-initiated via NEFT and the payment was confirmed."),
    ("D05", "buyer", "QUALITY", "UNDER_REVIEW", "HIGH", 18,
     "Moisture on arrival was higher than the graded report indicated.", None),
    ("D09", "farmer", "QUALITY", "WAITING_FOR_EVIDENCE", "MEDIUM", 7,
     "Buyer claims some bags were below the agreed grade; farmer disputes this.", None),
    ("D10", "farmer", "PAYMENT", "OPEN", "HIGH", 2,
     "Payment was due two days after delivery and has not been received.", None),
    ("D02", "buyer", "DELIVERY", "CLOSED", "LOW", 28,
     "Truck arrived 3 hours after the slot. No stock damage; closing as noted.", "Noted on transporter record; no action required."),
    ("D04", "farmer", "DELIVERY", "RESOLVED", "MEDIUM", 22,
     "Unloading at the buyer's yard was delayed by a full day.",
     "Buyer agreed to cover the extra waiting charge."),
    ("D08", "buyer", "QUANTITY", "REJECTED", "LOW", 14,
     "Claimed a 40 kg shortfall against the agreed 1200 kg.",
     "Weighbridge slip shows 1200 kg loaded; claim rejected."),
    ("D11", "farmer", "LOGISTICS", "OPEN", "MEDIUM", 1,
     "Truck has been halted at a checkpost for four hours.", None),
    ("D12", "farmer", "BUYER", "UNDER_REVIEW", "LOW", 1,
     "Buyer asked to change the bagging specification on the day of pickup.", None),
    ("D13", "buyer", "OTHER", "CLOSED", "LOW", 2,
     "Asked for the pickup slot to be moved by one day.", "Slot moved by agreement; closing."),
    ("D06", "farmer", "PRICE", "RESOLVED", "MEDIUM", 16,
     "Buyer's receiving note quoted Rs 52/kg instead of the agreed Rs 53/kg.",
     "Receiving note corrected to Rs 53/kg."),
]

# ---------------------------------------------------------------------------
# Reputation disputes ("right of reply"). kind record -> a PerformanceRecord
# (deal, metric), kind trip -> that deal's / shared trip's TransportRequest.
# ---------------------------------------------------------------------------
DISPUTES = [
    dict(kind="record", deal="D08", metric="BUYER_PICKUP", status="OPEN", days_ago=6,
         reason="Our truck reached the farm gate at the agreed time; the farmer's staff were not ready to load.", note=None),
    dict(kind="record", deal="D05", metric="BUYER_TERMS", status="UNDER_REVIEW", days_ago=9,
         reason="Grade was revised at weighing in the presence of the farmer's representative.",
         note="Requested the weighing slip and grading photos from both sides."),
    dict(kind="record", deal="D09", metric="BUYER_TERMS", status="UPHELD", days_ago=18,
         reason="Moisture reading at our depot exceeded the agreed limit; lab sheet attached.",
         note="Lab sheet verified. The record is excluded from the buyer's rates."),
    dict(kind="record", deal="D07", metric="BUYER_TERMS", status="REJECTED", days_ago=15,
         reason="The price change was agreed on a call with the farmer's representative.",
         note="No written agreement found; the original terms stand and the record counts."),
    dict(kind="record", deal="D01", metric="BUYER_PICKUP", status="REJECTED", days_ago=30,
         reason="Our vehicle was delayed by a road closure on the highway.",
         note="No closure notice found for the date; the record counts."),
    dict(kind="record", deal="D04", metric="BUYER_TERMS", status="OPEN", days_ago=4,
         reason="Quantity delivered was 4,950 kg, not 5,000 kg, so we adjusted payment accordingly.", note=None),
    dict(kind="trip", deal="D05", status="UNDER_REVIEW", days_ago=10,
         reason="The extra charge covered a state border tax that the farmer agreed to verbally.",
         note="Asked the transporter for the tax receipt."),
    dict(kind="trip", deal="D07", status="UPHELD", days_ago=14,
         reason="Delivery was delayed by a flooded road; the farmer rescheduled by phone.",
         note="Weather advisory verified; the trip is excluded from this agency's delivery rate."),
    dict(kind="trip", shared=0, status="REJECTED", days_ago=22,
         reason="Pickup was late because members were still loading.",
         note="Loading log shows the truck waited only 15 minutes; the record counts."),
    dict(kind="trip", deal="D06", status="OPEN", days_ago=3,
         reason="The higher final charge includes a night-halt fee agreed with the farmer.", note=None),
    dict(kind="trip", deal="D04", status="REJECTED", days_ago=19,
         reason="Pickup was late because the farmer's produce was not ready.",
         note="Pickup readiness is recorded as ready on arrival; the record counts."),
]

# ---------------------------------------------------------------------------
# Standing (non-deal) notifications. recipient: ("farmer"|"buyer", index).
# ---------------------------------------------------------------------------
NOTIFICATIONS = [
    ("farmer", 0, "price_drop", "warning", "Price drop alert", "Soybean modal prices in Bilaspur slipped this week; compare Raipur and Durg before accepting offers.", 1, False),
    ("farmer", 1, "harvest_reminder", "info", "Harvest reminder", "Your Wheat listing expired without offers. Relist or update the price to reach buyers again.", 12, True),
    ("farmer", 2, "high_demand", "success", "High demand nearby", "Two verified buyers are looking for Groundnut within 150 km of Durg.", 2, False),
    ("farmer", 3, "opportunity", "success", "Better price in another market", "Tomato nets more in Raipur than Bilaspur after transport this week.", 1, False),
    ("farmer", 4, "new_lot", "success", "New demand matches your lot", "FarmLink Agro posted a Soybean demand that matches your available lot.", 3, True),
    ("farmer", 5, "price_drop", "warning", "Price drop alert", "Paddy arrivals at Mahasamund are up 18%, which may soften prices.", 4, True),
    ("farmer", 6, "opportunity", "success", "Group selling available", "Join the Korba Farmer Collective Wheat pool to unlock a bulk buyer.", 6, False),
    ("farmer", 7, "harvest_reminder", "info", "Harvest reminder", "Update the available quantity on your Maize lot before the bidding window closes.", 2, False),
    ("farmer", 8, "high_demand", "success", "High demand nearby", "AgriExport India is buying Groundnut and Soybean from Bastar this fortnight.", 5, True),
    ("farmer", 9, "opportunity", "success", "Storage tip", "Cold storage in Raipur has spare capacity for Onion at a lower daily rate this week.", 1, False),
    ("buyer", 0, "new_lot", "success", "New lot available", "Two Grade A Onion lots were listed near Bilaspur.", 2, False),
    ("buyer", 2, "offer_update", "info", "Offer update", "A farmer countered your Groundnut offer. Review the new terms.", 1, False),
    ("buyer", 4, "high_demand", "success", "Matching supply", "Three farmers have Paddy (Rice) lots that match your open demand.", 2, True),
    ("buyer", 5, "verification_update", "success", "Verification complete", "Your documents were verified. Your offers now show a verified badge.", 22, True),
    ("buyer", 3, "verification_update", "warning", "Account suspended", "Your verification was suspended following unresolved payment complaints. Contact support to review.", 9, False),
    ("buyer", 7, "verification_update", "warning", "Verification rejected", "Your GST certificate could not be read. Please upload a clear copy and resubmit.", 11, False),
    ("buyer", 10, "verification_update", "info", "Documents under review", "Your documents were received and are being reviewed.", 2, False),
    ("buyer", 12, "verification_update", "info", "Documents under review", "Your export documents were received and are being reviewed.", 4, False),
]
