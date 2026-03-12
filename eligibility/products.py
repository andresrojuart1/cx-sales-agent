"""Product definitions and metadata for the CX Sales Agent tool."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Product:
    key: str
    name: str
    description: str
    pitch: str
    color_eligible: str
    color_using: str
    color_ineligible: str


PRODUCTS = {
    "quick": Product(
        key="quick",
        name="Quick",
        description="Earned wage advance program",
        pitch="Get access to your earned wages before payday — no interest, just a small flat fee.",
        color_eligible="#22c55e",
        color_using="#6b7280",
        color_ineligible="#ef4444",
    ),
    "future_fund": Product(
        key="future_fund",
        name="Future Fund",
        description="Investment product",
        pitch="Grow your money with Future Fund — invest automatically from your wallet balance.",
        color_eligible="#22c55e",
        color_using="#6b7280",
        color_ineligible="#ef4444",
    ),
    "tapi": Product(
        key="tapi",
        name="Tapi",
        description="Pay your bills service",
        pitch="Pay all your bills directly from your Ontop wallet — utilities, phone, internet and more.",
        color_eligible="#22c55e",
        color_using="#6b7280",
        color_ineligible="#ef4444",
    ),
    "esim": Product(
        key="esim",
        name="e-Sim",
        description="Digital SIM card product",
        pitch="Stay connected anywhere — get an e-Sim with data plans for 100+ countries, right from the app.",
        color_eligible="#22c55e",
        color_using="#6b7280",
        color_ineligible="#ef4444",
    ),
    "reserve": Product(
        key="reserve",
        name="Reserve",
        description="Visa debit card benefits with cashback and preferred discounts",
        pitch="Upgrade to Reserve — earn cashback on every purchase and unlock exclusive discounts.",
        color_eligible="#22c55e",
        color_using="#6b7280",
        color_ineligible="#ef4444",
    ),
}

PRODUCT_KEYS = list(PRODUCTS.keys())
PRODUCT_NAMES = {p.key: p.name for p in PRODUCTS.values()}
PRODUCT_ESTIMATED_MRR = {
    "quick": 11.9,
    "future_fund": 3.0,
    "reserve": 14.9,
    "tapi": 1.6,
    "esim": 5.0,
}
