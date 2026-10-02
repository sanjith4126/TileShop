"""
Draft guides and policy pages for the owner to review. Everything here is
saved UNPUBLISHED — nothing is visible on the site until the owner checks
it and ticks "is published" in the admin.

Policy drafts state only what the website's code actually does; everything
else is marked [OWNER TO CONFIRM].
"""
from django.db import migrations

DRAFT_NOTE = (
    "<p><em>Draft for owner review — not yet published. Check every section, replace the parts "
    "marked [OWNER TO CONFIRM], and remove this note before publishing.</em></p>\n"
)

GUIDES = [
    {
        "slug": "ceramic-vs-porcelain-tiles",
        "title": "Ceramic vs Porcelain Tiles: What's the Difference?",
        "category": "floor-tiles",
        "summary": (
            "Porcelain tiles are denser and absorb less water than ceramic tiles, so they suit busy floors "
            "and wet areas. Ceramic tiles are lighter and easier to cut, and work well on walls and in "
            "rooms with lighter foot traffic."
        ),
        "body": """<p><strong>Short answer:</strong> porcelain tiles are made from a finer clay mix fired at a higher temperature, so they are denser and absorb very little water (0.5% or less). That makes them harder-wearing and a better choice for busy floors, bathrooms and outdoor areas. Ceramic tiles absorb more water, are lighter and easier to cut, and work well on walls and in rooms with lighter foot traffic.</p>
<h2>How they are made</h2>
<p>Both are made from clay fired in a kiln. Porcelain uses a finer, purer clay mix fired at higher temperatures, which produces a dense body. Ceramic tiles use a coarser clay body fired at lower temperatures and are usually glazed on top.</p>
<h2>Water absorption</h2>
<p>Tiles are classified by how much water they absorb. Porcelain tiles absorb 0.5% or less, which is why they cope well in bathrooms, wet areas and outdoors. Ceramic tiles absorb more — many wall tiles absorb over 10%.</p>
<h2>Strength and wear</h2>
<p>Porcelain's denser body resists chipping and wear better, so it is a common choice for living rooms, shops and other busy floors. For glazed tiles, the PEI rating on the box shows how well the surface resists wear: PEI 3 suits most home floors, and PEI 4 suits busy homes and light commercial use.</p>
<h2>Cutting and laying</h2>
<p>Ceramic tiles are softer and easier to cut, which can make laying quicker. Porcelain needs sharper tools and more care, especially in large sizes.</p>
<h2>Which should you choose?</h2>
<ul>
<li><strong>Living room and bedroom floors:</strong> either works; porcelain lasts longer in busy homes.</li>
<li><strong>Bathroom floors:</strong> porcelain, ideally with a matt or textured finish for grip.</li>
<li><strong>Bathroom and kitchen walls:</strong> ceramic is a practical, cost-effective choice.</li>
<li><strong>Outdoor and parking areas:</strong> choose tiles made for outdoor use, such as parking tiles.</li>
</ul>
<p>Browse our <a href="/products/floor-tiles/">floor tiles</a> — each product page lists its material — or <a href="/inquiry/">ask us</a> which tile suits your room.</p>""",
    },
    {
        "slug": "choosing-floor-tile-size",
        "title": "How to Choose the Right Floor Tile Size",
        "category": "floor-tiles",
        "summary": (
            "Larger tiles such as 60 × 60 cm mean fewer grout lines and a calmer, more spacious look; "
            "smaller tiles are easier to slope towards drains and give more grip. Large-format tiles "
            "need a very flat floor."
        ),
        "body": """<p><strong>Short answer:</strong> for most living rooms and bedrooms, 60 × 60 cm (about 2 × 2 ft) or larger tiles give a clean look with fewer grout lines. In small bathrooms and around floor drains, smaller tiles are easier to slope and give more grip. Large-format tiles such as 60 × 120 cm need a very flat floor and an experienced tiler.</p>
<h2>Common floor tile sizes</h2>
<ul>
<li><strong>30 × 30 cm (about 1 × 1 ft):</strong> bathrooms, balconies and small spaces.</li>
<li><strong>60 × 60 cm (about 2 × 2 ft):</strong> the most common size for living rooms, bedrooms and halls.</li>
<li><strong>60 × 120 cm (about 2 × 4 ft):</strong> large-format tiles for open spaces and a near-seamless look.</li>
</ul>
<h2>Does a small room need small tiles?</h2>
<p>Not necessarily. Larger tiles have fewer grout lines, which can make a small room look bigger and calmer. What matters more is how many cuts the room needs: very large tiles in a room with many corners can mean a lot of cutting and waste.</p>
<h2>Bathrooms and wet areas</h2>
<p>Bathroom floors usually slope towards a drain. Smaller tiles follow that slope more easily, and the extra grout lines add grip underfoot. If you prefer larger tiles, choose a matt or textured finish.</p>
<h2>Large-format tiles</h2>
<p>Tiles of 60 × 120 cm and bigger need a flat, well-prepared floor. On an uneven floor they can rock, or their edges can sit higher than the next tile (called lippage). Ask your tiler whether your floor is suitable.</p>
<h2>Work out how many you need</h2>
<p>Use our <a href="/tile-calculator/">tile calculator</a> to turn your room size into a number of tiles, including extra for cutting. You can also <a href="/room-visualizer/">see a tile in your own room</a> before you buy.</p>
<p>Browse <a href="/products/floor-tiles/">floor tiles</a>, or <a href="/inquiry/">ask us</a> for advice on your room.</p>""",
    },
    {
        "slug": "matt-vs-glossy-bathroom-tiles",
        "title": "Matt vs Glossy Tiles for Bathrooms",
        "category": "bathroom-tiles",
        "summary": (
            "Use matt or textured tiles on bathroom floors because they are less slippery when wet. "
            "Glossy tiles reflect light and wipe clean easily, which suits bathroom walls."
        ),
        "body": """<p><strong>Short answer:</strong> use matt or textured tiles on bathroom floors, because they are less slippery when wet. Glossy tiles reflect light and are easy to wipe, so they work well on bathroom walls. Combining the two — glossy walls with a matt floor — is a common, practical choice.</p>
<h2>Safety underfoot</h2>
<p>Water makes any smooth surface slippery. Matt and textured finishes give your feet more grip. If a tile's slip resistance is stated — for example an R rating such as R10 or R11, where a higher number means more grip, or the label "anti-skid" — check it before choosing a floor tile for a wet area.</p>
<h2>Light and space</h2>
<p>Glossy tiles reflect light, which can make a small bathroom feel brighter and larger. Matt tiles give a softer look and hide water spots and smudges better.</p>
<h2>Cleaning</h2>
<p>Glossy tiles wipe clean easily but show water marks and soap residue. Matt tiles hide marks, but textured surfaces can hold dirt, so they need regular cleaning with a soft brush.</p>
<h2>What we suggest</h2>
<ul>
<li><strong>Floors and shower areas:</strong> matt or textured tiles.</li>
<li><strong>Walls:</strong> glossy for a bright, easy-to-clean finish, or matt for a softer look.</li>
</ul>
<p>See our <a href="/products/bathroom-tiles/">bathroom tiles</a>, or <a href="/inquiry/">ask us</a> to help you pick a matching floor and wall tile.</p>""",
    },
]

PAGES = [
    {
        "slug": "privacy-policy",
        "title": "Privacy Policy",
        "meta": "How Suwasthick Tiles collects and uses the details you give us when you order, ask for a quote or use the room visualizer.",
        "body": DRAFT_NOTE + """<h2>Who we are</h2>
<p>This website is run by Suwasthick Tiles, Bhavani, Tamil Nadu. For privacy questions, contact us at [OWNER TO CONFIRM: email and phone].</p>
<h2>What we collect</h2>
<ul>
<li><strong>Orders:</strong> your name, email address, phone number, delivery address, any notes you add, and the payment method you choose. We do not take card or UPI details online; payment is collected at delivery.</li>
<li><strong>Quote requests:</strong> your name, email address, phone number, location, project details (tiles, area, project type and message) and, if you tell us, the professional who referred you.</li>
<li><strong>Accounts:</strong> if you create an account, your username and your password, which is stored only in hashed form.</li>
<li><strong>Room Visualizer:</strong> when you use the AI room visualizer, the photo you upload and the selected tile image are sent to Google's Gemini API to create the visualization. The website does not save your photo. [OWNER TO CONFIRM: check Google's current data-use terms for your Gemini API plan.]</li>
<li><strong>Cookies:</strong> we use essential cookies to keep your cart and login working (session cookie) and to protect our forms (CSRF cookie). [OWNER TO CONFIRM: describe analytics cookies here if you turn analytics on.]</li>
</ul>
<h2>How we use it</h2>
<p>To process and deliver your order, to contact you about your order or quote, and to answer your questions. [OWNER TO CONFIRM: any other uses.]</p>
<h2>Who we share it with</h2>
<p>[OWNER TO CONFIRM: delivery partners or anyone else you share customer details with.]</p>
<h2>How long we keep it</h2>
<p>[OWNER TO CONFIRM]</p>
<h2>Your choices</h2>
<p>You can ask us to see, correct or delete your personal details by contacting us at [OWNER TO CONFIRM].</p>""",
    },
    {
        "slug": "terms-of-sale",
        "title": "Terms of Sale",
        "meta": "Terms for orders placed with Suwasthick Tiles: prices, order confirmation and payment on delivery.",
        "body": DRAFT_NOTE + """<h2>Prices</h2>
<p>Prices are shown in Indian rupees (₹) per square foot on each product page. [OWNER TO CONFIRM: whether prices include GST, and the selling unit — square foot, box or piece — for each product.]</p>
<h2>Placing an order</h2>
<p>After you place an order on this website, we call you to confirm it. [OWNER TO CONFIRM: what happens if an item is unavailable or the quantity changes.]</p>
<h2>Payment</h2>
<p>Payment is collected at the time of delivery by UPI, credit card, debit card, cheque or cash. Nothing is charged online.</p>
<h2>Delivery</h2>
<p>See our delivery policy. [OWNER TO CONFIRM]</p>
<h2>Cancellations</h2>
<p>[OWNER TO CONFIRM: how and until when an order can be cancelled.]</p>
<h2>Returns and breakage</h2>
<p>See our returns and breakage policy.</p>""",
    },
    {
        "slug": "delivery-policy",
        "title": "Delivery Policy",
        "meta": "Where and how Suwasthick Tiles delivers tile and sanitaryware orders.",
        "body": DRAFT_NOTE + """<h2>Where we deliver</h2>
<p>[OWNER TO CONFIRM: towns and districts you deliver to.]</p>
<h2>Delivery time</h2>
<p>[OWNER TO CONFIRM]</p>
<h2>Delivery charges</h2>
<p>[OWNER TO CONFIRM]</p>
<h2>Unloading</h2>
<p>[OWNER TO CONFIRM: whether unloading and carrying to the site are included.]</p>
<h2>Checking your tiles</h2>
<p>Please check the boxes when they arrive and tell us about any damage straight away. [OWNER TO CONFIRM: how and by when to report damage.]</p>""",
    },
    {
        "slug": "returns-and-breakage",
        "title": "Returns & Breakage Policy",
        "meta": "How Suwasthick Tiles handles returns and tiles damaged in delivery.",
        "body": DRAFT_NOTE + """<h2>Damaged on delivery</h2>
<p>[OWNER TO CONFIRM: how breakage found on delivery is handled.]</p>
<h2>Returning unused tiles</h2>
<p>[OWNER TO CONFIRM: whether unopened boxes can be returned, within how many days, and any charges.]</p>
<h2>Tiles that have been cut or laid</h2>
<p>[OWNER TO CONFIRM]</p>""",
    },
    {
        "slug": "warranty",
        "title": "Warranty",
        "meta": "What the Suwasthick Tiles quality warranty covers and how to make a claim.",
        "body": DRAFT_NOTE + """<h2>What is covered</h2>
<p>[OWNER TO CONFIRM: what the 10-year quality warranty covers, and whether it is provided by Suwasthick Tiles or by the manufacturer.]</p>
<h2>What is not covered</h2>
<p>[OWNER TO CONFIRM]</p>
<h2>How to make a claim</h2>
<p>[OWNER TO CONFIRM]</p>""",
    },
]


def create_drafts(apps, schema_editor):
    Guide = apps.get_model("content", "Guide")
    Page = apps.get_model("content", "Page")
    Category = apps.get_model("core", "Category")
    for data in GUIDES:
        if not Guide.objects.filter(slug=data["slug"]).exists():
            Guide.objects.create(
                slug=data["slug"], title=data["title"], summary=data["summary"], body=data["body"],
                related_category=Category.objects.filter(slug=data["category"]).first(),
                is_published=False,
            )
    for data in PAGES:
        if not Page.objects.filter(slug=data["slug"]).exists():
            Page.objects.create(
                slug=data["slug"], title=data["title"], meta_description=data["meta"],
                body=data["body"], is_published=False,
            )


def remove_drafts(apps, schema_editor):
    apps.get_model("content", "Guide").objects.filter(slug__in=[g["slug"] for g in GUIDES], is_published=False).delete()
    apps.get_model("content", "Page").objects.filter(slug__in=[p["slug"] for p in PAGES], is_published=False).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0001_initial"),
        ("core", "0004_prefill_business_info"),
    ]

    operations = [
        migrations.RunPython(create_drafts, remove_drafts),
    ]
