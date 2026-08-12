# STATE.md — Agency OS (SBA Lead-to-Meeting Pipeline)

> Purpose: one-page state so we never have to rescan the repo. Updated whenever
> the autopilot/agent status changes. Branch: `feat/sba-lead-to-meeting-pipeline`.

**Last updated:** 2026-08-12 10:40 IST (05:10 UTC)

---

## STORE — FEATURES DONE + GST/HSN REMOVED + SECURITY HARDENED (05:10 UTC)

- **User asked:** baki store kaam khatam karo, GST/HSN poori tarah hatao,
  colours/design aur achha karo.
- **GST/HSN 100% removed (codebase-wide verified):** backend (routes/store.py +
  store_store.py) + frontend `page.js` + StoreTab — zero `gst`/`hsn`/`GSTIN`
  matches left (only unrelated `fonts.gstatic.com`). Settings editor ab
  **Primary Color** field hai (GSTIN ki jagah).
- **New storefront features (frontend `0964f2e`, Vercel prod LIVE — verified):**
  1. **Service images** — upload/URL field in service editor + image cards.
  2. **Coupons (owner Coupons tab):** create/edit/delete/toggle-active, percent
     ya flat, min order, max uses, expiry. **Checkout pe coupon apply box** —
     validate API se discount milta hai, subtotal/discount/total rows, order
     pe coupon_code bhejta hai.
  3. **Reviews (owner Reviews tab + storefront):** customer product pe rating
     (1-5) + comment deta hai (pending), owner approve/unpublish/delete karta
     hai. Product cards pe star rating + count (approved stats only).
  4. **Hero banners (settings.banners):** upload/add-link/remove, storefront
     pe auto-rotating carousel (5s, arrows + dots).
  5. **WhatsApp:** order success pe "WhatsApp pe Order Confirm karo" deep link
     (owner ke number pe), + floating chat button visitors ke liye
     (settings.whatsapp).
  6. **Design polish:** hero gradient blobs, backdrop-blur chips, `--accent`
     CSS var ab store ke colour se sync (checkbox accents), banner carousel.
- **Security hardening (backend `59b3adb`, EC2 LIVE):**
  - `GET /reviews` bina token → sirf approved reviews (pending kabhi leak nahi).
  - `PATCH/DELETE /reviews` + coupons POST/PATCH/DELETE + `GET /coupons` →
    ab store owner token zaroori (pehle bina auth ke koi bhi pending review
    approve/delete kar sakta tha, coupon codes bhi padh/change sakta tha).
  - Public storefront view (`/api/store/public`) pehle se approved-only
    reviews + stats deta hai.
- **WhatsApp path live-verified:** settings me whatsapp number temporary set
  karke order banaya → response me `waLink=https://wa.me/919876543210?text=...`
  correct aaya, phir settings revert. Store owner ko **Settings tab me apna
  WhatsApp number daalna hai** taaki success screen ka confirm button + floating
  chat button dikhe (abhi `settings.whatsapp=''` hai isliye hidden).
- **Tests:** 58/58 pass (`admin/tests/test_store.py`). Frontend build 41/41.
  Live chunk (`page-48896c53…`) me Coupon/Review/whatsapp/banner sab present.
- **Test orders in live DB (E2E se bache):** `ORD-10979596` (coupon wala,
  total ₹1169.1) + `ORD-11068160` (WhatsApp link test, ₹1299). Owner dashboard
  me ye dikhenge — delete kar sakte hain ya chhod dein.
- **Commits:** frontend submodule `0964f2e` (pushed → Vercel), parent
  `59b3adb` (routes security + submodule pointer). Backend deploy via
  `python deploy/deploy_sba.py` (100 files, py_compile OK, service active).
- **Live portal:** `https://agency-frontend-seven.vercel.app/store/agency`
  (login `client@tagsagency.com` / `Client@2026`).

---

## STORE — CLIENT PORTAL: 17 FEATURES + TABS + IMAGE UPLOAD LIVE (19:20 UTC)

- **User approved all 17 store features** ("ya sab add kar") — sab ek hi jagah
  (client dashboard), **tabs** taaki scroll na karna pade.
- **Frontend `src/app/store/[slug]/page.js` (3 commits, Vercel prod live):**
  1. `88b62bb` store-features-17-all — settings editor (store name/tagline/logo/
     GSTIN/color/contact/WhatsApp/delivery charge/free-delivery min/payment
     toggles), order detail modal (customer/dispatch/items w/ HSN/total/status
     buttons), label + invoice print, CSV export, bulk dispatch bar
     (select → carrier/tracking/note → ship), GST%+HSN fields, Low stock badge
     (≤5), 14-day sales graph, payment breakdown, customer list.
  2. `104beb8` store-dashboard-tabs-nav — sticky nav with 5 tabs:
     **Dashboard** (stats/graph/publish), **Orders** (badge=pendingDispatch),
     **Products** (badge=lowStock), **Services**, **Settings** (gated editor).
     Low-stock "Update Stock" jumps to Products tab.
  3. `b37650e` store-image-upload-logo-product — **Upload button** (logo +
     product image): file → resize (max 900px) → compressed JPEG data URL →
     seedha settings/product me save (no server storage, backend untouched).
     Link paste field ab optional.
- **Backend `admin/store/store_store.py` (parent `7e986ed`, EC2 live):**
  ORDER_STATUSES + labels me `returned`/`refunded` added (tests 39 passed);
  settings fields (GSTIN, HSN, logo, delivery, payments) already present.
  Live verified: GET/PATCH settings round-trip (whatsapp, delivery_charge,
  free_delivery_min, gstin, payments) → LOGIN_OK / PATCH_OK / REVERT_OK.
- **Public checkout reverted clean:** leftover `_nextjs_store_shop` diff
  (unwanted public selling site) removed via `git checkout --` from
  `admin/tools/website_tools.py`. Store = client portal (login), NOT public
  selling site.
- **Parent repo commits:** `7e986ed` (backend+submodule), `866bc76`
  (submodule pointer b37650e). Branch `feat/sba-lead-to-meeting-pipeline`.
- **Live portal:** `https://agency-frontend-seven.vercel.app/store/agency`
  (login `client@tagsagency.com` / `Client@2026`). Build 41/41 static pages.
- **PENDING (user asked, not yet done):** service image, coupon/discount codes,
  product reviews, offers/banners (homepage), WhatsApp order notification.
  Track Order (order#+email) pehle se hai (`GET /api/store/track`).

---

## STORE — CART CHECKOUT LIVE + PERSISTENCE VERIFIED (08:10 UTC)

- **Feature complete + deployed:** multi-item cart checkout. Backend
  `45accb6` (admin/api/routes/store.py, admin/store/store_store.py,
  admin/tests/test_store.py; 28/28 tests). Frontend `a552d32` (cart drawer +
  payment method + product search in `src/app/store/[slug]/page.js` +
  `admin/agents/website/StoreTab.jsx`; build 41/41). Submodule pointer
  `0ec50fd`. Backend deployed via `deploy/deploy_sba.py` (97 files, autopilot
  active). Vercel deploy **READY** (production, 30 min after push).
- **DB persistence contradiction RESOLVED:** backend returned 9 products but
  the PB collection list showed none — that was PB **pagination truncation**
  (`/api/collections` default perPage=30, 39 collections exist). With
  `perPage=200`: `ws_agency__store_products` (9), `ws_agency__store_orders` (8),
  `ws_agency__store_settings` (1), `ws_agency__store_accounts` (1) all present.
  Data lives in **PocketBase** (EC2 8090) via the pb-supabase-gateway (8095),
  NOT in Supabase Postgres. Backend `.env`: `SUPABASE_URL=http://127.0.0.1:8095`
  (gateway) — PocketBase is the real store.
- **Live E2E verified (via Vercel proxy → EC2 → PB):**
  1. `GET /api/store/public?workspace=agency` → 9 active products.
  2. `POST /api/store/orders` (2 items: Premium Cotton Kurta ₹1299 + Running
     Sports Shoes ₹1599, UPI, customer Indore MP 452001) → 200,
     **ORD-35314411**, total ₹2898, status placed, city/state/pincode
     auto-parsed from address.
  3. PB direct check: orders 8→9, new row present with full items[],
     payment_method=UPI, source=live-e2e-test.
  4. **Stock decremented:** Kurta 17→16, Shoes 13→12.
  5. Sales stats (backend + via Vercel proxy, identical): 9 orders, ₹19,184
     revenue, 16 units, status breakdown placed 6/shipped 1/delivered 2,
     cities include Indore + states Madhya Pradesh — **storefront dashboard
     reflects the new order.**
- **Live storefront:** `https://agency-frontend-seven.vercel.app/store/agency`
  (proxy `src/app/api/[...slug]/route.js` → `BACKEND_API_URL` =
  18.213.66.136:8000, default in code).

---

## STORE — OWNER DASHBOARD UX FIXES (18:00 UTC)

- **User feedback:** "frontend mein product add ka option nahi, order track nahi,
  order labels/dispatch nahi dikh raha". Root cause: wo bina login ke dekh rahe
  the — Add Product + Orders sirf login ke baad dikhte hain (by design).
- **Verified live (headless render + login):** visitor view mein Track Order
  button tha; login (`client@tagsagency.com` / `Client@2026`) ke baad Add
  Product, Orders (Kaha se: Pune, PIN 411001, Source: Instagram, Shipped +
  Delhivery DL-778899) sab dikhta hai.
- **Fixes deployed (`d1a17a4`):**
  1. **Track Order button ab hamesha header mein** (visitor + owner dono ko) —
     pehle sirf `!account` (visitor) ko dikhta tha, owner login ke baad gayab.
  2. **Visitor hint:** products section ke upar "Store owner? Login karke
     products add/edit kar sakte ho, orders dekho (kaha se aaya, status), aur
     dispatch/tracking update karo" — taaki bina login wala samjhe ki kya
     login ke baad milta hai.
- **Vercel deploy verified live:** storefront chunk mein "Track Order",
  "Store owner?", "Login karke products add/edit", "Add Product", "Kaha se
  (Location)", "Status / Dispatch", "Ship it", "Track Order Status", "naya
  order aaya hai" — sab present.
- Build 41/41 pass. Playwright dev dependency remove (`dca8554`).

---

## STORE — CLIENT ACCOUNT + FULL LOOP VERIFIED (17:25 UTC)

- **Client account LIVE:** `client@tagsagency.com` / `Client@2026` (name: TAGS
  Store Owner) — created via `POST /api/store/accounts` for ws_agency/Client.
  Client login karta hai `/store/agency` → "Store Owner Login".
- **Full client loop verified live end-to-end:**
  1. Client login → token ✅
  2. Client apna product add (Premium Cotton Kurta ₹1299, via
     `POST /api/store/products` with X-Store-Token) ✅
  3. Customer order (ORD-82646280, ₹2598, Vikram Singh, Pune/Maharashtra,
     source Instagram) ✅
  4. Order client dashboard mein dikha (7 orders, naya order location+source
     ke saath) ✅
  5. Client dispatch (shipped, Delhivery, DL-778899, shipped_at stamped) ✅
  6. Public track shows shipped + tracking ✅
- Live store ab: 8 products (7 demo + Premium Cotton Kurta), 7 orders
  (ORD-82646280 = naya, rest previous E2E), sales ~₹13,989.
- Client khud products add/edit/delete karega apne dashboard se; demo
  products ko delete/edit kar sakta hai. Agency StoreTab mein bhi account
  create kar sakta hai (Email + Password → "Create Client Account").

---

## STORE ORDER FLOW — CLIENT VISIBILITY + DISPATCH (17:15 UTC)

- **Client ke paas ab ek jagah hai jahan sab dikhta hai:** client store login
  (`/store/agency` → "Store Owner Login") ke baad dashboard mein:
  - **Kitne orders** (header count + status filter tabs All/placed/processing/
    shipped/delivered/cancelled with per-status counts)
  - **Kaha se aaya** (Location column: city, state, PIN + Source column:
    Direct/Instagram/Google/WhatsApp via `detectSource()`)
  - **Dispatch status** (Status/Dispatch column — status dropdown, carrier +
    tracking + note, "Ship it" form jab shipped select karo)
  - **Naya order aaye toh turant dikhe** (red "X naya" badge + green banner +
    NEW chip on fresh rows, 30s polling, localStorage `last_seen` per store)
  - **Track Order button** (header) + checkout success pe "Track Order Status"
    — order# + email se koi bhi status timeline dekh sakta hai
- **Backend (deployed `d46fe86` + fix `e780305`):** `parse_location()`
  (city/state/pincode extraction), `source` on place_order, `find_order_by_number`
  + `track_order` (public, PII-safe summary), `update_order_status` now stores
  tracking_number/carrier/dispatch_note + `shipped_at` stamp, `sales_stats`
  includes cities/states/sources breakdown. `GET /api/store/track` public.
- **Dispatch-info preserve fix (`e780305`):** plain status updates (e.g.
  shipped→delivered without re-sending dispatch fields) NO LONGER wipe
  tracking/carrier. Verified live: ship w/ DTDC + tracking, then delivered →
  tracking intact in list + track endpoint.
- **Admin StoreTab (`b2cef0f`) complete:** Kaha se + Source + Status/Dispatch
  columns, new-order badge + 30s polling, dispatch form, "Client ko kya milega"
  box updated. Build 41/41, pushed to master → Vercel deploy verified live
  (literal strings present in deployed chunks for both `/admin/agents/website`
  and `/store/agency`).
- **Tests: 25/25 green** (added preserve test). Live E2E verified:
  track match/mismatch (404), dispatch PATCH 200 + shipped_at, invalid status
  400, status-only PATCH keeps tracking.
- **Live orders:** 6 orders (ORD-76731817 E2E Test Buyer shipped→delivered w/
  DTDC D123456789IN as demo dispatch, others placed). Sales ₹11,391.

---

## STORE ORDER FLOW — SHOPIFY-LIKE (15:02 UTC)

- **`fd83a12` + frontend `347cfa6` deployed:** order flow upgraded from
  "name+email order" to a real Shopify-like experience.
- **Checkout now collects phone + address** (backend already stored them via
  `customer_phone` / `customer_address`; frontend checkout modal now has the
  fields).
- **Order confirmation shows order number** (`ORD-xxxx`) + total on success.
- **Owner dashboard gets an Orders list** (after store login): order number,
  customer + phone/address, items, total, status badge, placed date; status
  filter tabs (All/placed/processing/shipped/delivered/cancelled) + inline
  status dropdown.
- **Admin StoreTab gets an Orders table** too (agency sees all client orders,
  can update status).
- **Backend:** `PATCH /api/store/orders/{oid}` (status update, validated
  against lifecycle), `GET /api/store/orders` now optional-auth (owner or
  agency), `list_orders` limit 200. New `get_order` + `update_order_status`.
- **Email notifications (best-effort):** `POST /api/store/orders` sends a
  confirmation email to the customer + a new-order alert to the owner
  (`settings.contact_email`). Failure never blocks checkout.
- **Tests:** 14/14 green (5 new order/status tests). Live EC2 verified:
  `PATCH /orders/{oid}` → 200 processing, invalid status → 400.
- **Live storefront:** `https://agency-frontend-seven.vercel.app/store/agency`
  (8 products, TAGS Store, ₹ currency, color #7C3AED).
- **Vercel deploy verified 15:38 UTC:** `app/store/[slug]` chunk contains the
  new checkout/orders code (`customer_phone`, `customer_address`,
  `order_number`, status tabs processing/shipped/delivered/cancelled).
- **Live E2E verified 15:45 UTC:** placed real order `ORD-76731817` (Running
  Sports Shoes, ₹1599) with phone `+919876543210` + Bengaluru address → 200,
  persisted in `GET /orders`, status cycle placed→processing→shipped→placed
  all 200, invalid status → 400. Sales now real: **₹11,391 across 6 orders**
  (source=orders).
- **6 orders live** (5 previous test buyers + E2E Test Buyer).

---

## STORE SYSTEM LIVE ON PRODUCTION (13:58 UTC)

- **Backend store routes deployed to EC2 (commit `c23cedf`):** `admin/store/`
  (`store_store.py`, `store_auth.py`, `__init__.py`) + `admin/api/routes/store.py`
  were MISSING from the deploy bundle (only `admin/agency/sba_store.py` was
  included), so `/api/store/*` 404'd on EC2 while the frontend expected them.
  Added 4 files to `deploy/deploy_sba.py` FILES list, deployed via
  `python deploy/deploy_sba.py` — 97 files, py_compile OK, backend restarted,
  DEPLOY OK (exit 0).
- **Verified live on EC2 backend :8000:** `/api/store/public?workspace=agency`,
  `/api/store/products`, `/api/store/settings` all 200.
- **Frontend redeployed to Vercel (`agency-frontend-seven.vercel.app`, commit
  `0792b05`):** build 41/41 pages, `/store/[slug]` route present. StoreTab live
  (Revenue/Orders/Units/Top Product cards) + public storefront page.
- **Public storefront:** `https://agency-frontend-seven.vercel.app/store/agency`
  (renders "My Store", 0 products, 0 orders, ₹0 revenue — no products in live
  agency workspace yet; local test products/orders were in local dev PB only).
- **Admin Store tab:** `/admin/agents/website` → Store tab → shows Client Store
  link, Publish, Products management.
- Note: SSH hangs in cmd.exe wrapper; use python subprocess ssh (works fine).
  Store deps (`website_supabase.py`, `workspace_provision.py`,
  `website_tools.py`) already present on EC2.

---

## AGENTS REPAIRED + FULL MEMORY STACK (19:30 UTC)

- **Root cause:** `agent_persistence.py` (SupabaseSaver) imported
  `empty_checkpoint_id` / `uuid_type` from `langgraph.checkpoint.base`, both
  removed in langgraph-checkpoint 4.x (installed: langgraph 1.2.9). Every
  LangGraph agent (seo, ads, analytics, social, website, memory) crashed with
  ImportError -> "temporarily unavailable" on chat. `content-creator` worked
  only because it didn't hit the shared checkpointer.
- **Fix (commit `30a72b1`, deployed via scp + sba.service restart):**
  1. `put()` falls back to `str(uuid.uuid4())` checkpoint ids when
     `uuid_type` is unavailable, and `""` for parent when no parent exists.
  2. `list`/`alist` accept langgraph v4's `filter` kwarg.
  3. Pending writes are JSON-sanitized (`deque`/`tuple` -> lists) before
     storage; reads normalize 2-tuples to PendingWrite `(task_id, channel,
     value)`.
  4. Backend pytest `test_agent_persistence.py` 12/12 green; EC2 end-to-end
     graph test PASS (checkpoint resumes across runs, memory save/get OK).
- **PB collections created (all agent tables now exist per workspace):**
  `ws_agency__agent_messages`, `ws_agency__agent_data`,
  `ws_agency__agent_checkpoint_writes` (cloned schema/rules from
  `ws_agency__agent_checkpoints`) + same 3 for `ws_agency_workspace__`.
  Previously only `agent_memory` + `agent_checkpoints` existed.
- **Verified live (backend :8000, all 7 agents):** content-creator, seo-engine,
  ads-runner, analytics-bot, social-manager, website-builder, memory-agent all
  reply. `/api/agents` lists exactly 7. All 11 SBA-page endpoints return 200
  through the Vercel proxy (`agency-frontend-seven.vercel.app`). Frontend
  `npm run build` passes (41/41 pages). Note: gateway :8095 only serves
  `/rest/v1/*` + `/api/health`; `/api/agents` etc. live on backend :8000.
- Remaining minor: `/api/sba/agents` + `/api/sba/platforms` are 404 (no such
  routes; the SBA page doesn't call them) — harmless.

---



## PocketBase Supabase Replacement — PRODUCTION GREEN + PAGINATION FIXED (16:20 UTC)

- **Why:** EC2 (2GB RAM) chokes on Supabase (13 containers, ~290MB RAM,
  ~11GB disk). User chose **PocketBase** as lightweight open-source replacement.
- **PocketBase v0.39.10** running on EC2 at `127.0.0.1:8090` (systemd
  `pocketbase.service`, enabled for reboot, localhost-bound), data dir
  `/home/ubuntu/pocketbase/pb_data`. Admin:
  `admin@tagsagency.local` / `pb-admin-2026-x9`.
- **`deploy/pb_gateway.py`** (FastAPI, **port 8095**, systemd `sba-gateway.service`):
  Supabase-compat gateway. Backend needs ZERO code changes: `/rest/v1/{table}` +
  `apikey`/`Authorization` headers + `Content-Profile` → `{profile}__{table}`
  collections + PostgREST operators (eq/neq/gt/gte/lt/lte/ilike/like/is/in) +
  order/limit + upsert (`on_conflict` + merge-duplicates) + auto-creates/extends
  collections. **Legacy Supabase id remap:** non-PocketBase `id` values (UUID /
  int) are moved to `legacy_id` so PocketBase generates its own ≤15-char id.
  **Pagination fixed:** `page` query param is now honored (was always 1, which
  broke dedup/idempotent imports and backend pagination).
- **PAGINATION v2 (16:01 UTC) — limit semantics fixed:** PostgREST returns ALL
  rows when no `limit` param is given; the gateway defaulted to 50 (cap 200).
  Backend `load_leads` sends `/rest/v1/leads?select=*&order=created_at.asc`
  with NO limit, so autopilot only ever saw 50 leads (`no_email: 36` per pass
  instead of ~636). **Fix:** `_build_limit` — no `limit` → page through ALL
  PocketBase pages (perPage 200), `limit=N` → up to N rows; `_find_by_filter`
  (PATCH/DELETE targets) also pages now. **Verified live:** gateway returns
  785 rows; pass 16:17 `no_email: 636, deferred: 21, invalid: 5, errors 0`
  (matches Supabase-era pool). Deploy note: service imports
  `/home/ubuntu/sba-backend/pb_gateway.py` (root), NOT `deploy/pb_gateway.py`.
- **INT-PHONE BUG found + fixed (16:50 UTC) — CRITICAL:** PB `json` field type
  normalizes digit-only strings to int (`"3464049915"` → `3464049915`). 489 of
  814 imported leads had int phones at rest (export had all 783 as strings).
  First full-pool pass (16:16) crashed dedupe: `'int' object has no attribute
  'strip'` (autopilot `.strip()` on int phone). **Triple fix:**
  (1) gateway `_record_out` coerces known string columns back to str on EVERY
  read (`_STRING_FIELDS`), (2) gateway now CREATES these columns as `text` not
  `json` (`_field_type`), (3) autopilot `_s()` helper wraps all loaded-field
  `.strip()` calls. Verified live: gateway returns 0 non-str phones; pass
  16:50 `no_email: 635, deferred: 22, invalid: 5, errors 0`. At-rest ints
  left as-is (harmless — every read goes through the gateway).
- **29 DUPLICATE LEADS removed (16:47 UTC):** pagination bug (only 50-row
  dedupe) let the autopilot re-add 29 already-imported leads between 15:17 and
  15:56 (same name+phone, no legacy_id). Deleted via gateway `id=eq.` DELETE,
  kept the legacy_id originals. Backup: `/home/ubuntu/dup_backup_20260809.json`
  (58 records = 29 dup pairs). Live count now **785** (783 import + 2
  non-legacy). **Collection name note:** real data lives in collection `leads`
  (public, no prefix). `leads__leads` is a junk collection with 2 probe rows
  (`probe-$(date +%s)`, `ec2-id-test`) — harmless, ignore it.
- **Data parity verified (15:12 UTC):** leads 784 (= 783 Supabase + 1 probe),
  agents 10, workspaces 2, goals 2, clients 1, org_charts 1, ws_agency__leads
  325, ws_agency__website_builds 5, ws_agency__website_docs 10,
  ws_agency__website_build_log 10. **Importer `deploy/_pb_import.py` is
  idempotent** (skips rows whose `legacy_id` already exists). Live count now
  **785 leads** (783 import + 2 non-legacy; 29 pagination-era dups removed
  16:47, backup `/home/ubuntu/dup_backup_20260809.json`). Autopilot writes
  flow through the gateway. Data lives in collection **`leads`** (public);
  `leads__leads` (2 probe rows) is junk, ignore it. `ws_agency__agent_memory`
  + `ws_agency__agent_checkpoints` (CEO persistence) present.
- **Autopilot now on gateway (15:11 UTC restart):** new leads POST via
  gateway (`201 Created`, verified 15:17:31), enrichment + email flows hit
  `127.0.0.1:8095`, gateway 500 count = 0.
- **Supabase docker stack REMOVED (15:39 UTC):** `docker compose down` +
  image removal in `/home/ubuntu/supabase/docker`. **Freed ~8.5GB disk**
  (31G→23G used, 81%→60%; 8 supabase images ~9GB + 11 containers removed)
  and **~290MB RAM** (swap pressure 1.6Gi→1.5Gi). Data volumes (67MB, DB
  data) preserved for rollback — `docker compose up -d` recreates the stack.
  Backend `.env` now points at `SUPABASE_URL=http://127.0.0.1:8095`. Remaining
  docker: rallly images only (2.6GB).
- **IMPORTANT PocketBase v0.39 quirk:** collection create/patch uses
  **`fields`** key, NOT `schema` (PATCHing with `schema` silently wipes all
  fields). Gateway + `deploy/_pb_init.py` both use `fields`.

---

## High Priority Tasks

1. **Autopilot healthy — 80+ passes, NRestarts=0** — DONE
   - Deployed `979ef71` (12:22 UTC): generic first-party email prefix fix (see #3).
   - Restart clean (12:22:48 UTC), fresh pass at 12:25 UTC complete normally.
   - After PB migration (15:11 UTC): passes continue normally on the gateway;
     pass 16:17 `no_email: 636, deferred: 21, invalid: 5, errors 0`.
   - Int-phone crash (16:16) fixed 16:50 (gateway coercion + autopilot `_s`);
     pass 16:50 clean `no_email: 635, deferred: 22, invalid: 5, errors 0`.
2. **Website backfill COMPLETE** — DONE
   - Backfill finished 10:30 UTC: 670 leads, 487 no-website, 63 with email.
   - Only orphaned chrome (port 9252) remains; harmless.
3. **Enrichment yield fix DEPLOYED (`979ef71`, 12:22 UTC)** — ROOT CAUSE FOUND + RE-ENRICH DONE
   - **Bug:** `_JUNK_PREFIXES`/`_JUNK_EMAIL_PREFIXES` unconditionally blocked
     `info@`, `contact@`, `hello@`, `support@`, `admin@`, `office@`... But for a
     local small business those ARE the owner inbox. `allow_consumer` only
     relaxed the DOMAIN check, not the PREFIX check, so `info@beyondwow.com`
     (found on the business's own verified page) was rejected as junk.
   - **Fix:** split prefixes into `_GENERIC_*` (info/contact/hello/office/
     support/admin/sales/service/...) allowed ONLY when provenance proves the
     address came from the business's own verified page
     (consumer/own_domain/homepage), and `_HARD_JUNK_*` (noreply/unsubscribe/
     careers/press/billing/mailer/bounce/...) always rejected.
   - Applied in `admin/tools/lead_enrichment.py` (validity + crawl) AND
     `admin/agency/sba_autopilot.py` (send gate) AND `deploy/_backfill_websites.py`.
   - **Proof live:** `info@beyondwow.com` now enriches as `own_domain`
     (previously empty).
4. **Re-enrichment batch COMPLETE (12:39 UTC)** — DONE
   - 133 website-having no-email leads retried with fixed gate (REST-based,
     venv, bypassed 24h cooldown).
   - **RESULT: found=44, skipped=1, failed=0.** All 44 emails patched to
     Supabase with provenance (mostly `own_domain`/`homepage`, 1 consumer).
     Examples: info@beyondwow.com, info@coolmenow.com, service@nicksplumbing.com,
     info@roofsquad.com, contact@dfw-roofinginc.com.
   - no_email now verified in PocketBase (pass 16:17): **636** (was ~541 in
     Supabase; the +95 delta is freshly-scraped leads without email yet).
5. **LEADS ARE FLOWING** — multi-source, NOT just Google Maps
   - Autopilot `_find_new_leads` → `find_leads_all` loops **5 sources**:
     google_maps, yelp, yellowpages, bing_maps, facebook_pages.
   - DB 671 leads (latest). Enrichment state tracks 156 leads; ~60 tried in 2h.
6. **Email sends — watch `emails_sent` after 14:00 UTC (in progress)**
   - Cap 30/day. Pass 14:02-14:55 showed `emails_sent: 0` (daily cap reached
     from earlier sends?); post-migration passes 15:17-16:17 also `0` with
     `deferred: 21` (business-hours gating). Watch next passes.
7. **Memory pressure on EC2:** 1.9GiB total. After Supabase removal (15:39 UTC)
   ~290MB RAM + ~8.5GB disk freed; swap pressure 1.6Gi→1.5Gi. PocketBase stack
   (backend + gateway + PB) ≈ 100MB. Do NOT add heavier workloads to EC2.
8. **Email send cap / Gmail daily limit** — once sends start, watch for 550s;
   backoff is 24h per recipient and is already implemented.

---

## Loop Engineering Setup — DONE (13:50 UTC)

- **7 loop skills installed to system** `C:\Users\TAUSHEF\.jcode\skills\`:
  `/install-loop`, `/loop-triage`, `/loop-verifier`, `/minimal-fix`,
  `/loop-budget`, `/loop-constraints`, `/budget-negotiator`
  (from cobusgreyling/loop-engineering, cloned 12:50 UTC, verified loaded via
  skill reload — 242 skills).
- **`loop doctor` on repo:** score **100 / L3** (was L2). Added:
  - `.claude/agents/loop-verifier.md` (maker/checker split agent)
  - `docs/safety.md` (path denylist, auto-merge L1/L2/L3 policy, MCP scopes,
    escalation, budget)
  - Commit `a8466f0`.
- **Not enabled (needs human opt-in):** Foundry harness (`--with-foundry`),
  GitHub issue/PR templates + workflows, MCP usage doc.
- User workflow: jab bhi `/loop-*` command ya "loop se kaam kar" bole, skills
  use hoti hain.

---

## Two-Account Migration — SUPERSEDED (Supabase removed 15:39 UTC)

**The original plan** (launch new t3.small in account `aws2` + migrate Supabase)
is **no longer needed**: Supabase docker was removed from EC2 #1 entirely and
replaced with PocketBase (≈100MB vs ≈400MB), freeing ~8.5GB disk (23G/38G used,
60%) and ~290MB RAM. Rallly remains on EC2 #1.

**Stale notes kept for reference:**
- New AWS account `301556368065` (Umer, IN) — profile `aws2`, region us-east-1,
  billing view HEALTHY. Free tier: t3.small eligible + $100 credit. Old account
  `default` (176980002493) untouched + `~/.aws/credentials.bak`.
- EC2 service activation was pending (`OptInRequired`) — no longer needed.
- Rallly on EC2 #1: `/home/ubuntu/rallly`, postgres 5450, app 3001 — untouched.

---

## Agency Agents Status (EC2: 18.213.66.136, t3.small)

**Framework: LangGraph** (crewai REMOVED `81cc807` — `crewai-repo/` deleted, .gitignore updated).
All agents expose FastAPI routes under `/api/*`; only SBA autopilot runs 24/7 as a
systemd daemon — the others are on-demand (API-driven, no scheduler daemon).

| Agent | Code | LangGraph? | API routes | Live status |
|---|---|---|---|---|
| **SBA autopilot** | `sba_autopilot.py` | `langgraph_sba.py` (SBAGraphState) | `/api/sba/*` | ✅ **running 24/7** (systemd `sba-autopilot.service`), ~20min cadence, NRestarts=0 |
| **CEO agent** | `ceo.py` → `AgencyCEO` | ✅ `build_ceo_graph()` (call_llm→run_tools→finalize) | `/api/ceo/chat`, `/handoff/receive`, `parallel-blast`, `review-output`, `route-error`, `generate-report` | ✅ graph builds OK, 4 nodes; **now Supabase-checkpointed** (`get_checkpointer("Agency","ceo")` fallback MemorySaver) + real `conversation_id` threading; on-demand (no daemon) |
| **Content agent** | `content_agent.py` → `AgencyContentAgent` | – (class-based) | `/api/content/init`, `/discover-brand`, `/status/{ws}` | ✅ importable + store present (`data/workspace_content_agents/ws_test.json`); on-demand |
| **SEO agent** | `seo_skills.py`, `seo_store.py` + `tools/seo_tools.py` | – | `/api/seo/chat`, `/audit`, `/audits` | ✅ importable; on-demand |
| **Social agent** | `social_skills.py` + `tools/social_tools.py` | – | `/api/social/chat`, `/calendar`, `/hashtags` | ✅ tokens store (`data/social_tokens/` 1/default/test); on-demand |
| **Website agent** | `website_skills.py` + `tools/website_tools.py` | – | `/api/website/chat`, `/analyze`, `/performance` | ✅ importable; on-demand |
| **Ads agent** | `tools/ads_tools.py` + `ads_api_client.py` | – | `/api/ads/status`, `/tools`, `/campaign-strategy` | ✅ importable; on-demand |
| **Swarm** | `swarm.py` | – | `/api/swarm/agents/add`, `/tasks/assign`, `/run` | ✅ importable; on-demand |
| **Orchestrator** | `orchestrator.py` | – (functions) | `/api/orch/workspace`, `/workspaces` | ✅ importable; on-demand |
| **Analytics** | routes only | – | `/api/analytics/status`, `/weekly-report` | ✅ on-demand |
| **Workflows** | routes only | – | `/api/workflows/*` | ✅ on-demand |
| **Agent aliases** | `routes/agent_aliases.py` | – | `/api/agents`, `/api/agents/{id}/chat`, `/seo-engine` | ✅ on-demand |

**Running services (systemd):**
| Service | Status | Notes |
|---|---|---|
| `sba.service` | active | backend API (all /api routes) |
| `sba-autopilot.service` | active | 24/7 SBA loop, ~15 min cadence, NRestarts=0 |
| `sba-chrome.service` | active | Chrome daemon for browser automation |
| `sba-gateway.service` | active | PB Supabase-compat gateway (8095) |
| `pocketbase.service` | active | PocketBase (8090), localhost-bound, enabled

**Other systemd agents:** NONE — no daemon runs CEO/content/SEO/social/website/ads.
They are API-on-demand only. A scheduler daemon is a future option (currently on-demand is the design).

**Email sends LIVE (13:19-13:20 UTC, first real sends!):** 12 emails sent to
re-enriched leads (info@flamingolandscapes.com, info@electricianatl.com,
info@primeroofrepairtampa.com, rainierroofingllc@hotmail.com, yosef@orlandoevergreen.com,
info@idealgardensorl.com, wayne@wayneslawnservice.com, info@hancocklandscape.com,
taylorlandscapingky@gmail.com, info@myersla.com, bladerunners1999@aol.com, +1).
Pass 13:25 summary: `emails_sent: 12, send_failed: 0, no_email: 540, deferred: 98`.
Pass 14:02: `emails_sent: 0` (cap reached for the day? watch). `reply_understood`
event seen 13:43 (a reply was processed).

| API health | ok | version 0.1.0, `ceo_ready: true`, workspace_count: 2 |
| Email client (`SBAEmailClient`) | enabled: True | creds live on EC2 (.env), code falls back to `TAGS_SMTP_*` |
| Database | **PocketBase** (gateway 8095) | 785 leads (live), ~635 no-email, CEO persistence in `ws_agency__agent_checkpoints` |
| Organic engine (7 channels) | deployed | telegram/gbp/facebook browser + api channels |

Deploy: `python deploy/deploy_sba.py` (bundle → scp → extract → py_compile → restart → verify).
Verify after deploy: `autopilot/status` endpoint, `journalctl -u sba-autopilot.service`.

---

## Current Error Logs (recent, journalctl sba-autopilot)

```
Aug 08 08:53  ImportError build_workspace_email_client / TypeError email_client  <- crash-loop, FIXED 9e3e83e
Aug 08 10:30  backfill DONE: 670 leads, 487 no website, 63 with email (orphaned chrome only)
Aug 08 12:21  pass 50: emails_sent 0, no_email 587, deferred 62 (US pre-business-hours)
Aug 08 12:25  pass 51: invalid_email 5 (newly-allowed addresses being rescored), NRestarts=0
Aug 08 12:39  re-enrichment batch: found=44 emails (own_domain/homepage), patched to Supabase
Aug 08 13:50  loop engineering setup: skills installed + doctor 100/L3 + verifier agent + safety.md
Aug 09 16:20  PAGINATION FIXED: gateway _build_limit pages ALL PocketBase pages
              (no limit → all rows; limit=N → up to N). Autopilot sees full
              pool again: pass 16:17 no_email 636 / deferred 21 / invalid 5 / errors 0.
Aug 09 16:16  INT-PHONE BUG: full-pool dedupe crashed ('int' object has no
              attribute 'strip') — PB json fields coerce digit-only phones to int.
Aug 09 16:50  FIXED: gateway _record_out coerces string cols to str on read +
              _field_type creates text not json + autopilot _s() helper.
              Pass 16:50 clean: no_email 635 / deferred 22 / invalid 5 / errors 0.
Aug 09 16:47  29 duplicate leads removed (pagination-era re-adds), backup saved
              /home/ubuntu/dup_backup_20260809.json. Live count 785.
Aug 09 15:39  Supabase stack stopped + removed (8 images gone): ~8.5GB disk freed
              (31G→23G, 81%→60%), ~290MB RAM. Data volumes preserved for rollback.
Aug 09 15:35  PocketBase bound to systemd (pocketbase.service), bind 0.0.0.0→127.0.0.1,
              enabled for reboot. Migration verified: PB counts match Supabase
              (784 vs 783 = probe +1); autopilot POSTing through gateway (201).
```

- No SMTP errors yet because no sends have happened (`send_failed: 0`).
- Leads ARE being judged each pass (Google Maps rotation active).
- `meetings` + `email_sends` tables do NOT exist in PocketBase either (same as
  Supabase) — meetings are stored locally in `sba_store` SQLite in-memory; a
  DB meetings table may be a future hardening step.

---

## Current Issue Being Fixed (DO NOT RESCAN THE REPO)

**Supabase→PocketBase migration is COMPLETE (15:11-16:17 UTC, branch
`feat/sba-lead-to-meeting-pipeline`).** Backend + autopilot run on the gateway
(8095) → PocketBase (8090). Data parity verified, autopilot writes flow, CEO
persistence collections present. The old "enrichment prefix fix" issue below is
historical — keep the fix notes but it is closed.

**Latest fix (16:01 UTC): gateway limit semantics** — see PocketBase section
(PAGINATION v2). Verified: 814 leads served, pass 16:17 `no_email: 636`.

**Historical — enrichment prefix fix (fixed `979ef71`, deployed 12:22 UTC, re-enrichment DONE 12:39 UTC):**
604 leads had no email, so the pipeline stalled at step 2. Root cause found in
the enrichment VALIDITY GATE, not the crawl: generic first-party prefixes
(info@/contact@/office@) were unconditionally rejected even when the address
came from the business's own verified page. 124 leads HAVE websites; many
expose exactly such addresses.

**Fix:** prefix lists split into generic (verified-only) vs hard-junk (always),
in both `lead_enrichment.py` and `sba_autopilot.py`. Provenance
consumer/own_domain/homepage now implies "verified first-party" and unlocks
generic prefixes; unverified scrapes still reject them.

**Proof:** `find_lead_email("Beyond Wow Plumbing & Drains", ..., site=beyondwow.com)`
now returns `info@beyondwow.com` (own_domain). Re-enrichment of the 133
website leads found **44 emails**, all patched (to Supabase then migrated to PB).

**Still open:** (a) ~480 leads with no website need Bing-based enrichment
(slower, lower yield); (b) 403/Cloudflare/JS-rendered sites
(papermoonpainting, johnmooreservices, texasqualityplumbing) need a headless
browser for email extraction — NOT on EC2 (memory); (c) watch `emails_sent`
and Gmail 550s once sends resume.

---

## Recent Commits (this branch)

| Commit | What |
|---|---|
| `59b3adb` | store: secure coupon/review routes (token required, no pending/code leak) + submodule pointer |
| `0964f2e` | store frontend: service images, coupons, reviews, banners, WhatsApp, GST/HSN removed, design polish (pushed → Vercel) |
| `866bc76` | store: submodule pointer → `b37650e` (image upload live) |
| `7e986ed` | store: returned/refunded statuses + settings round-trip verified (backend) |
| `b37650e` | store frontend: image upload (logo + product, data URL) |
| `104beb8` | store frontend: 5-tab dashboard nav (Dashboard/Orders/Products/Services/Settings) |
| `88b62bb` | store frontend: all 17 features (settings editor, orders detail/print/CSV/bulk dispatch, GST/HSN, stats) |
| `522031b` | docs: STATE.md — PocketBase bound to systemd service, PRODUCTION GREEN |
| `48242d3` | **feat(pocketbase): gateway GREEN on EC2 — id remap + pagination fix, autopilot on 8095, Supabase stopped** |
| `6bd88f5` | **CEO checkpointing: Supabase-backed cross-session memory + real conversation_id** (get_checkpointer("Agency","ceo"), fallback MemorySaver; tests 7 passed) |
| `a8466f0` | loop engineering: verifier agent + safety policy (doctor 100/L3) (current) |
| `aee18a7` | docs: STATE.md update after prefix fix deploy |
| `979ef71` | **generic first-party prefix fix (enrichment yield)** |
| `1e5a733` | docs: STATE.md — crash-loop fixed, backfill running, leads flowing |
| `9e3e83e` | crash-loop fix + junk email gate + workspace email identity |
| `4c6dc28` | prioritize enrichment-ready leads + backfill phone-match fix |
| `0c1352c` | enrichment internal 38s budget + shrinking timeouts |
| `0711677` | enrichment state persistence + 45s wrapper timeout |
| `87ff421` | leads `website` column migration (PGRST204 fix) |
| `aa38243` | email client `TAGS_SMTP_*` env fallback |
| `f3efb99` | repo cleanup: removed scratch files, updated .gitignore |
| `0b03900` | capture `website` from Maps, os import, settle 8s |

## Run Log

- 09:05 UTC — backfill relaunched with junk gate (pid 2367341), 668 leads.
- 10:30 UTC — backfill DONE: 670 leads, 63 with email. Only orphaned chrome.
- 12:22 UTC — deployed `979ef71` (generic prefix fix), autopilot restarted
  clean, NRestarts=0.
- 12:25 UTC — pass 51: `invalid_email: 5`, `no_email: 585` (fix live).
- 12:26 UTC — re-enrichment batch started for 124 website-having no-email
  leads (bypasses 24h cooldown).
- 12:39 UTC — re-enrichment DONE: **found=44 emails** (skipped=1, failed=0),
  all patched to Supabase with provenance. no_email ~541.
- 12:40 UTC — Supabase verify script prepared (ran remotely via venv).
- 13:50 UTC — loop-engineering setup: 7 skills installed to system, `loop
  doctor` score 100/L3, verifier agent + safety.md committed (`a8466f0`).
- 15:11 UTC — autopilot restarted on PocketBase gateway (8095); new leads
  POSTing `201 Created`; enrichment + email flows hit `127.0.0.1:8095`.
- 15:12 UTC — data parity verified: 784 leads (783 Supabase + 1 probe), agents
  10, workspaces 2; importer idempotent.
- 15:35 UTC — PocketBase bound to systemd (`pocketbase.service`), bind
  `0.0.0.0:8090` → `127.0.0.1:8090`, enabled for reboot.
- 15:39 UTC — Supabase stack stopped + removed (8 images ~9GB, 11 containers):
  ~8.5GB disk freed (31G→23G, 81%→60%), ~290MB RAM. Volumes preserved.
- 16:01 UTC — gateway pagination fix (`_build_limit` pages all PB pages; no
  limit → all rows). Deployed to root `/home/ubuntu/sba-backend/pb_gateway.py`.
- 16:16 UTC — first full-pool pass crashed dedupe: `'int' object has no
  attribute 'strip'` (PB json fields coerce digit-only phones to int).
- 16:47 UTC — 29 pagination-era duplicate leads removed via gateway DELETE
  (backup `/home/ubuntu/dup_backup_20260809.json`); live count 785.
- 16:50 UTC — INT-PHONE FIX live: gateway `_record_out` coerces string cols
  to str, `_field_type` creates text not json, autopilot `_s()` helper.
  Verified: 0 non-str phones; pass 16:50 `no_email: 635, deferred: 22,
  invalid: 5, errors 0`. NRestarts=0.

---

## SBA Workspace Isolation Audit (2026-08-08, code + live EC2)

**Question:** har client workspace ek alag (isolated) kaise hai?

**How isolation works (code, `admin/agency/sba_autopilot.py` + `sba_biztypes.py`):**
Each workspace gets its own `SBAAutopilot` instance (`run_all_once` loops
`list_sba_workspaces()`). Isolation key = `workspace_name` column on leads.

| Isolation domain | Mechanism | Verdict |
|---|---|---|
| Lead pool | `run_once` filters `workspace_name == self.workspace_name` before emailing; dedupe (name+phone) also workspace-scoped | ✅ isolated |
| New leads tagged | every saved row gets `workspace_name: self.workspace_name` | ✅ |
| Rotation cursor | per-workspace file `sba_rotation_{ws}.state` | ✅ |
| Outreach angle/strategy | per-workspace `sba_strategy_{ws}.json` | ✅ |
| Reasoning journal | per-workspace `sba_reasoning_{ws}.log` | ✅ |
| Owner email | `owner_email` from config; owner notifications + `_is_owner` use workspace owner (fallback agency OWNER_EMAIL) | ✅ |
| Reply handling | replies matched against THIS workspace's lead list only (email match); owner commands resolve only within workspace leads | ✅ |
| Meetings | created only from workspace-filtered leads; stored with `lead_id` (indirect scoping via lead) | ✅ (minor: meeting rows carry no `workspace_name` themselves) |

**Live status (EC2):**
- `sba_workspaces.json` does NOT exist on EC2 → `list_sba_workspaces()` runs
  **only the `agency` workspace** (it auto-injects agency when config missing).
- Supabase: **all leads are `workspace_name = agency`**. No client workspace
  is SBA-enabled yet.
- `api/health` `workspace_count: 2` counts the platform workspaces table (CEO
  workspaces), NOT SBA-enabled workspaces — don't confuse the two.

**Low-risk shared resources (note, not bugs):**
- **One shared Gmail inbox** for all workspaces (SMTP/IMAP creds are global).
  `check_replies(mark_read=True)` runs per workspace pass; with 2+ workspaces a
  reply could be consumed by whichever pass runs first. Today harmless (agency
  only), but a future per-workspace inbox or a `seen`-flag filter would harden it.
- **Enrichment cooldown file** `.sba_enrichment_state` is one shared file keyed
  by globally-unique lead id → no cross-contamination.
- **`client_id` on saved leads is hardcoded** to `00000000-...-0001` for all
  workspaces, but it is never read for filtering (isolation is by
  `workspace_name`) — dead metadata, low priority to fix.

**To enable a client workspace:** create `sba_workspaces.json` on EC2
(`{"<ws>": {"enabled": true, "owner_email": "...", "category": "..."}}`) or call
`set_workspace_config()`; next autopilot restart picks it up with its own
rotation/strategy/journal/owner and its own lead pool.
