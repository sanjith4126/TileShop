"""
Orders models.
"""
from django.db import models
from django.contrib.auth.models import User
from apps.products.models import Product


class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("processing", "Processing"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    ]

    PAYMENT_METHOD_CHOICES = [
        ("upi", "UPI (on delivery)"),
        ("credit_card", "Credit Card (on delivery)"),
        ("debit_card", "Debit Card (on delivery)"),
        ("cheque", "Cheque (on delivery)"),
        ("cash", "Cash (on delivery)"),
    ]

    # Optional account link — guests can order without logging in
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, related_name="orders",
        null=True, blank=True,
    )

    # Customer contact details (collected like the quote form)
    full_name = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_address = models.TextField(blank=True)
    payment_method = models.CharField(
        max_length=20, choices=PAYMENT_METHOD_CHOICES, default="cash",
        help_text="Payment is collected at the time of delivery.",
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        who = self.full_name or (self.user.username if self.user else "Guest")
        return f"Order #{self.pk} - {who}"

    def calculate_total(self):
        self.total_price = sum(item.subtotal for item in self.items.all())
        self.save()


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"

    @property
    def subtotal(self):
        if self.unit_price is None or self.quantity is None:
            return 0
        return self.unit_price * self.quantity
