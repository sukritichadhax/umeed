import os
from pathlib import Path
from io import BytesIO
from datetime import datetime, timezone, timedelta
import secrets
import qrcode
from PIL import Image, UnidentifiedImageError
import re

from sqlalchemy import inspect, text

from dotenv import load_dotenv

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    abort
)

from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user
)

from models import (
    db,
    User,
    NGO,
    Campaign,
    Donation,
    DonationItem,
    DonationEvent
)


# ==========================================
# APPLICATION CONFIGURATION
# ==========================================

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

app = Flask(__name__)
# ==========================================
# INDIAN STANDARD TIME FORMATTER
# ==========================================

IST = timezone(timedelta(hours=5, minutes=30))


def format_ist_timestamp(
    value,
    date_format="%d %b %Y, %I:%M %p"
):
    """
    Convert stored UTC timestamps into Indian Standard Time.

    Existing database timestamps are assumed to be naive UTC
    because the application currently uses datetime.utcnow().
    """

    if value is None:
        return ""

    # Treat timestamps without timezone information as UTC.

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    # Convert to IST and format for display.

    return value.astimezone(IST).strftime(date_format)


# Make the formatter available in Jinja templates.

app.jinja_env.filters["ist_datetime"] = format_ist_timestamp

app.config["SECRET_KEY"] = os.getenv(
    "SECRET_KEY",
    "development-only-change-before-deployment"
)

database_url = os.environ.get("DATABASE_URL")

if database_url:
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + str(BASE_DIR / "umeed.db")

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAX_CONTENT_LENGTH"] = 40 * 1024 * 1024  # allow multiple product images, with per-file limits below

db.init_app(app)


# ==========================================
# LOGIN CONFIGURATION
# ==========================================

login_manager = LoginManager()

login_manager.init_app(app)

login_manager.login_view = "login"

login_manager.login_message = "Please sign in to continue."


@login_manager.user_loader
def load_user(user_id):
    """Load the authenticated user from the database."""

    return db.session.get(User, int(user_id))


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def require_role(*roles):
    """Restrict access to users with specified roles."""

    if not current_user.is_authenticated:
        abort(401)

    if current_user.role not in roles:
        abort(403)


def get_approved_ngo(user):
    """Return the user's approved NGO, if applicable."""

    if user.role != "ngo_staff":
        return None

    ngo = user.ngo

    if not ngo or ngo.status != "approved":
        return None

    return ngo

# ==========================================
# CAMPAIGN EDITOR HELPERS
# ==========================================

LEGACY_DEFAULT_PRODUCT_CATALOG = """Baby food (300 g pack)|100|295|
Powdered milk (500 g pack)|100|220|
Poha (1 kg)|100|100|
Atta (5 kg bag)|100|250|
Rice (5 kg bag)|100|250|
Mineral water (1 L bottle)|500|18|
Tarpaulin sheet (12 x 15 ft)|30|599|
Rechargeable LED torch (1 unit)|50|399|
Iodised salt (1 kg)|100|28|
Sugar (1 kg)|100|59|"""

# The vendor-procurement catalogue is deliberately separate from campaign.required_items,
# which continues to control the physical in-kind donation tab.
DEFAULT_PRODUCT_CATALOG = """Iodised salt (1 kg)|100|28|
Sugar (1 kg)|100|59|
Atta (5 kg bag)|100|250|
Masoor dal (1 kg pack)|100|160|
Rechargeable LED torch (1 unit)|50|399|
Baby food (300 g pack)|100|295|
Powdered milk (500 g pack)|100|220|"""

DEFAULT_CAROUSEL_IMAGES = [
    "https://images.unsplash.com/photo-1547683905-f686c993aae5?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1488521787991-ed7bbaae773c?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1593113598332-cd288d649433?auto=format&fit=crop&w=1200&q=80",
]

DEFAULT_PRODUCTS_INTRO = (
    "Choose the relief products you would like Umeed to arrange from suppliers. "
    "Prices are estimated unit costs and may change with supplier quotations."
)

DEFAULT_IN_KIND_INTRO = (
    "Choose the products you intend to provide, then pack and label "
    "them carefully so the receiving team can sort them safely."
)

DEFAULT_PACKAGING_STEPS = """Check that food is unopened, properly sealed, and within its expiry date.
Group similar items together and count the quantities before packing.
Use clean, sturdy boxes. Keep liquids separate from food, clothing, and other items.
Print the donation QR code and attach it clearly to the outside of each box. If a label or count is unclear, the team will try to contact you to resolve it. Unsafe, expired, or contaminated items may need to be declined."""


def parse_product_catalog(raw):
    """
    Convert the editable product catalogue into validated product rows.

    Each non-empty line must use:
    Product name | Required quantity | Unit price | Image URL
    """

    products = []
    seen_names = set()

    for line_number, line in enumerate(raw.splitlines(), start=1):
        if not line.strip():
            continue

        parts = [part.strip() for part in line.split("|", 3)]

        if len(parts) != 4:
            raise ValueError(
                f"Product line {line_number} must contain four fields "
                "separated by | characters."
            )

        name, quantity_text, price_text, image_url = parts

        if not name or len(name) > 120:
            raise ValueError(
                f"Enter a product name of 1–120 characters "
                f"on line {line_number}."
            )

        normalized_name = name.casefold()

        if normalized_name in seen_names:
            raise ValueError(
                f"The product name '{name}' appears more than once."
            )

        seen_names.add(normalized_name)

        try:
            required_qty = int(quantity_text)
            unit_price = int(price_text)
        except ValueError:
            raise ValueError(
                f"Quantity and price must be whole numbers "
                f"on product line {line_number}."
            )

        if not 0 <= required_qty <= 1000000:
            raise ValueError(
                f"Quantity must be between 0 and 1,000,000 "
                f"on line {line_number}."
            )

        if not 0 <= unit_price <= 10000000:
            raise ValueError(
                f"Price must be between ₹0 and ₹10,000,000 "
                f"on line {line_number}."
            )

        if image_url and not image_url.startswith(
            ("https://", "http://", "/static/")
        ):
            raise ValueError(
                f"Use an HTTPS/HTTP image URL or a /static/ path "
                f"on line {line_number}."
            )

        products.append({
            "name": name,
            "required_qty": required_qty,
            "unit_price": unit_price,
            "image_url": image_url,
        })

    if not products:
        raise ValueError("Add at least one product to the catalogue.")

    if len(products) > 20:
        raise ValueError("A campaign can have at most 20 product types.")

    return products


def campaign_products_for(campaign):
    """Return product data in the format expected by campaign_detail.html."""

    raw = campaign.product_catalog or DEFAULT_PRODUCT_CATALOG

    try:
        parsed_products = parse_product_catalog(raw)
    except ValueError:
        app.logger.warning(
            "Invalid product catalogue on campaign %s; using demo items.",
            campaign.id,
        )
        parsed_products = parse_product_catalog(DEFAULT_PRODUCT_CATALOG)

    # Get the same accepted and outstanding quantities used by the tracker.
    tracker_rows = campaign_supply_summary(campaign)

    tracker_by_name = {
        str(row.get("name", "")).strip().casefold(): row
        for row in tracker_rows
    }

    products = []

    for index, item in enumerate(parsed_products):
        name = item["name"]
        required = int(item["required_qty"])

        # Match the product to the campaign's supply tracker.
        tracker = tracker_by_name.get(name.casefold(), {})

        accepted = int(tracker.get("accepted", 0) or 0)
        committed = int(tracker.get("committed", 0) or 0)

        if "available" in tracker:
            available = max(0, int(tracker["available"] or 0))
        else:
            available = max(0, required - accepted - committed)

        # Extract the pack size from names such as "Rice (5 kg bag)".
        if "(" in name and ")" in name:
            unit_label = name.rsplit("(", 1)[1].split(")", 1)[0].strip()
        else:
            unit_label = "unit"

        image_url = item["image_url"] or (
            "https://placehold.co/600x450/f8fafc/1d3557"
            "?text=Relief+product"
        )

        products.append({
            "index": index,
            "name": name,
            "required": required,
            "required_qty": required,
            "accepted": accepted,
            "committed": committed,
            "available": available,
            "unit_price": int(item["unit_price"]),
            "unit_label": unit_label,
            "image": image_url,
            "image_url": image_url,
        })

    return products


def campaign_packaging_steps(campaign):
    """Return the four current packaging instructions."""

    raw = campaign.packaging_steps or DEFAULT_PACKAGING_STEPS

    return [
        step.strip()
        for step in raw.splitlines()
        if step.strip()
    ]

# Temporary catalogue for the prototype. Replace rates and image URLs with
# NGO-confirmed procurement details when the campaign editor is implemented.
DEMO_PRODUCT_META = {
    "baby food 300 g pack": {
        "unit_price": 295,
        "unit_label": "pack",
        "image": "https://images.unsplash.com/photo-1498837167922-ddd27525d352?auto=format&fit=crop&w=700&q=80",
    },
    "powdered milk 500 g pack": {
        "unit_price": 220,
        "unit_label": "pack",
        "image": "https://images.unsplash.com/photo-1550583724-b2692b85b150?auto=format&fit=crop&w=700&q=80",
    },
    "poha 1 kg": {
        "unit_price": 100,
        "unit_label": "1 kg pack",
        "image": "https://images.unsplash.com/photo-1586201375761-83865001e31c?auto=format&fit=crop&w=700&q=80",
    },
    "atta 5 kg bag": {
        "unit_price": 250,
        "unit_label": "5 kg bag",
        "image": "https://images.unsplash.com/photo-1627485937980-221c88ac04f9?auto=format&fit=crop&w=700&q=80",
    },
    "rice 5 kg bag": {
        "unit_price": 250,
        "unit_label": "5 kg bag",
        "image": "https://images.unsplash.com/photo-1586201375761-83865001e31c?auto=format&fit=crop&w=700&q=80",
    },
    "mineral water 1 l bottle": {
        "unit_price": 18,
        "unit_label": "1 L bottle",
        "image": "https://images.unsplash.com/photo-1606168094336-48f205276929?auto=format&fit=crop&w=700&q=80",
    },
    "tarpaulin sheet 12x15 ft": {
        "unit_price": 599,
        "unit_label": "sheet",
        "image": "https://images.unsplash.com/photo-1504280390367-361c6d9f38f4?auto=format&fit=crop&w=700&q=80",
    },
    "rechargeable led torch 1 unit": {
        "unit_price": 399,
        "unit_label": "torch",
        "image": "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?auto=format&fit=crop&w=700&q=80",
    },
    "masoor dal 1 kg pack": {
        "unit_price": 160,
        "unit_label": "1 kg pack",
        "image": "https://images.unsplash.com/photo-1586201375761-83865001e31c?auto=format&fit=crop&w=700&q=80",
    },
    "masoor dal 1 kg": {
        "unit_price": 160,
        "unit_label": "1 kg pack",
        "image": "https://images.unsplash.com/photo-1586201375761-83865001e31c?auto=format&fit=crop&w=700&q=80",
    },
    "iodised salt 1 kg": {
        "unit_price": 28,
        "unit_label": "1 kg pack",
        "image": "https://images.unsplash.com/photo-1518110925495-5fe2fda0442b?auto=format&fit=crop&w=700&q=80",
    },
    "sugar 1 kg": {
        "unit_price": 59,
        "unit_label": "1 kg pack",
        "image": "https://images.unsplash.com/photo-1581441363689-1f3c3c414635?auto=format&fit=crop&w=700&q=80",
    },
}


def normalize_supply_name(value):
    """Normalize supply labels and map the legacy Tarpaulins label to the catalogue name."""
    key = " ".join(re.sub(r"[^a-z0-9]+", " ", (value or "").casefold()).split())
    # Normalise dimensions such as "12 x 15 ft" and "12x15 ft" to the same key.
    key = re.sub(r"\b(\d+)\s+x\s+(\d+)\b", r"\1x\2", key)
    aliases = {
        "tarpaulins": "tarpaulin sheet 12x15 ft",
        "tarpaulin": "tarpaulin sheet 12x15 ft",
        "tarpaulin sheets": "tarpaulin sheet 12x15 ft",
        "tarpaulin sheet": "tarpaulin sheet 12x15 ft",
        "tarpaulin sheet 12x15 ft": "tarpaulin sheet 12x15 ft",
    }
    return aliases.get(key, key)


def campaign_procurement_summary(campaign):
    """Track vendor-procurement product requests separately from physical in-kind needs."""
    from collections import defaultdict

    try:
        catalog = parse_product_catalog(campaign.product_catalog or DEFAULT_PRODUCT_CATALOG)
    except ValueError:
        catalog = parse_product_catalog(DEFAULT_PRODUCT_CATALOG)

    required_by_key = {
        normalize_supply_name(item["name"]): item
        for item in catalog
    }
    accepted_by_key = defaultdict(int)
    committed_by_key = defaultdict(int)

    donations = Donation.query.filter_by(campaign_id=campaign.id).all()
    for donation in donations:
        if donation.delivery_method != "vendor_procurement":
            continue
        if donation.status in {"cancelled", "rejected"}:
            continue

        for item in donation.items:
            key = normalize_supply_name(item.item_name)
            if key not in required_by_key:
                continue
            if donation.status == "verified" and item.accepted_qty is not None:
                accepted_by_key[key] += max(0, int(item.accepted_qty or 0))
            elif donation.status in {"offered", "accepted", "awaiting_confirmation", "received"}:
                committed_by_key[key] += max(0, int(item.declared_qty or 0))

    summary = []
    for key, product in required_by_key.items():
        required = int(product["required_qty"])
        accepted = accepted_by_key[key]
        committed = committed_by_key[key]
        available = max(0, required - accepted - committed)
        percent = min(100, round(accepted * 100 / required)) if required else 0

        if required and accepted >= required:
            status = "Target reached"
        elif available == 0 and required:
            status = "Fully committed — awaiting procurement/delivery"
        elif required and accepted / required >= 0.9:
            status = "Almost fulfilled"
        elif accepted:
            status = "In progress"
        else:
            status = "Needs supplies"

        summary.append({
            "name": product["name"],
            "required": required,
            "accepted": accepted,
            "committed": committed,
            "available": available,
            "percent": percent,
            "status": status,
        })
    return summary


def campaign_product_options(campaign):
    """Products shown in Donate Products; targets come from the separate procurement catalogue."""
    try:
        catalogue = parse_product_catalog(campaign.product_catalog or DEFAULT_PRODUCT_CATALOG)
    except ValueError:
        app.logger.warning(
            "Invalid product catalogue for campaign %s; using safe defaults.",
            campaign.id,
        )
        catalogue = parse_product_catalog(DEFAULT_PRODUCT_CATALOG)

    summary_by_key = {
        normalize_supply_name(row["name"]): row
        for row in campaign_procurement_summary(campaign)
    }
    products = []

    for index, item in enumerate(catalogue):
        key = normalize_supply_name(item["name"])
        tracker = summary_by_key.get(key, {})
        meta = DEMO_PRODUCT_META.get(key, {})
        name = item["name"]
        unit_label = (
            name.rsplit("(", 1)[1].split(")", 1)[0].strip()
            if "(" in name and ")" in name
            else meta.get("unit_label", "unit")
        )
        image = item["image_url"] or meta.get("image") or (
            "https://placehold.co/600x450/f8fafc/1d3557?text=Relief+product"
        )
        products.append({
            "index": index,
            "name": name,
            "required": int(item["required_qty"]),
            "required_qty": int(item["required_qty"]),
            "accepted": int(tracker.get("accepted", 0)),
            "committed": int(tracker.get("committed", 0)),
            "available": int(tracker.get("available", item["required_qty"])),
            "percent": int(tracker.get("percent", 0)),
            "status": tracker.get("status", "Needs supplies"),
            "unit_price": int(item["unit_price"]),
            "unit_label": unit_label,
            "image": image,
            "image_url": image,
        })
    return products


def campaign_inkind_options(campaign):
    """Physical in-kind needs, always sourced from campaign.required_items."""
    products = []
    for index, need in enumerate(campaign_supply_summary(campaign)):
        key = normalize_supply_name(need["name"])
        meta = DEMO_PRODUCT_META.get(key, {})
        products.append({
            **need,
            "index": index,
            "unit_price": int(meta.get("unit_price", 0)),
            "unit_label": meta.get("unit_label", "unit"),
            "image": meta.get("image") or (
                "https://placehold.co/600x450/f8fafc/1d3557?text=Physical+donation"
            ),
            "image_url": meta.get("image", ""),
        })
    return products


def save_product_image(upload, campaign_id, product_index):
    """Validate and save a PNG/JPEG/WebP upload under static for the local prototype."""
    if not upload or not upload.filename:
        return None

    raw = upload.read(5 * 1024 * 1024 + 1)
    if not raw:
        raise ValueError("An uploaded product image is empty.")
    if len(raw) > 5 * 1024 * 1024:
        raise ValueError("Each product image must be 5 MB or smaller.")

    try:
        image = Image.open(BytesIO(raw))
        image.verify()
        image = Image.open(BytesIO(raw))
        image_format = (image.format or "").upper()
        width, height = image.size
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        raise ValueError("Upload a valid PNG, JPEG, or WebP image.")

    extensions = {"PNG": ".png", "JPEG": ".jpg", "WEBP": ".webp"}
    if image_format not in extensions:
        raise ValueError("Product images must be PNG, JPEG, or WebP files.")
    if width < 1 or height < 1 or width * height > 20_000_000:
        raise ValueError("Product images must have at most 20 megapixels.")

    upload_dir = BASE_DIR / "static" / "campaign_product_images"
    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = f"campaign_{campaign_id}_product_{product_index}_{secrets.token_hex(6)}{extensions[image_format]}"
    destination = upload_dir / filename

    # Re-encode the file so embedded metadata is not retained.
    if image_format == "JPEG":
        image = image.convert("RGB")
    save_options = {"optimize": True} if image_format in {"PNG", "JPEG"} else {}
    image.save(destination, format=image_format, **save_options)

    return f"/static/campaign_product_images/{filename}"


def get_selected_campaign_products(campaign):
    """Validate selected quantities on the server and calculate the displayed basket total."""
    products = campaign_product_options(campaign)
    selected = []
    total = 0

    for product in products:
        raw_qty = request.form.get(f'qty_{product["index"]}', "0").strip()
        try:
            quantity = int(raw_qty or "0")
        except ValueError:
            raise ValueError(f"Enter a whole-number quantity for {product['name']}.")

        if quantity < 0 or quantity > 10000:
            raise ValueError("Each quantity must be between 0 and 10,000.")

        available = max(0, int(product["available"]))
        if quantity > available:
            raise ValueError(
                f"Only {available} {product['name']} currently remain available. Please update your quantity."
            )

        if quantity == 0:
            continue

        line_total = quantity * product["unit_price"]
        selected.append({
            "index": product["index"],
            "name": product["name"],
            "quantity": quantity,
            "condition": "good",
            "unit_price": product["unit_price"],
            "unit_label": product["unit_label"],
            "line_total": line_total,
        })
        total += line_total

    if not selected:
        raise ValueError("Please select a quantity for at least one supply.")

    return selected, total

# ==========================================
# RECORD DONATION HISTORY EVENTS
# ==========================================

def record_event(donation, event_type, note="", user_id=None):
    """Record an event at the time the action occurs."""

    event_time_utc = datetime.now(
        timezone.utc
    ).replace(tzinfo=None)

    event = DonationEvent(
        donation=donation,
        event_type=event_type,
        note=note,
        user_id=user_id,
        created_at=event_time_utc
    )

    db.session.add(event)

# ==========================================
# HOME AND HEALTH CHECK
# ==========================================

# ==========================================
# HOMEPAGE
# ==========================================

@app.route("/")
def home():

    # Administrators go directly to their workspace.

    if (
        current_user.is_authenticated
        and current_user.role == "admin"
    ):
        return redirect(url_for("dashboard"))

    return render_template("index.html")


@app.route("/health")
def health():

    return {
        "status": "ok",
        "app": "Umeed"
    }


# ==========================================
# USER REGISTRATION
# ==========================================

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        account_type = request.form.get("account_type", "donor")

        if not name or not email or not password:
            flash("Please complete all required fields.", "error")
            return render_template("register.html"), 400
        if len(name) > 150 or len(email) > 254:
            flash("Name or email is too long.", "error")
            return render_template("register.html"), 400
        if len(password) < 8:
            flash("Your password must contain at least 8 characters.", "error")
            return render_template("register.html"), 400
        if account_type not in {"donor", "ngo"}:
            flash("Invalid account type.", "error")
            return render_template("register.html"), 400
        if User.query.filter_by(email=email).first():
            flash("An account with this email already exists.", "error")
            return render_template("register.html"), 400

        user = User(name=name, email=email)
        user.set_password(password)

        if account_type == "ngo":
            ngo_name = request.form.get("ngo_name", "").strip()
            ngo_location = request.form.get("ngo_location", "").strip()
            ngo_description = request.form.get("ngo_description", "").strip()
            legal_form = request.form.get("ngo_legal_form", "").strip()
            registration_number = request.form.get("ngo_registration_number", "").strip()
            registration_authority = request.form.get("ngo_registration_authority", "").strip()
            evidence_url = request.form.get("ngo_evidence_url", "").strip()

            if not all([ngo_name, ngo_location, ngo_description, legal_form,
                        registration_number, registration_authority, evidence_url]):
                flash("Please complete all organisation details and verification evidence fields.", "error")
                return render_template("register.html"), 400
            if not evidence_url.lower().startswith(("https://", "http://")):
                flash("Enter a valid HTTP/HTTPS link to the supporting evidence.", "error")
                return render_template("register.html"), 400
            if (len(ngo_name) > 180 or len(ngo_location) > 180 or
                    len(ngo_description) > 600 or len(legal_form) > 60 or
                    len(registration_number) > 120 or len(registration_authority) > 150 or
                    len(evidence_url) > 500):
                flash("One or more organisation fields exceeds its length limit.", "error")
                return render_template("register.html"), 400

            ngo = NGO(
                name=ngo_name,
                email=email,
                location=ngo_location,
                description=ngo_description,
                status="pending",
                legal_form=legal_form,
                registration_number=registration_number,
                registration_authority=registration_authority,
                evidence_url=evidence_url,
            )
            db.session.add(ngo)
            db.session.flush()
            user.role = "ngo_staff"
            user.ngo = ngo
        else:
            user.role = "donor"

        db.session.add(user)
        db.session.commit()
        login_user(user)

        if user.role == "ngo_staff":
            flash("Your NGO registration is awaiting administrator approval.", "success")
        else:
            flash("Your account has been created successfully.", "success")

        return redirect(url_for("dashboard"))

    return render_template("register.html")


# ==========================================
# USER LOGIN
# ==========================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        user = User.query.filter_by(
            email=email
        ).first()

        if user and user.check_password(password):

            login_user(user)

            flash(
                "Welcome back.",
                "success"
            )

            return redirect(url_for("dashboard"))

        flash(
            "Incorrect email or password.",
            "error"
        )

    return render_template("login.html")


# ==========================================
# USER LOGOUT
# ==========================================

@app.route("/logout", methods=["POST"])
@login_required
def logout():

    logout_user()

    flash(
        "You have signed out.",
        "success"
    )

    return redirect(url_for("home"))


# ==========================================
# ROLE-SPECIFIC DASHBOARDS
# ==========================================

@app.route("/dashboard")
@login_required
def dashboard():

    # Administrator dashboard

    if current_user.role == "admin":

        pending_ngos = NGO.query.filter_by(
            status="pending"
        ).order_by(
            NGO.created_at.desc()
        ).all()

        pending_campaigns = Campaign.query.filter_by(
            status="pending"
        ).order_by(
            Campaign.created_at.desc()
        ).all()

        return render_template(
            "dashboard.html",
            dashboard_type="admin",
            pending_ngos=pending_ngos,
            pending_campaigns=pending_campaigns
        )

    # NGO staff dashboard

    if current_user.role == "ngo_staff":

        ngo = current_user.ngo

        # The NGO cannot operate campaigns until approved.

        if not ngo or ngo.status != "approved":

            return render_template(
                "dashboard.html",
                dashboard_type="ngo_pending",
                ngo=ngo
            )

        campaigns = Campaign.query.filter_by(
            ngo_id=ngo.id
        ).order_by(
            Campaign.created_at.desc()
        ).all()

        donations = Donation.query.filter_by(
            ngo_id=ngo.id
        ).order_by(
            Donation.created_at.desc()
        ).limit(10).all()

        return render_template(
            "dashboard.html",
            dashboard_type="ngo",
            ngo=ngo,
            campaigns=campaigns,
            donations=donations
        )

    # Donor dashboard

    donations = Donation.query.filter_by(
        donor_id=current_user.id
    ).order_by(
        Donation.created_at.desc()
    ).all()

    return render_template(
        "dashboard.html",
        dashboard_type="donor",
        donations=donations
    )

@app.route("/ngo/campaigns/<int:campaign_id>/needs", methods=["GET", "POST"])
@login_required
def edit_campaign_needs(campaign_id):
    require_role("ngo_staff")
    ngo = get_approved_ngo(current_user)
    if not ngo:
        abort(403)

    campaign = Campaign.query.filter_by(
        id=campaign_id,
        ngo_id=ngo.id
    ).first_or_404()

    if request.method == "POST":
        import re
        raw = request.form.get("required_items", "").strip()
        rows = []
        seen = set()
        allowed_names = {normalize_supply_name(name) for name in DEMO_PRODUCT_META}

        for line in raw.splitlines():
            if not line.strip():
                continue
            match = re.match(r"^\s*(.+?)\s*:\s*(\d+)\s*$", line)
            if not match:
                flash(f"Use the format Product (pack size): quantity. Problem line: {line}", "error")
                return render_template("edit_campaign_needs.html", campaign=campaign, form_items=raw), 400

            name = match.group(1).strip()
            key = normalize_supply_name(name)
            quantity = int(match.group(2))
            if key not in allowed_names:
                flash(f"'{name}' is not in this demo catalogue. Use one of the ten listed product names and pack sizes.", "error")
                return render_template("edit_campaign_needs.html", campaign=campaign, form_items=raw), 400
            if key in seen:
                flash(f"'{name}' appears more than once. Combine it into one line.", "error")
                return render_template("edit_campaign_needs.html", campaign=campaign, form_items=raw), 400
            if not 1 <= quantity <= 1000000:
                flash("Each requirement must be from 1 to 1,000,000 units.", "error")
                return render_template("edit_campaign_needs.html", campaign=campaign, form_items=raw), 400
            seen.add(key)
            rows.append(f"{name}: {quantity}")

        if not rows:
            flash("Add at least one campaign requirement.", "error")
            return render_template("edit_campaign_needs.html", campaign=campaign, form_items=raw), 400

        campaign.required_items = "\n".join(rows)
        campaign.last_verified_at = datetime.utcnow()
        db.session.commit()
        flash("Campaign requirements updated. The tracker and product picker now use these quantities.", "success")
        return redirect(url_for("campaign_detail", campaign_id=campaign.id))

    return render_template("edit_campaign_needs.html", campaign=campaign)

# ==========================================
# ADMINISTRATOR: NGO APPROVAL
# ==========================================

@app.route(
    "/admin/ngos/<int:ngo_id>/approve",
    methods=["POST"]
)
@login_required
def approve_ngo(ngo_id):

    require_role("admin")

    ngo = db.session.get(NGO, ngo_id)

    if not ngo:
        abort(404)

    registration_checked = request.form.get("review_registration_checked") == "on"
    address_checked = request.form.get("review_address_checked") == "on"
    contact_checked = request.form.get("review_contact_checked") == "on"
    review_notes = request.form.get("review_notes", "").strip()

    if not all([
        ngo.legal_form,
        ngo.registration_number,
        ngo.registration_authority,
        ngo.evidence_url,
    ]):
        flash("This NGO has not supplied all required evidence details.", "error")
        return redirect(url_for("dashboard"))

    if not all([registration_checked, address_checked, contact_checked]):
        flash("Complete all three verification checks before approving this NGO.", "error")
        return redirect(url_for("dashboard"))

    if not review_notes:
        flash("Add a short note describing the basis for this review.", "error")
        return redirect(url_for("dashboard"))

    ngo.review_registration_checked = registration_checked
    ngo.review_address_checked = address_checked
    ngo.review_contact_checked = contact_checked
    ngo.review_notes = review_notes[:2000]
    ngo.reviewed_at = datetime.utcnow()
    ngo.status = "approved"
    db.session.commit()

    flash(f"{ngo.name} approved. The review checklist has been recorded.", "success")
    return redirect(url_for("dashboard"))

@app.route(
    "/admin/ngos/<int:ngo_id>/reject",
    methods=["POST"]
)
@login_required
def reject_ngo(ngo_id):

    require_role("admin")

    ngo = db.session.get(NGO, ngo_id)

    if not ngo:
        abort(404)

    ngo.status = "rejected"

    db.session.commit()

    flash(
        f"{ngo.name} has been rejected.",
        "success"
    )

    return redirect(url_for("dashboard"))


# ==========================================
# PUBLIC CAMPAIGN LIST
# ==========================================

@app.route("/campaigns")
def campaigns():

    # Check whether the page should show one specific NGO's campaigns.

    ngo_id = request.args.get("ngo_id", type=int)
    selected_ngo = None

    if ngo_id is not None:

        selected_ngo = NGO.query.filter_by(
            id=ngo_id,
            status="approved"
        ).first()

        # Do not show campaigns for an unapproved or missing NGO.

        if not selected_ngo:
            abort(404)

    # Start with active campaigns belonging to approved NGOs.

    campaign_query = Campaign.query.join(NGO).filter(
        Campaign.status == "active",
        NGO.status == "approved"
    )

    # If an NGO was selected, show only that NGO's campaigns.

    if selected_ngo:
        campaign_query = campaign_query.filter(
            Campaign.ngo_id == selected_ngo.id
        )

    active_campaigns = campaign_query.order_by(
        Campaign.created_at.desc()
    ).all()

    return render_template(
        "campaigns.html",
        campaigns=active_campaigns,
        selected_ngo=selected_ngo
    )

def campaign_supply_summary(campaign):
    import re
    from collections import defaultdict

    requirements = []
    for line in (campaign.required_items or "").splitlines():
        match = re.match(r"^\s*(.+?)\s*:\s*(\d+)\s*$", line)
        if match and int(match.group(2)) > 0:
            requirements.append({
                "name": match.group(1).strip(),
                "required": int(match.group(2)),
            })

    accepted_by_name = defaultdict(int)
    committed_by_name = defaultdict(int)
    donations = Donation.query.filter_by(campaign_id=campaign.id).all()

    for donation in donations:
        # The in-kind tracker reflects physical donations only. Vendor-procurement
        # requests are tracked against product_catalog in campaign_procurement_summary.
        if donation.delivery_method == "vendor_procurement":
            continue
        if donation.status in {"cancelled", "rejected"}:
            continue
        for item in donation.items:
            key = normalize_supply_name(item.item_name)
            if donation.status == "verified" and item.accepted_qty is not None:
                accepted_by_name[key] += max(0, item.accepted_qty)
            elif donation.status in {"offered", "accepted", "awaiting_confirmation", "received"}:
                committed_by_name[key] += max(0, item.declared_qty or 0)

    result = []
    for need in requirements:
        key = normalize_supply_name(need["name"])
        required = need["required"]
        accepted = accepted_by_name[key]
        committed = committed_by_name[key]
        available = max(0, required - accepted - committed)
        percent = min(100, round(accepted * 100 / required))

        if accepted >= required:
            status = "Target reached"
        elif available == 0:
            status = "Fully committed — awaiting delivery"
        elif accepted / required >= 0.9:
            status = "Almost fulfilled"
        elif accepted:
            status = "In progress"
        else:
            status = "Needs supplies"

        result.append({
            "name": need["name"],
            "required": required,
            "accepted": accepted,
            "committed": committed,
            "available": available,
            "percent": percent,
            "status": status,
        })

    return result

# ==========================================
# PUBLIC CAMPAIGN DETAILS
# ==========================================

@app.route("/campaigns/<int:campaign_id>")
def campaign_detail(campaign_id):
    campaign = db.session.get(Campaign, campaign_id)
    if not campaign:
        abort(404)
    if campaign.status != "active":
        abort(404)
    if not campaign.ngo or campaign.ngo.status != "approved":
        abort(404)

    return render_template(
        "campaign_detail.html",
        campaign=campaign,
        supply_summary=campaign_supply_summary(campaign),
        products=campaign_product_options(campaign),
        inkind_products=campaign_inkind_options(campaign),
        packaging_steps=campaign_packaging_steps(campaign),
    )


# ==========================================
# NGO: CREATE CAMPAIGN
# ==========================================

@app.route("/campaigns/new", methods=["GET", "POST"])
@login_required
def create_campaign():
    require_role("ngo_staff")
    ngo = get_approved_ngo(current_user)
    if not ngo:
        flash("Your NGO must be approved before creating campaigns.", "error")
        return redirect(url_for("dashboard"))

    emergency_types = [
        "Natural disaster", "Food insecurity", "Infrastructure collapse",
        "Civil unrest humanitarian relief", "Emergency preparedness",
        "Other humanitarian emergency",
    ]

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        emergency_type = request.form.get("emergency_type", "").strip()
        location = request.form.get("location", "").strip()
        description = request.form.get("description", request.form.get("story_who_helping", "")).strip()
        required_items = request.form.get("required_items", "").strip()
        evidence_summary = request.form.get("evidence_summary", "").strip()
        evidence_url = request.form.get("evidence_url", "").strip()
        needs_source = request.form.get("needs_source", "").strip()

        if not all([title, emergency_type, location, description, required_items,
                    evidence_summary, evidence_url, needs_source]):
            flash("Complete all required campaign and evidence fields.", "error")
            return render_template("create_campaign.html", emergency_types=emergency_types), 400
        if emergency_type not in emergency_types:
            flash("Please select a valid emergency category.", "error")
            return render_template("create_campaign.html", emergency_types=emergency_types), 400
        if len(title) > 180 or len(location) > 200 or len(description) > 5000:
            flash("The title, location, or description exceeds its length limit.", "error")
            return render_template("create_campaign.html", emergency_types=emergency_types), 400
        if not evidence_url.lower().startswith(("https://", "http://")):
            flash("Enter a valid HTTP/HTTPS link for campaign evidence.", "error")
            return render_template("create_campaign.html", emergency_types=emergency_types), 400
        if len(evidence_summary) > 2000 or len(evidence_url) > 500 or len(needs_source) > 180:
            flash("One or more campaign evidence fields is too long.", "error")
            return render_template("create_campaign.html", emergency_types=emergency_types), 400
        try:
            parsed_requirements = parse_campaign_requirements(required_items)
            # Store units as part of the item name so existing inventory tracking
            # remains compatible with the current database schema.
            required_items = "\n".join(
                f"{item['name']}: {item['required']}" for item in parsed_requirements
            )
        except ValueError as error:
            flash(str(error), "error")
            return render_template("create_campaign.html", emergency_types=emergency_types), 400

        campaign = Campaign(
            title=title,
            emergency_type=emergency_type,
            location=location,
            description=description,
            required_items=required_items,
            status="pending",
            ngo_id=ngo.id,
            last_verified_at=datetime.utcnow(),
            evidence_summary=evidence_summary,
            evidence_url=evidence_url,
            needs_source=needs_source,
        )
        db.session.add(campaign)
        db.session.commit()
        flash("Campaign submitted for administrator approval.", "success")
        return redirect(url_for("dashboard"))

    return render_template("create_campaign.html", emergency_types=emergency_types)


# ==========================================
# ADMINISTRATOR: CAMPAIGN APPROVAL
# ==========================================

@app.route("/admin/campaigns/<int:campaign_id>/approve", methods=["POST"])
@login_required
def approve_campaign(campaign_id):
    require_role("admin")
    campaign = db.session.get(Campaign, campaign_id)
    if not campaign:
        abort(404)
    if not campaign.ngo or campaign.ngo.status != "approved":
        flash("The organisation must be approved first.", "error")
        return redirect(url_for("dashboard"))
    if not all([campaign.evidence_summary, campaign.evidence_url, campaign.needs_source]):
        flash("This campaign has not supplied all required evidence details.", "error")
        return redirect(url_for("dashboard"))
    if not campaign.evidence_url.lower().startswith(("https://", "http://")):
        flash("The campaign evidence link must use HTTP or HTTPS.", "error")
        return redirect(url_for("dashboard"))
    try:
        parse_campaign_requirements(campaign.required_items)
    except ValueError as error:
        flash(f"Campaign needs are not valid: {error}", "error")
        return redirect(url_for("dashboard"))

    location_checked = request.form.get("review_location_checked") == "on"
    requirements_checked = request.form.get("review_requirements_checked") == "on"
    evidence_checked = request.form.get("review_evidence_checked") == "on"
    review_notes = request.form.get("review_notes", "").strip()
    if not all([location_checked, requirements_checked, evidence_checked]):
        flash("Complete all three campaign checks before approving this campaign.", "error")
        return redirect(url_for("dashboard"))
    if not review_notes:
        flash("Add a short note describing the basis for this campaign review.", "error")
        return redirect(url_for("dashboard"))

    campaign.review_location_checked = location_checked
    campaign.review_requirements_checked = requirements_checked
    campaign.review_evidence_checked = evidence_checked
    campaign.review_notes = review_notes[:2000]
    campaign.reviewed_at = datetime.utcnow()
    campaign.status = "active"
    campaign.last_verified_at = datetime.utcnow()
    db.session.commit()
    flash("Campaign approved. The verification checklist has been recorded.", "success")
    return redirect(url_for("dashboard"))



@app.route(
    "/admin/campaigns/<int:campaign_id>/reject",
    methods=["POST"]
)
@login_required
def reject_campaign(campaign_id):

    require_role("admin")

    campaign = db.session.get(
        Campaign,
        campaign_id
    )

    if not campaign:
        abort(404)

    campaign.status = "rejected"

    db.session.commit()

    flash(
        "Campaign rejected.",
        "success"
    )

    return redirect(url_for("dashboard"))

# ==========================================
# DONATION HELPERS
# ==========================================

def generate_donation_code():
    """Generate a unique, hard-to-guess donation ID."""

    while True:
        code = f"UM-{secrets.token_hex(8).upper()}"

        if not Donation.query.filter_by(code=code).first():
            return code


def create_donation_qr(donation):
    """Generate a QR image linking to the donation record."""

    qr_directory = BASE_DIR / "static" / "qr_codes"

    qr_directory.mkdir(parents=True, exist_ok=True)

    configured_url = os.getenv(
        "UMEED_BASE_URL",
        ""
    ).strip().rstrip("/")

    base_url = configured_url or request.host_url.rstrip("/")

    donation_url = (
        base_url
        + url_for("scan_donation", code=donation.code)
    )

    qr_image = qrcode.make(donation_url)

    image_path = qr_directory / f"{donation.code}.png"

    qr_image.save(image_path)

    return url_for(
        "static",
        filename=f"qr_codes/{donation.code}.png"
    )


def get_qr_image_url(donation):
    """Return a QR image URL if its file exists."""

    image_path = (
        BASE_DIR
        / "static"
        / "qr_codes"
        / f"{donation.code}.png"
    )

    if image_path.exists():
        return url_for(
            "static",
            filename=f"qr_codes/{donation.code}.png"
        )

    return None


def collect_donation_items():
    """
    Read repeated item fields from a submitted donation form.

    Returns a list of validated item dictionaries.
    Raises ValueError for invalid input.
    """

    names = request.form.getlist("item_name")
    quantities = request.form.getlist("declared_qty")
    conditions = request.form.getlist("condition")

    rows = []

    if len(names) > 10:
        raise ValueError("A donation can contain at most 10 item types.")

    for index, raw_name in enumerate(names):

        name = raw_name.strip()

        quantity_text = (
            quantities[index].strip()
            if index < len(quantities)
            else ""
        )

        condition = (
            conditions[index].strip()
            if index < len(conditions)
            else "usable"
        )

        if not name and not quantity_text:
            continue

        if not name or not quantity_text:
            raise ValueError(
                "Enter both the item name and quantity."
            )

        try:
            quantity = int(quantity_text)
        except ValueError:
            raise ValueError(
                "Item quantities must be whole numbers."
            )

        if quantity < 1 or quantity > 10000:
            raise ValueError(
                "Each quantity must be between 1 and 10,000."
            )

        if condition not in {"good", "usable", "needs_review"}:
            raise ValueError(
                "Please select a valid item condition."
            )

        rows.append({
            "name": name,
            "quantity": quantity,
            "condition": condition
        })

    if not rows:
        raise ValueError(
            "Add at least one item to the donation."
        )

    return rows

def normalize_item_name(value):
    """Normalise item labels for safe, case-insensitive matching."""
    return " ".join((value or "").strip().casefold().split())


def parse_campaign_requirements(raw_text):
    """Parse needs such as 'Rice: 100', 'Rice: 100 kg', or 'Oil: 30 litres'.

    Units are stored with the item name (for example, 'Rice (kg)') so existing
    quantity tracking continues to work without a database migration.
    """
    requirements = []
    seen = set()

    unit_pattern = r"(kilograms?|kgs?|kg|grams?|g|litres?|liters?|l|millilitres?|milliliters?|ml|tonnes?|tons?|bags?|boxes?|packets?|packs?|bottles?|cans?|units?|pieces?|meals?)"

    for line_number, line in enumerate((raw_text or "").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue

        match = re.fullmatch(
            rf"(.{{1,120}}?)\s*:\s*(\d{{1,7}})(?:\s+{unit_pattern})?",
            line,
            flags=re.IGNORECASE,
        )
        if not match:
            raise ValueError(
                f"Requirement line {line_number} must use 'Item: quantity [unit]', "
                "for example 'Rice: 100 kg' or 'Blankets: 50 units'."
            )

        name = match.group(1).strip()
        quantity = int(match.group(2))
        unit = match.group(3)
        if unit:
            name = f"{name} ({unit})"

        key = normalize_supply_name(name)
        if not key:
            raise ValueError(f"Requirement line {line_number} has no item name.")
        if quantity < 1 or quantity > 1000000:
            raise ValueError("Each requirement must be between 1 and 1,000,000 units.")
        if key in seen:
            raise ValueError(f"The item '{name}' is listed more than once. Combine it into one line.")

        seen.add(key)
        requirements.append({
            "name": name,
            "key": normalize_supply_name(name),
            "required": quantity,
        })

    if not requirements:
        raise ValueError("Add at least one requirement using 'Item: quantity [unit]' on each line.")

    return requirements


def campaign_inventory(campaign):
    """Return each campaign need with accepted, committed, remaining and surplus quantities.

    For verified donations, only accepted quantities fulfil the requirement.
    Active offers and offline receipts awaiting final verification count as commitments.
    Cancelled/rejected donations are excluded.
    """
    try:
        requirements = parse_campaign_requirements(campaign.required_items)
    except ValueError:
        # Do not crash public pages for legacy campaigns with malformed free text.
        return []

    totals = {
        requirement["key"]: {"accepted": 0, "committed": 0}
        for requirement in requirements
    }

    donations = Donation.query.filter_by(campaign_id=campaign.id).all()
    for donation in donations:
        if donation.status in {"cancelled", "rejected"}:
            continue

        for item in donation.items:
            key = normalize_supply_name(item.item_name)
            if key not in totals:
                continue

            if donation.status == "verified":
                totals[key]["accepted"] += max(0, int(item.accepted_qty or 0))
            else:
                totals[key]["committed"] += max(0, int(item.declared_qty or 0))

    result = []
    for requirement in requirements:
        amount = totals[requirement["key"]]
        accounted_for = amount["accepted"] + amount["committed"]
        result.append({
            "name": requirement["name"],
            "key": requirement["key"],
            "required": requirement["required"],
            "accepted": amount["accepted"],
            "committed": amount["committed"],
            "remaining": max(0, requirement["required"] - accounted_for),
            "surplus": max(0, accounted_for - requirement["required"]),
        })
    return result


def validate_items_against_campaign(campaign, items_data, inventory=None):
    """Reject online pledges that do not match a listed need or exceed its balance."""
    inventory = inventory if inventory is not None else campaign_inventory(campaign)
    if not inventory:
        raise ValueError(
            "This campaign has no readable structured requirements. Ask the NGO to update its list."
        )

    by_key = {row["key"]: row for row in inventory}
    totals_requested = {}

    for row in items_data:
        key = normalize_supply_name(row["name"])
        if key not in by_key:
            raise ValueError(
                f"'{row['name']}' is not a listed requirement for this campaign. Select an item from the list."
            )
        totals_requested[key] = totals_requested.get(key, 0) + row["quantity"]
        # Store the canonical campaign spelling rather than arbitrary user input.
        row["name"] = by_key[key]["name"]

    for key, requested_quantity in totals_requested.items():
        need = by_key[key]
        if requested_quantity > need["remaining"]:
            raise ValueError(
                f"Only {need['remaining']} more unit(s) of {need['name']} can be pledged "
                f"right now; your form requests {requested_quantity}."
            )

    return items_data


def offline_surplus_warnings(campaign, items_data):
    """Warn about surplus/unlisted physical goods, but never block recording goods already received."""
    if not campaign:
        return []

    inventory = campaign_inventory(campaign)
    if not inventory:
        return ["This campaign's needs list could not be parsed; recorded goods need manual allocation."]

    by_key = {row["key"]: row for row in inventory}
    incoming = {}
    for row in items_data:
        key = normalize_supply_name(row["name"])
        incoming[key] = incoming.get(key, 0) + row["quantity"]

    warnings = []
    for key, quantity in incoming.items():
        need = by_key.get(key)
        if not need:
            warnings.append(
                f"{quantity} unit(s) of '{key}' are not on this campaign's needs list. "
                "The physical donation was recorded; allocate it manually."
            )
        elif quantity > need["remaining"]:
            excess = quantity - need["remaining"]
            warnings.append(
                f"Surplus flagged: {excess} extra unit(s) of {need['name']}. "
                "The physical donation was recorded and needs allocation review."
            )
    return warnings

def donation_access_allowed(donation):
    """Check whether the authenticated user can view a full record."""

    if not current_user.is_authenticated:
        return False

    if current_user.role == "admin":
        return True

    if (
        current_user.role == "donor"
        and donation.donor_id == current_user.id
    ):
        return True

    if (
        current_user.role == "ngo_staff"
        and current_user.ngo_id == donation.ngo_id
    ):
        return True

    return False


# ==========================================
# DONOR: REGISTER AN ONLINE DONATION
# ==========================================

@app.route("/campaigns/<int:campaign_id>/donate", methods=["GET", "POST"])
@login_required
def donate_to_campaign(campaign_id):
    require_role("donor")

    campaign = db.session.get(Campaign, campaign_id)
    if (
        not campaign
        or campaign.status != "active"
        or not campaign.ngo
        or campaign.ngo.status != "approved"
    ):
        abort(404)

    products = campaign_product_options(campaign)

    if request.method == "GET":
        return redirect(url_for("campaign_detail", campaign_id=campaign.id) + "#campaign-donations")

    phase = request.form.get("phase", "review").strip()

    try:
        # Recalculate quantities, availability, and totals on the server.
        items_data, total = get_selected_campaign_products(campaign)
    except ValueError as error:
        flash(str(error), "error")
        return redirect(
            url_for("campaign_detail", campaign_id=campaign.id) + "#campaign-donations"
        )

    if phase == "review":
        return render_template(
            "demo_checkout.html",
            campaign=campaign,
            items=items_data,
            total=total,
        )

    if phase != "confirm":
        abort(400)

    payment_method = request.form.get("payment_method", "upi").strip()
    if payment_method not in {"upi", "card", "netbanking"}:
        abort(400)

    # This records a pending vendor-procurement request only.
    # It does not represent a payment and does not call a payment provider.
    internal_note = (
        f"Vendor procurement request; displayed basket value ₹{total:,}; "
        f"selected checkout method: {payment_method}; payment is not processed. "
        "Supplies remain pending procurement and NGO receipt verification."
    )

    donation = Donation(
        code=generate_donation_code(),
        donor_id=current_user.id,
        created_by_id=current_user.id,
        ngo_id=campaign.ngo_id,
        campaign_id=campaign.id,
        source="online",
        status="offered",
        delivery_method="vendor_procurement",
        notes=internal_note,
    )
    db.session.add(donation)
    db.session.flush()

    for item_data in items_data:
        db.session.add(DonationItem(
            donation_id=donation.id,
            item_name=item_data["name"],
            declared_qty=item_data["quantity"],
            condition="good",
            received_qty=None,
            accepted_qty=None,
        ))

    record_event(
        donation,
        "offer_submitted",
        (
            f"Vendor-procurement request recorded for basket value ₹{total:,}. "
            "Items are pending procurement and NGO verification; no payment was processed."
        ),
        current_user.id,
    )
    db.session.commit()

    try:
        create_donation_qr(donation)
    except Exception:
        app.logger.exception("QR generation failed for %s", donation.code)

    flash(
        "Your contribution request has been recorded.",
        "success",
    )
    return redirect(url_for("donation_passport", code=donation.code))
  


# ==========================================
# DONOR: REGISTER A PHYSICAL IN-KIND DONATION
# ==========================================

@app.route("/campaigns/<int:campaign_id>/donate-in-kind", methods=["POST"])
@login_required
def donate_in_kind_to_campaign(campaign_id):
    require_role("donor")
    campaign = db.session.get(Campaign, campaign_id)
    if (
        not campaign
        or campaign.status != "active"
        or not campaign.ngo
        or campaign.ngo.status != "approved"
    ):
        abort(404)

    delivery_method = request.form.get("delivery_method", "drop_off").strip()
    if delivery_method not in {"drop_off", "collection_request"}:
        abort(400)

    products = campaign_inkind_options(campaign)
    if not products:
        flash("This campaign has no available physical supply needs yet.", "error")
        return redirect(url_for("campaign_detail", campaign_id=campaign.id) + "#campaign-donations")

    items_data = []
    requested_by_key = {}
    try:
        for product in products:
            raw = request.form.get(f"inkind_qty_{product['index']}", "0").strip()
            try:
                quantity = int(raw or "0")
            except ValueError:
                raise ValueError(f"Enter a whole-number quantity for {product['name']}.")
            if quantity < 0 or quantity > 10000:
                raise ValueError("Each physical supply quantity must be between 0 and 10,000.")
            available = max(0, int(product["available"]))
            if quantity > available:
                raise ValueError(f"Only {available} more unit(s) of {product['name']} are listed as available.")
            if quantity == 0:
                continue
            key = normalize_supply_name(product["name"])
            requested_by_key[key] = requested_by_key.get(key, 0) + quantity
            items_data.append({
                "name": product["name"],
                "quantity": quantity,
                "condition": "good",
            })
    except ValueError as error:
        flash(str(error), "error")
        return redirect(url_for("campaign_detail", campaign_id=campaign.id) + "#campaign-donations")

    if not items_data:
        flash("Choose a quantity for at least one physical supply.", "error")
        return redirect(url_for("campaign_detail", campaign_id=campaign.id) + "#campaign-donations")

    # Refresh the database snapshot immediately before creating the commitment.
    # The current prototype does not reserve stock transactionally across concurrent requests.
    inventory = {normalize_supply_name(row["name"]): row for row in campaign_supply_summary(campaign)}
    for key, quantity in requested_by_key.items():
        need = inventory.get(key)
        if not need or quantity > int(need["available"]):
            available = int(need["available"]) if need else 0
            flash(f"Availability changed. Only {available} unit(s) remain for this item; please review your quantities.", "error")
            return redirect(url_for("campaign_detail", campaign_id=campaign.id) + "#campaign-donations")

    delivery_label = "donor drop-off" if delivery_method == "drop_off" else "pickup requested; awaiting NGO confirmation"
    donation = Donation(
        code=generate_donation_code(),
        donor_id=current_user.id,
        created_by_id=current_user.id,
        ngo_id=campaign.ngo_id,
        campaign_id=campaign.id,
        source="online",
        status="offered",
        delivery_method=delivery_method,
        notes=f"Physical in-kind donation. Delivery preference: {delivery_label}.",
    )
    db.session.add(donation)
    db.session.flush()
    for item_data in items_data:
        db.session.add(DonationItem(
            donation_id=donation.id,
            item_name=item_data["name"],
            declared_qty=item_data["quantity"],
            condition="good",
            received_qty=None,
            accepted_qty=None,
        ))

    event_note = "Physical in-kind supply offer submitted."
    if delivery_method == "collection_request":
        event_note += " Pickup requested; this request is not yet confirmed."
    else:
        event_note += " Donor plans to deliver the supplies."
    record_event(donation, "inkind_offer_submitted", event_note, current_user.id)
    db.session.commit()

    try:
        create_donation_qr(donation)
    except Exception:
        app.logger.exception("QR generation failed for physical donation %s", donation.code)

    flash("Your physical in-kind donation has been registered. You can print its QR label from the Donation Passport.", "success")
    return redirect(url_for("donation_passport", code=donation.code))


# ==========================================
# NGO: VIEW INCOMING DONATIONS
# ==========================================

@app.route("/ngo/donations")
@login_required
def ngo_donations():

    require_role("ngo_staff")

    ngo = get_approved_ngo(current_user)

    if not ngo:
        flash(
            "Your NGO must be approved to manage donations.",
            "error"
        )

        return redirect(url_for("dashboard"))

    donations = Donation.query.filter_by(
        ngo_id=ngo.id
    ).order_by(
        Donation.created_at.desc()
    ).all()

    return render_template(
        "ngo_donations.html",
        donations=donations,
        ngo=ngo
    )


# ==========================================
# NGO: REGISTER AN OFFLINE DONATION
# ==========================================

@app.route(
    "/ngo/donations/offline",
    methods=["GET", "POST"]
)
@login_required
def offline_donation():

    require_role("ngo_staff")

    ngo = get_approved_ngo(current_user)

    if not ngo:
        flash(
            "Your NGO must be approved first.",
            "error"
        )

        return redirect(url_for("dashboard"))

    active_campaigns = Campaign.query.filter_by(
        ngo_id=ngo.id,
        status="active"
    ).order_by(
        Campaign.created_at.desc()
    ).all()

    if request.method == "POST":

        try:
            items_data = collect_donation_items()
        except ValueError as error:
            flash(str(error), "error")

            return render_template(
                "offline_donation.html",
                campaigns=active_campaigns
            ), 400

        campaign_id_text = request.form.get(
            "campaign_id",
            ""
        ).strip()

        campaign = None

        if campaign_id_text:

            try:
                campaign_id = int(campaign_id_text)
            except ValueError:
                abort(400)

            campaign = db.session.get(
                Campaign,
                campaign_id
            )

            if (
                not campaign
                or campaign.ngo_id != ngo.id
                or campaign.status != "active"
            ):
                flash(
                    "Select one of your active campaigns.",
                    "error"
                )

                return render_template(
                    "offline_donation.html",
                    campaigns=active_campaigns
                ), 400
        surplus_warnings = offline_surplus_warnings(campaign, items_data)

        donation = Donation(
            code=generate_donation_code(),
            donor_id=None,
            created_by_id=current_user.id,
            ngo_id=ngo.id,
            campaign_id=campaign.id if campaign else None,
            source="offline",
            status="received",
            delivery_method="drop_off",
            notes="Offline walk-in donation."
        )

        db.session.add(donation)

        db.session.flush()

        for item_data in items_data:

            item = DonationItem(
                donation_id=donation.id,
                item_name=item_data["name"],
                declared_qty=item_data["quantity"],
                condition=item_data["condition"],
                received_qty=None,
                accepted_qty=None
            )

            db.session.add(item)

        record_event(
            donation,
            "offline_registered",
            "NGO staff registered a walk-in donation.",
            current_user.id
        )

        db.session.commit()

        try:
            create_donation_qr(donation)
        except Exception:
            app.logger.exception(
                "QR generation failed for %s",
                donation.code
            )

        flash(
            "Offline donation registered. Verify the quantities received.",
            "success"
        )

        for warning in surplus_warnings:
            flash(warning, "warning")

        return redirect(
            url_for(
                "verify_donation",
                code=donation.code
            )
        )

    return render_template(
        "offline_donation.html",
        campaigns=active_campaigns
    )


# ==========================================
# NGO: ACCEPT AN ONLINE DONATION OFFER
# ==========================================

@app.route(
    "/ngo/donations/<code>/accept",
    methods=["POST"]
)
@login_required
def accept_donation_offer(code):

    require_role("ngo_staff")

    ngo = get_approved_ngo(current_user)

    if not ngo:
        abort(403)

    donation = Donation.query.filter_by(
        code=code,
        ngo_id=ngo.id
    ).first_or_404()

    if donation.status != "offered":

        flash(
            "This donation offer is no longer awaiting acceptance.",
            "error"
        )

        return redirect(url_for("ngo_donations"))

    donation.status = "accepted"

    record_event(
        donation,
        "offer_accepted",
        "NGO accepted the donation offer.",
        current_user.id
    )

    db.session.commit()

    flash(
        "Donation offer accepted.",
        "success"
    )

    return redirect(url_for("ngo_donations"))


# ==========================================
# NGO: VERIFY RECEIVED QUANTITIES
# ==========================================

@app.route(
    "/ngo/donations/<code>/verify",
    methods=["GET", "POST"]
)
@login_required
def verify_donation(code):

    require_role("ngo_staff")

    ngo = get_approved_ngo(current_user)

    if not ngo:
        abort(403)

    donation = Donation.query.filter_by(
        code=code,
        ngo_id=ngo.id
    ).first_or_404()

    if donation.status in {"cancelled", "rejected"}:
        abort(400)

    if request.method == "POST":

        if donation.status == "verified":

            flash(
                "This donation has already been verified.",
                "error"
            )

            return redirect(
                url_for(
                    "donation_passport",
                    code=donation.code
                )
            )

        verified_items = []

        # Validate every item before changing the database.

        for item in donation.items:

            received_text = request.form.get(
                f"received_{item.id}",
                ""
            ).strip()

            accepted_text = request.form.get(
                f"accepted_{item.id}",
                ""
            ).strip()

            rejection_reason = request.form.get(
                f"reason_{item.id}",
                ""
            ).strip()

            try:
                received_qty = int(received_text)
                accepted_qty = int(accepted_text)
            except ValueError:

                flash(
                    f"Enter valid quantities for {item.item_name}.",
                    "error"
                )

                return render_template(
                    "verify_donation.html",
                    donation=donation,
                    read_only=False
                ), 400

            if received_qty < 0 or accepted_qty < 0:

                flash(
                    "Quantities cannot be negative.",
                    "error"
                )

                return render_template(
                    "verify_donation.html",
                    donation=donation,
                    read_only=False
                ), 400

            if accepted_qty > received_qty:

                flash(
                    f"Accepted quantity cannot exceed received quantity for {item.item_name}.",
                    "error"
                )

                return render_template(
                    "verify_donation.html",
                    donation=donation,
                    read_only=False
                ), 400

            if received_qty > 10000:

                flash(
                    "Received quantities cannot exceed 10,000 per item.",
                    "error"
                )

                return render_template(
                    "verify_donation.html",
                    donation=donation,
                    read_only=False
                ), 400

            if received_qty > accepted_qty and not rejection_reason:

                flash(
                    f"Explain why some {item.item_name} were rejected.",
                    "error"
                )

                return render_template(
                    "verify_donation.html",
                    donation=donation,
                    read_only=False
                ), 400

            if len(rejection_reason) > 250:

                flash(
                    "Rejection reasons must be under 250 characters.",
                    "error"
                )

                return render_template(
                    "verify_donation.html",
                    donation=donation,
                    read_only=False
                ), 400

            verified_items.append({
                "item": item,
                "received": received_qty,
                "accepted": accepted_qty,
                "reason": rejection_reason
            })

        # Apply validated changes.

        event_lines = []

        for entry in verified_items:

            item = entry["item"]

            item.received_qty = entry["received"]
            item.accepted_qty = entry["accepted"]
            item.rejection_reason = entry["reason"]

            rejected_qty = (
                entry["received"] - entry["accepted"]
            )

            line = (
                f"{item.item_name}: "
                f"declared {item.declared_qty}, "
                f"received {entry['received']}, "
                f"accepted {entry['accepted']}, "
                f"rejected {rejected_qty}"
            )

            if entry["reason"]:
                line += f" (Reason: {entry['reason']})"

            event_lines.append(line)

        donation.status = "verified"
        donation.received_at = datetime.utcnow()

        record_event(
            donation,
            "intake_verified",
            "; ".join(event_lines),
            current_user.id
        )

        db.session.commit()

        flash(
            "Receipt verified. The Donation Passport has been updated.",
            "success"
        )

        return redirect(
            url_for(
                "donation_passport",
                code=donation.code
            )
        )

    return render_template(
        "verify_donation.html",
        donation=donation,
        read_only=(donation.status == "verified")
    )


# ==========================================
# NGO: RECORD A PROCESSING OR DISTRIBUTION STAGE
# ==========================================

@app.route(
    "/ngo/donations/<code>/stage",
    methods=["POST"]
)
@login_required
def update_donation_stage(code):

    require_role("ngo_staff")

    ngo = get_approved_ngo(current_user)

    if not ngo:
        abort(403)

    donation = Donation.query.filter_by(
        code=code,
        ngo_id=ngo.id
    ).first_or_404()

    if donation.delivery_method == "vendor_procurement":
        flash("Use the product progress controls for vendor-procured contributions.", "info")
        return redirect(url_for("donation_passport", code=donation.code))

    if donation.status != "verified":
        flash(
            "Verify the donation before recording later stages.",
            "error"
        )

        return redirect(
            url_for(
                "donation_passport",
                code=donation.code
            )
        )

    allowed_stages = {
        "sorted",
        "allocated",
        "dispatched",
        "delivery_confirmed",
        "distribution_reported"
    }

    stage = request.form.get("stage", "").strip()

    batch_code = request.form.get(
        "batch_code",
        ""
    ).strip()

    note = request.form.get(
        "note",
        ""
    ).strip()

    if stage not in allowed_stages:
        abort(400)

    if not batch_code or len(batch_code) > 80:
        flash(
            "Enter a valid batch reference.",
            "error"
        )

        return redirect(
            url_for(
                "donation_passport",
                code=donation.code
            )
        )

    if len(note) > 500:
        flash(
            "The note must be under 500 characters.",
            "error"
        )

        return redirect(
            url_for(
                "donation_passport",
                code=donation.code
            )
        )

    event_note = f"Batch {batch_code}."

    if note:
        event_note += f" {note}"

    record_event(
        donation,
        stage,
        event_note,
        current_user.id
    )

    db.session.commit()

    flash(
        "Donation processing update recorded.",
        "success"
    )

    return redirect(
        url_for(
            "donation_passport",
            code=donation.code
        )
    )

# ==========================================
# NGO: RECORD VENDOR-PROCUREMENT PROGRESS
# ==========================================

@app.route("/ngo/donations/<code>/procurement-stage", methods=["POST"])
@login_required
def update_procurement_stage(code):
    require_role("ngo_staff")
    ngo = get_approved_ngo(current_user)
    if not ngo:
        abort(403)

    donation = Donation.query.filter_by(code=code, ngo_id=ngo.id).first_or_404()
    if donation.delivery_method != "vendor_procurement":
        abort(400)
    if donation.status in {"cancelled", "rejected"}:
        flash("Cancelled or rejected requests cannot be progressed.", "error")
        return redirect(url_for("donation_passport", code=donation.code))

    stage = request.form.get("stage", "").strip()
    note = request.form.get("note", "").strip()
    allowed_stages = {
        "procurement_started", "procured", "sorted", "allocated",
        "dispatched", "delivery_confirmed", "distribution_reported",
        "reached_recipients",
    }
    if stage not in allowed_stages:
        abort(400)
    if len(note) > 500:
        flash("The update note must be 500 characters or fewer.", "error")
        return redirect(url_for("donation_passport", code=donation.code))

    distribution_stages = {"distribution_reported", "reached_recipients"}
    if stage in distribution_stages and donation.status != "verified":
        flash("Confirm delivery and accepted quantities before recording distribution.", "error")
        return redirect(url_for("donation_passport", code=donation.code))

    event_note = note
    if stage == "delivery_confirmed" and donation.status != "verified":
        # The authorised staff member is confirming that every selected quantity has arrived
        # and is accepted. If quantities differ, do not use this action; record the issue first.
        now = datetime.utcnow()
        for item in donation.items:
            item.received_qty = int(item.declared_qty or 0)
            item.accepted_qty = int(item.declared_qty or 0)
            item.rejection_reason = ""
        donation.status = "verified"
        donation.received_at = now
        event_note = (
            "NGO confirmed delivery and acceptance of all selected quantities. "
            + (note if note else "")
        ).strip()

    record_event(donation, stage, event_note, current_user.id)
    db.session.commit()
    flash("Product progress update recorded.", "success")
    return redirect(url_for("donation_passport", code=donation.code))


@app.route("/ngo/donations/<code>/quick-update", methods=["POST"])
@login_required
def qr_quick_update(code):
    require_role("ngo_staff")
    ngo = get_approved_ngo(current_user)
    if not ngo:
        abort(403)

    donation = Donation.query.filter_by(code=code, ngo_id=ngo.id).first_or_404()
    if donation.delivery_method == "vendor_procurement":
        flash("Use the product progress controls for vendor-procured contributions.", "info")
        return redirect(url_for("donation_passport", code=code))

    action = request.form.get("action", "").strip()
    note = request.form.get("note", "").strip()
    people_text = request.form.get("people_assisted", "").strip()
    if len(note) > 500:
        flash("Optional note must be 500 characters or fewer.", "error")
        return redirect(url_for("donation_passport", code=code))

    if action == "received":
        if donation.status == "verified":
            flash("This physical donation has already been verified.", "info")
            return redirect(url_for("donation_passport", code=code))
        return redirect(url_for("verify_donation", code=code))

    if action == "distributed":
        if donation.status != "verified":
            flash("Verify received and accepted quantities before distribution.", "error")
            return redirect(url_for("donation_passport", code=code))
        if any(event.event_type == "distribution_reported" for event in donation.events):
            flash("Distribution has already been recorded for this donation.", "error")
            return redirect(url_for("donation_passport", code=code))

        people = None
        if people_text:
            try:
                people = int(people_text)
                if not 0 <= people <= 1000000:
                    raise ValueError
            except ValueError:
                flash("People assisted must be a whole number from 0 to 1,000,000.", "error")
                return redirect(url_for("donation_passport", code=code))

        details = "Distribution recorded by authorised NGO staff."
        if people is not None:
            details += f" People assisted (reported): {people}."
        if note:
            details += f" Note: {note}"
        record_event(donation, "distribution_reported", details, current_user.id)
        db.session.commit()
        flash("Distribution event recorded.", "success")
        return redirect(url_for("donation_passport", code=code))

    abort(400)


# ==========================================
# DONOR: CANCEL AN UNFULFILLED OFFER
# ==========================================

@app.route(
    "/donations/<code>/cancel",
    methods=["POST"]
)
@login_required
def cancel_donation(code):

    require_role("donor")

    donation = Donation.query.filter_by(
        code=code,
        donor_id=current_user.id
    ).first_or_404()

    if donation.status not in {"offered", "accepted"}:

        flash(
            "This donation can no longer be cancelled through the website.",
            "error"
        )

        return redirect(
            url_for(
                "donation_passport",
                code=donation.code
            )
        )

    donation.status = "cancelled"

    record_event(
        donation,
        "cancelled",
        "Donor cancelled the donation offer.",
        current_user.id
    )

    db.session.commit()

    flash(
        "Donation offer cancelled.",
        "success"
    )

    return redirect(
        url_for(
            "donation_passport",
            code=donation.code
        )
    )


# ==========================================
# DONOR: VIEW A PRIVATE DONATION PASSPORT
# ==========================================

@app.route("/donations/<code>/passport")
@login_required
def donation_passport(code):

    donation = Donation.query.filter_by(
        code=code
    ).first_or_404()

    if not donation_access_allowed(donation):
        abort(403)

    return render_template(
        "donation_passport.html",
        donation=donation,
        events=donation.events,
        public_view=False,
        can_manage=(
            current_user.role == "ngo_staff"
            and current_user.ngo_id == donation.ngo_id
        ),
        qr_image_url=get_qr_image_url(donation)
    )


# ==========================================
# QR: OPEN THE DONATION RECORD
# ==========================================

@app.route("/scan/<code>")
def scan_donation(code):
    donation = Donation.query.filter_by(code=code).first_or_404()

    if current_user.is_authenticated and current_user.role == "ngo_staff" and current_user.ngo_id == donation.ngo_id:
        if donation.delivery_method != "vendor_procurement" and donation.status != "verified":
            return redirect(url_for("verify_donation", code=donation.code))
        return redirect(url_for("donation_passport", code=donation.code))

    if (current_user.is_authenticated and current_user.role == "donor"
            and current_user.id == donation.donor_id):
        return redirect(url_for("donation_passport", code=donation.code))

    if current_user.is_authenticated and current_user.role == "admin":
        return redirect(url_for("donation_passport", code=donation.code))

    # Public QR access is read-only; passport template hides private information.
    return render_template(
        "donation_passport.html",
        donation=donation,
        events=donation.events,
        public_view=True,
        can_manage=False,
        qr_image_url=get_qr_image_url(donation),
    )


# ==========================================
# NGO: LOOK UP DONATION USING PRINTED ID
# ==========================================

@app.route("/ngo/donations/lookup")
@login_required
def lookup_donation():

    require_role("ngo_staff")

    ngo = get_approved_ngo(current_user)

    if not ngo:

        flash(
            "Your NGO must be approved before managing donations.",
            "error"
        )

        return redirect(url_for("dashboard"))

    code = request.args.get("code", "").strip().upper()

    if not code:

        flash(
            "Enter the donation ID printed on the box.",
            "error"
        )

        return redirect(url_for("ngo_donations"))

    donation = Donation.query.filter_by(
        code=code,
        ngo_id=ngo.id
    ).first()

    if not donation:

        flash(
            "No donation with that ID was found for your organisation.",
            "error"
        )

        return redirect(url_for("ngo_donations"))

    if donation.status in {
        "verified",
        "cancelled",
        "rejected"
    }:

        return redirect(
            url_for(
                "donation_passport",
                code=donation.code
            )
        )

    return redirect(
        url_for(
            "verify_donation",
            code=donation.code
        )
    )
# ==========================================
# PUBLIC LIST OF AFFILIATED NGOS
# ==========================================

@app.route("/affiliated-ngos")
def affiliated_ngos():

    approved_ngos = NGO.query.filter_by(
        status="approved"
    ).order_by(
        NGO.name.asc()
    ).all()

    return render_template(
        "affiliated_ngos.html",
        ngos=approved_ngos
    )

# ==========================================
# NGO: VIEW OWN CAMPAIGNS
# ==========================================

@app.route("/ngo/campaigns")
@login_required
def ngo_campaigns():

    require_role("ngo_staff")

    ngo = get_approved_ngo(current_user)

    if not ngo:

        flash(
            "Your NGO must be approved to manage campaigns.",
            "error"
        )

        return redirect(url_for("dashboard"))

    campaigns = Campaign.query.filter_by(
        ngo_id=ngo.id
    ).order_by(
        Campaign.created_at.desc()
    ).all()

    return render_template(
        "ngo_campaigns.html",
        ngo=ngo,
        campaigns=campaigns
    )

# ==========================================
# NGO: EDIT AN EXISTING CAMPAIGN
# ==========================================

@app.route(
    "/ngo/campaigns/<int:campaign_id>/edit",
    methods=["GET", "POST"]
)
@login_required
def edit_campaign(campaign_id):
    require_role("ngo_staff")
    ngo = get_approved_ngo(current_user)
    if not ngo:
        abort(403)

    campaign = Campaign.query.filter_by(
        id=campaign_id,
        ngo_id=ngo.id
    ).first_or_404()

    emergency_types = [
        "Natural disaster",
        "Food insecurity",
        "Infrastructure collapse",
        "Civil unrest humanitarian relief",
        "Emergency preparedness",
        "Other humanitarian emergency",
    ]

    form_values = request.form if request.method == "POST" else {}

    # Build editor rows from the stored catalogue on GET. On a failed POST,
    # rebuild from submitted fields so validation errors do not erase user input.
    if request.method == "POST":
        product_names = request.form.getlist("product_name")
        product_quantities = request.form.getlist("product_required_qty")
        product_prices = request.form.getlist("product_unit_price")
        product_image_urls = request.form.getlist("product_image_url")
        product_rows = []
        for i, name in enumerate(product_names):
            product_rows.append({
                "name": name,
                "required_qty": product_quantities[i] if i < len(product_quantities) else "1",
                "unit_price": product_prices[i] if i < len(product_prices) else "0",
                "image_url": product_image_urls[i] if i < len(product_image_urls) else "",
            })
        inkind_names = request.form.getlist("inkind_name")
        inkind_quantities = request.form.getlist("inkind_required_qty")
        inkind_rows = [
            {"name": name, "required_qty": inkind_quantities[i] if i < len(inkind_quantities) else "1"}
            for i, name in enumerate(inkind_names)
        ]
    else:
        try:
            product_rows = parse_product_catalog(campaign.product_catalog or DEFAULT_PRODUCT_CATALOG)
        except ValueError:
            app.logger.exception("Invalid product catalogue for campaign %s", campaign.id)
            product_rows = parse_product_catalog(DEFAULT_PRODUCT_CATALOG)

        inkind_rows = []
        for line in (campaign.required_items or "").splitlines():
            if not line.strip():
                continue
            match = re.fullmatch(r"\s*(.+?)\s*:\s*(\d+)\s*", line)
            if match:
                inkind_rows.append({"name": match.group(1).strip(), "required_qty": match.group(2)})

    product_catalog_value = form_values.get("product_catalog", campaign.product_catalog or DEFAULT_PRODUCT_CATALOG)

    def render_editor(status=200):
        return render_template(
            "edit_campaign.html",
            campaign=campaign,
            emergency_types=emergency_types,
            form_values=form_values,
            product_catalog_value=product_catalog_value,
            product_rows=product_rows,
            inkind_rows=inkind_rows,
            carousel_defaults=DEFAULT_CAROUSEL_IMAGES,
            default_products_intro=DEFAULT_PRODUCTS_INTRO,
            default_in_kind_intro=DEFAULT_IN_KIND_INTRO,
            default_packaging_steps=DEFAULT_PACKAGING_STEPS,
        ), status

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        emergency_type = request.form.get("emergency_type", "").strip()
        location = request.form.get("location", "").strip()
        description = (request.form.get("description")or request.form.get("story_who_helping")or "").strip()
        card_overview = request.form.get("card_overview", "").strip()
        listing_image_url = request.form.get("listing_image_url", "").strip()

        story_who_helping = request.form.get("story_who_helping", "").strip()
        story_urgency = request.form.get("story_urgency", "").strip()
        story_mission = request.form.get("story_mission", "").strip()
        story_impact = request.form.get("story_impact", "").strip()
        images = [request.form.get(f"carousel_image_{index}", "").strip() for index in range(1, 4)]
        products_intro = request.form.get("products_intro", "").strip()
        in_kind_intro = request.form.get("in_kind_intro", "").strip()
        packaging_steps = request.form.get("packaging_steps", "").strip()

        required_fields = {
            "title": title,
            "emergency_type": emergency_type,
            "location": location,
            "description": description,
            "card_overview": card_overview,
        }
        missing_fields = [name for name, value in required_fields.items() if not value]

        if missing_fields:
            app.logger.warning(
                "Edit campaign validation failed. Missing fields: %s",
                missing_fields,
            )
            flash(
                "Missing submitted fields: " + ", ".join(missing_fields),
                "error",
            )
            return render_editor(400)

        if len(title) > 180 or len(location) > 200:
            flash("The title must be at most 180 characters and the location at most 200 characters.", "error")
            return render_editor(400)
        if emergency_type not in emergency_types:
            flash("Select a valid campaign category.", "error")
            return render_editor(400)
        if not 200 <= len(card_overview) <= 300:
            flash("The campaign overview must contain 200–300 characters.", "error")
            return render_editor(400)
        if any(len(value) > 5000 for value in [description, story_who_helping, story_urgency, story_mission, story_impact, products_intro, in_kind_intro]):
            flash("Descriptions and tab instructions must be 5,000 characters or fewer.", "error")
            return render_editor(400)
        for image_url in [listing_image_url, *images]:
            if image_url and not image_url.startswith(("https://", "http://", "/static/")):
                flash("Images must use HTTP/HTTPS URLs or a /static/ path.", "error")
                return render_editor(400)
            if len(image_url) > 1000:
                flash("An image URL is too long.", "error")
                return render_editor(400)

        steps = [step.strip() for step in packaging_steps.splitlines() if step.strip()]
        if len(steps) != 4:
            flash("Enter exactly four packaging instructions, one instruction per line.", "error")
            return render_editor(400)
        if any(len(step) > 1000 for step in steps):
            flash("Each packaging instruction must be 1,000 characters or fewer.", "error")
            return render_editor(400)

        # Serialize the individual product form rows into the format used by the
        # donor page and procurement tracker. This fixes the empty-editor mismatch.
        try:
            if len(product_rows) > 20:
                raise ValueError("A campaign can have at most 20 product types.")
            serialized_products = []
            seen_product_names = set()
            for i, row in enumerate(product_rows):
                name = row["name"].strip()
                qty_text = str(row["required_qty"]).strip()
                price_text = str(row["unit_price"]).strip()
                image_url = str(row["image_url"] or "").strip()
                if not name or len(name) > 120:
                    raise ValueError(f"Enter a product name of 1–120 characters on row {i + 1}.")
                if name.casefold() in seen_product_names:
                    raise ValueError(f"The product '{name}' appears more than once.")
                seen_product_names.add(name.casefold())
                qty = int(qty_text)
                price = int(price_text)
                if not 0 <= qty <= 1000000 or not 0 <= price <= 10000000:
                    raise ValueError("Product quantities and prices are outside the allowed range.")
                if image_url and not image_url.startswith(("https://", "http://", "/static/")):
                    raise ValueError(f"Use an HTTP/HTTPS URL or /static/ path for the image for {name}.")
                upload = request.files.get(f"product_image_{i}")
                if upload and upload.filename:
                    image_url = save_product_image(upload, campaign.id, i) or image_url
                serialized_products.append(f"{name}|{qty}|{price}|{image_url}")
            if not serialized_products:
                raise ValueError("Add at least one product to the Donate Products catalogue.")
            product_catalog_value = "\n".join(serialized_products)
            # Re-parse for consistent validation with the existing catalogue parser.
            parse_product_catalog(product_catalog_value)
        except (ValueError, TypeError) as error:
            flash(str(error) or "Check the product rows.", "error")
            return render_editor(400)

        # In-kind items use the existing required_items storage and tracker.
        try:
            if len(inkind_rows) > 30:
                raise ValueError("A campaign can have at most 30 physical item types.")
            raw_inkind = "\n".join(
                f"{row['name'].strip()}: {str(row['required_qty']).strip()}"
                for row in inkind_rows if row["name"].strip()
            )
            parsed_inkind = parse_campaign_requirements(raw_inkind)
            required_items_value = "\n".join(
                f"{item['name']}: {item['required']}" for item in parsed_inkind
            )
        except (ValueError, TypeError) as error:
            flash(str(error), "error")
            return render_editor(400)

        campaign.title = title
        campaign.emergency_type = emergency_type
        campaign.location = location
        campaign.description = description
        campaign.card_overview = card_overview
        campaign.listing_image_url = listing_image_url
        campaign.story_who_helping = story_who_helping
        campaign.story_urgency = story_urgency
        campaign.story_mission = story_mission
        campaign.story_impact = story_impact
        campaign.carousel_image_1, campaign.carousel_image_2, campaign.carousel_image_3 = images
        campaign.products_intro = products_intro
        campaign.in_kind_intro = in_kind_intro
        campaign.packaging_steps = "\n".join(steps)
        campaign.product_catalog = product_catalog_value
        campaign.required_items = required_items_value
        campaign.last_verified_at = datetime.utcnow()
        db.session.commit()

        flash("Campaign details, images, vendor products, and physical in-kind needs have been saved.", "success")
        return redirect(url_for("edit_campaign", campaign_id=campaign.id))

    return render_editor()

# ==========================================
# NGO: CLOSE AN ACTIVE CAMPAIGN
# ==========================================

@app.route(
    "/ngo/campaigns/<int:campaign_id>/close",
    methods=["POST"]
)
@login_required
def close_campaign(campaign_id):

    require_role("ngo_staff")

    ngo = get_approved_ngo(current_user)

    if not ngo:
        abort(403)

    campaign = Campaign.query.filter_by(
        id=campaign_id,
        ngo_id=ngo.id
    ).first_or_404()

    if campaign.status != "active":

        flash(
            "Only active campaigns can be closed.",
            "error"
        )

        return redirect(url_for("ngo_campaigns"))

    campaign.status = "closed"

    db.session.commit()

    flash(
        f"Campaign '{campaign.title}' has been closed.",
        "success"
    )

    return redirect(url_for("ngo_campaigns"))

# ==========================================
# NGO: EDIT OWN PROFILE
# ==========================================

@app.route(
    "/ngo/profile",
    methods=["GET", "POST"]
)
@login_required
def edit_ngo_profile():

    require_role("ngo_staff")

    ngo = current_user.ngo

    if not ngo:
        abort(404)

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        location = request.form.get(
            "location",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        if not name or not location or not description:

            flash(
                "Please complete all profile fields.",
                "error"
            )

            return render_template(
                "ngo_profile.html",
                ngo=ngo
            ), 400

        if (
            len(name) > 150
            or len(location) > 200
            or len(description) > 600
        ):

            flash(
                "The name, location, or description exceeds the allowed length.",
                "error"
            )

            return render_template(
                "ngo_profile.html",
                ngo=ngo
            ), 400

        ngo.name = name
        ngo.location = location
        ngo.description = description

        db.session.commit()

        flash(
            "Your NGO profile has been updated.",
            "success"
        )

        return redirect(url_for("ngo_campaigns"))

    return render_template(
        "ngo_profile.html",
        ngo=ngo
    )
# ==========================================
# ERROR HANDLERS
# ==========================================

@app.errorhandler(403)
def forbidden(_error):

    return (
        "Access denied. Your account does not have permission for this action.",
        403
    )


@app.errorhandler(404)
def not_found(_error):

    return (
        "The requested page or record was not found.",
        404
    )


# ==========================================
# DATABASE INITIALISATION
# ==========================================

with app.app_context():

    db.create_all()

    # Safely add the NGO description column to an existing SQLite database.
    # db.create_all() creates missing tables but does not add missing columns.

    ngo_table_name = NGO.__table__.name

    existing_ngo_columns = {
        column["name"]
        for column in inspect(db.engine).get_columns(ngo_table_name)
    }

    if "description" not in existing_ngo_columns:

        with db.engine.begin() as connection:

            connection.execute(
                text(
                    f'ALTER TABLE "{ngo_table_name}" '
                    'ADD COLUMN description TEXT'
                )
            )


    # Add campaign editor columns to an existing database.
    # This preserves existing campaign records.

    campaign_editor_columns = [
        "story_who_helping",
        "story_urgency",
        "story_mission",
        "story_impact",
        "carousel_image_1",
        "carousel_image_2",
        "carousel_image_3",
        "products_intro",
        "in_kind_intro",
        "packaging_steps",
        "product_catalog",
        "card_overview",
        "listing_image_url",
    ]

    existing_campaign_columns = {
        column["name"]
        for column in inspect(db.engine).get_columns("campaigns")
    }

    for column_name in campaign_editor_columns:

        if column_name not in existing_campaign_columns:

            with db.engine.begin() as connection:
                connection.execute(
                    text(
                        f'ALTER TABLE "campaigns" '
                        f'ADD COLUMN "{column_name}" TEXT'
                    )
                )

            existing_campaign_columns.add(column_name)

    # Local demonstration administrator.
    # Change these credentials before public deployment.

    admin_email = os.getenv(
        "UMEED_ADMIN_EMAIL",
        "umeed@admin.com"
    ).strip().lower()

    admin_password = os.getenv(
        "UMEED_ADMIN_PASSWORD",
        "umeed1234"
    )

    existing_admin = User.query.filter_by(
        email=admin_email
    ).first()

    if not existing_admin:

        admin = User(
            name="Umeed Administrator",
            email=admin_email,
            role="admin"
        )

        admin.set_password(admin_password)

        db.session.add(admin)

        db.session.commit()
    # Add new review fields to existing SQLite or PostgreSQL databases.
    # db.create_all() creates missing tables but does not add columns.
    def ensure_table_columns(table_name, additions):
        existing = {
            column["name"]
            for column in inspect(db.engine).get_columns(table_name)
        }
        for column_name, sql_type in additions.items():
            if column_name not in existing:
                with db.engine.begin() as connection:
                    connection.execute(
                        text(
                            f'ALTER TABLE "{table_name}" '
                            f'ADD COLUMN "{column_name}" {sql_type}'
                        )
                    )

    ensure_table_columns("ngos", {
        "legal_form": "VARCHAR(60)",
        "registration_number": "VARCHAR(120)",
        "registration_authority": "VARCHAR(150)",
        "evidence_url": "VARCHAR(500)",
        "review_registration_checked": "BOOLEAN NOT NULL DEFAULT FALSE",
        "review_address_checked": "BOOLEAN NOT NULL DEFAULT FALSE",
        "review_contact_checked": "BOOLEAN NOT NULL DEFAULT FALSE",
        "review_notes": "TEXT",
        "reviewed_at": "TIMESTAMP NULL",
    })

    ensure_table_columns("campaigns", {
        "evidence_summary": "TEXT",
        "evidence_url": "VARCHAR(500)",
        "needs_source": "VARCHAR(180)",
        "review_location_checked": "BOOLEAN NOT NULL DEFAULT FALSE",
        "review_requirements_checked": "BOOLEAN NOT NULL DEFAULT FALSE",
        "review_evidence_checked": "BOOLEAN NOT NULL DEFAULT FALSE",
        "review_notes": "TEXT",
        "reviewed_at": "TIMESTAMP NULL",
    })       


    # Replace only the exact earlier prototype default catalogue with the new
    # seven-item Donate Products defaults. Do not modify required_items (physical in-kind).
    migrated_catalogues = 0
    for existing_campaign in Campaign.query.all():
        saved_catalogue = (existing_campaign.product_catalog or "").strip()
        if not saved_catalogue or saved_catalogue == LEGACY_DEFAULT_PRODUCT_CATALOG.strip():
            if saved_catalogue != DEFAULT_PRODUCT_CATALOG.strip():
                existing_campaign.product_catalog = DEFAULT_PRODUCT_CATALOG
                migrated_catalogues += 1
    if migrated_catalogues:
        db.session.commit()


# ==========================================
# RUN APPLICATION
# ==========================================

if __name__ == "__main__":

    app.run(debug=True)