import os
from pathlib import Path
from datetime import datetime, timezone, timedelta
import secrets
import qrcode

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

app.config["SQLALCHEMY_DATABASE_URI"] = (
    "sqlite:///" + str(BASE_DIR / "umeed.db")
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

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

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get("password", "")

        account_type = request.form.get(
            "account_type",
            "donor"
        )

        # Basic form validation

        if not name or not email or not password:

            flash(
                "Please complete all required fields.",
                "error"
            )

            return render_template("register.html")

        if len(password) < 8:

            flash(
                "Your password must contain at least 8 characters.",
                "error"
            )

            return render_template("register.html")

        if account_type not in {"donor", "ngo"}:

            flash(
                "Invalid account type.",
                "error"
            )

            return render_template("register.html")

        # Prevent duplicate accounts

        existing_user = User.query.filter_by(
            email=email
        ).first()

        if existing_user:

            flash(
                "An account with this email already exists.",
                "error"
            )

            return render_template("register.html")

        # Create user account

        user = User(
            name=name,
            email=email
        )

        user.set_password(password)

        # Create an NGO registration if requested.
        # NGO descriptions are displayed on the public Affiliated NGOs page.

        if account_type == "ngo":

            ngo_name = request.form.get(
                "ngo_name",
                ""
            ).strip()

            ngo_location = request.form.get(
                "ngo_location",
                ""
            ).strip()

            ngo_description = request.form.get(
                "ngo_description",
                ""
            ).strip()

            if not ngo_name or not ngo_location or not ngo_description:

                flash(
                    "NGO name, location, and description are required.",
                    "error"
                )

                return render_template("register.html"), 400

            if len(ngo_name) > 180:

                flash(
                    "The NGO name must be 180 characters or fewer.",
                    "error"
                )

                return render_template("register.html"), 400

            if len(ngo_location) > 180:

                flash(
                    "The NGO location must be 180 characters or fewer.",
                    "error"
                )

                return render_template("register.html"), 400

            if len(ngo_description) > 600:

                flash(
                    "The NGO description must be 600 characters or fewer.",
                    "error"
                )

                return render_template("register.html"), 400

            ngo = NGO(
                name=ngo_name,
                email=email,
                location=ngo_location,
                description=ngo_description,
                status="pending"
            )

            db.session.add(ngo)

            # Assign the database ID before linking the user.

            db.session.flush()

            user.role = "ngo_staff"
            user.ngo = ngo

        else:

            user.role = "donor"

        db.session.add(user)

        db.session.commit()

        login_user(user)

        if user.role == "ngo_staff":

            flash(
                "Your NGO registration is awaiting administrator approval.",
                "success"
            )

        else:

            flash(
                "Your account has been created successfully.",
                "success"
            )

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

    ngo.status = "approved"

    db.session.commit()

    flash(
        f"{ngo.name} has been approved.",
        "success"
    )

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

# ==========================================
# PUBLIC CAMPAIGN DETAILS
# ==========================================

@app.route("/campaigns/<int:campaign_id>")
def campaign_detail(campaign_id):

    campaign = db.session.get(
        Campaign,
        campaign_id
    )

    if not campaign:
        abort(404)

    # Only active campaigns are publicly accessible.

    if campaign.status != "active":
        abort(404)

    # Only campaigns belonging to approved NGOs are public.

    if not campaign.ngo or campaign.ngo.status != "approved":
        abort(404)

    return render_template(
        "campaign_detail.html",
        campaign=campaign
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

        flash(
            "Your NGO must be approved before creating campaigns.",
            "error"
        )

        return redirect(url_for("dashboard"))

    emergency_types = [
        "Natural disaster",
        "Food insecurity",
        "Infrastructure collapse",
        "Civil unrest",
        "Emergency preparedness"
    ]

    if request.method == "POST":

        title = request.form.get(
            "title",
            ""
        ).strip()

        emergency_type = request.form.get(
            "emergency_type",
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

        required_items = request.form.get(
            "required_items",
            ""
        ).strip()

        if not all([
            title,
            emergency_type,
            location,
            description,
            required_items
        ]):

            flash(
                "Please complete all required fields.",
                "error"
            )

        elif emergency_type not in emergency_types:

            flash(
                "Please select a valid emergency category.",
                "error"
            )

        else:

            campaign = Campaign(
                title=title,
                emergency_type=emergency_type,
                location=location,
                description=description,
                required_items=required_items,
                status="pending",
                ngo_id=ngo.id,
                last_verified_at=datetime.utcnow()
            )

            db.session.add(campaign)

            db.session.commit()

            flash(
                "Campaign submitted for administrator approval.",
                "success"
            )

            return redirect(url_for("dashboard"))

    return render_template(
        "create_campaign.html",
        emergency_types=emergency_types
    )


# ==========================================
# ADMINISTRATOR: CAMPAIGN APPROVAL
# ==========================================

@app.route(
    "/admin/campaigns/<int:campaign_id>/approve",
    methods=["POST"]
)
@login_required
def approve_campaign(campaign_id):

    require_role("admin")

    campaign = db.session.get(
        Campaign,
        campaign_id
    )

    if not campaign:
        abort(404)

    if not campaign.ngo or campaign.ngo.status != "approved":

        flash(
            "The organisation must be approved first.",
            "error"
        )

        return redirect(url_for("dashboard"))

    campaign.status = "active"
    campaign.last_verified_at = datetime.utcnow()

    db.session.commit()

    flash(
        "Campaign approved and published.",
        "success"
    )

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

@app.route(
    "/campaigns/<int:campaign_id>/donate",
    methods=["GET", "POST"]
)
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

    if request.method == "POST":

        try:
            items_data = collect_donation_items()
        except ValueError as error:
            flash(str(error), "error")

            return render_template(
                "donation_form.html",
                campaign=campaign
            ), 400

        delivery_method = request.form.get(
            "delivery_method",
            "drop_off"
        )

        if delivery_method not in {
            "drop_off",
            "collection_request"
        }:
            flash("Select a valid delivery method.", "error")

            return render_template(
                "donation_form.html",
                campaign=campaign
            ), 400

        notes = request.form.get("notes", "").strip()

        if len(notes) > 1000:
            flash("Notes must be under 1,000 characters.", "error")

            return render_template(
                "donation_form.html",
                campaign=campaign
            ), 400

        donation = Donation(
            code=generate_donation_code(),
            donor_id=current_user.id,
            created_by_id=current_user.id,
            ngo_id=campaign.ngo_id,
            campaign_id=campaign.id,
            source="online",
            status="offered",
            delivery_method=delivery_method,
            notes=notes
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
            "offer_submitted",
            "Donor submitted a donation offer.",
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
            "Your donation offer has been registered.",
            "success"
        )

        return redirect(
            url_for(
                "donation_passport",
                code=donation.code
            )
        )

    return render_template(
        "donation_form.html",
        campaign=campaign
    )


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

    donation = Donation.query.filter_by(
        code=code
    ).first_or_404()

    # The associated NGO can open intake verification directly.

    if (
        current_user.is_authenticated
        and current_user.role == "ngo_staff"
        and current_user.ngo_id == donation.ngo_id
        and donation.status != "verified"
    ):

        return redirect(
            url_for(
                "verify_donation",
                code=donation.code
            )
        )

    # Owners see their full Donation Passport.

    if (
        current_user.is_authenticated
        and current_user.role == "donor"
        and current_user.id == donation.donor_id
    ):

        return redirect(
            url_for(
                "donation_passport",
                code=donation.code
            )
        )

    if (
        current_user.is_authenticated
        and (
            current_user.role == "admin"
            or (
                current_user.role == "ngo_staff"
                and current_user.ngo_id == donation.ngo_id
            )
        )
    ):

        return redirect(
            url_for(
                "donation_passport",
                code=donation.code
            )
        )

    # A QR link acts as a read-only receipt.
    # No donor email, phone number, or other personal data is exposed.

    return render_template(
        "donation_passport.html",
        donation=donation,
        events=donation.events,
        public_view=True,
        can_manage=False,
        qr_image_url=get_qr_image_url(donation)
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

    # Local demonstration administrator.
    # Change these credentials before public deployment.

    admin_email = os.getenv(
        "UMEED_ADMIN_EMAIL",
        "admin@umeed.local"
    ).strip().lower()

    admin_password = os.getenv(
        "UMEED_ADMIN_PASSWORD",
        "UmeedAdmin123!"
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


# ==========================================
# RUN APPLICATION
# ==========================================

if __name__ == "__main__":

    app.run(debug=True)