"""
Fill the business-info record with the contact details the site already showed
(footer and About page), so nothing visible changes. They stay unconfirmed
(details_confirmed=False) until the owner checks them in the admin.
"""
from django.db import migrations

CURRENT_SITE_VALUES = {
    "address": "Opp. Kalyana Mandabam, Bhavani, Erode Dt, Tamil Nadu",
    "street_address": "Opp. Kalyana Mandabam",
    "locality": "Bhavani",
    "region": "Tamil Nadu",
    "country": "IN",
    "phone": "+91 98765 43210",
    "email": "studio@suwasthick.com",
    "opening_hours": "Mon–Sat, 9 AM to 7 PM",
    "details_confirmed": False,
}


def prefill(apps, schema_editor):
    BusinessInfo = apps.get_model("core", "BusinessInfo")
    if not BusinessInfo.objects.filter(pk=1).exists():
        BusinessInfo.objects.create(pk=1, **CURRENT_SITE_VALUES)


def remove(apps, schema_editor):
    apps.get_model("core", "BusinessInfo").objects.filter(pk=1).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0003_business_info_and_category_slug"),
    ]

    operations = [
        migrations.RunPython(prefill, remove),
    ]
