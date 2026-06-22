import re
from difflib import SequenceMatcher


# Keyword rules are checked first, then fuzzy matching is used as fallback.
CATEGORY_RULES = {
    "Food": {
        "Restaurant": [
            "cafe coffee day",
            "zomato",
            "swiggy",
            "ubereats",
            "dominos",
            "pizza hut",
            "mcdonald",
            "burger king",
            "kfc",
            "starbucks",
            "barbeque nation",
            "curefit",
            "eatfit",
            "chaayos",
            "freshmenu",
            "box8",
            "faasos",
            "behrouz",
            "subway",
            "haldiram",
            "bikanervala",
            "world of veg",
            "bamboos family garden",
            "ananthi wines",
            "truffles hospitality",
            "sherlocks pub",
            "barbeque nation hospit",
            "raidan restaurant",
            "the rasoi",
            "diverse retails",
            "food",
            "cafe",
            "restaurant",
        ],
        "Grocery": ["bigbasket", "grofers", "dmart"],
    },
    "Automobile": {
        "Fuel": ["petrol", "diesel", "kamod and company"],
        "Maintenance": [
            "isuzu",
            "toyota",
            "subaru",
            "mitsubishi",
            "mahindra",
            "tesla",
            "scion",
            "saab",
            "force",
            "bmw",
            "suzuki",
            "dodge",
            "alfa romeo",
            "aston martin",
            "fiat",
            "lexus",
            "jaguar",
            "genesis",
            "datsun",
            "pontiac",
            "chevrolet",
            "renault",
            "volvo",
            "skoda",
            "plymouth",
            "hyundai",
            "ford",
            "acura",
            "buick",
            "volkswagen",
            "lamborghini",
            "nissan",
            "spyker",
            "smart",
            "maserati",
            "infiniti",
            "bugatti",
            "ferrari",
            "mercedes benz",
            "mercedesbenz",
            "mclaren",
            "mazda",
            "maruti",
            "cadillac",
            "mini",
            "land rover",
            "jeep",
            "honda",
            "gmc",
            "kia",
            "lotus",
            "oldsmobile",
            "hummer",
            "lincoln",
            "porsche",
            "chrysler",
            "rolls royce",
            "maybach",
            "bentley",
            "tata",
            "ambassador",
            "audi",
        ],
        "Insurance": ["icicilombard", "bajajallianz", "acko"],
    },
    "Travel": {
        "Taxi": [
            "uber",
            "ola",
            "rapido",
            "zaak",
            "blusmart",
            "meru",
            "cab",
            "taxi",
            "ride",
        ],
        "Fuel": [
            "indian oil",
            "bharat petroleum",
            "hpcl",
            "shell",
            "petrol",
            "diesel",
            "fuel",
            "cng",
        ],
        "Transit": [
            "irctc",
            "redbus",
            "abhibus",
            "makemytrip",
            "goibibo",
            "yatra",
            "air india",
            "indigo",
            "vistara",
            "airasia",
            "spicejet",
            "metro",
            "fastag",
            "toll",
        ],
        "Airplane": ["airasia", "air india", "indigo", "spicejet"],
        "Train": ["irctc"],
    },
    "Utilities": {
        "Telephone": [
            "vodafone",
            "vi",
            "airtel",
            "jio",
            "bsnl",
            "mobile recharge",
            "recharge",
            "postpaid",
            "prepaid",
        ],
        "Internet": [
            "actcorp",
            "act fibernet",
            "jiomoney",
            "jiofiber",
            "airtel broadband",
            "hathway",
            "you broadband",
            "wifi",
            "broadband",
            "internet",
        ],
        "Electricity": [
            "bescom",
            "mseb",
            "tneb",
            "electricity",
            "power bill",
            "torrent power",
            "tata power",
            "adani electricity",
        ],
        "Gas": ["indane", "hp gas", "bharat gas", "gas bill", "lpg", "bpcl", "bpcl r n gupta brother"],
        "Electric": ["bescom", "mseb"],
        "Water": ["water bill", "bwssb", "municipal water"],
    },
    "Personal": {
        "Clothing": [
            "myntra",
            "ajio",
            "nykaa fashion",
            "hm",
            "zara",
            "lifestyle",
            "pantaloons",
            "max fashion",
            "shoppers stop",
            "clothing",
            "apparel",
        ],
        "Grooming": [
            "nykaa",
            "purplle",
            "sephora",
            "salon",
            "barber",
            "spa",
            "beauty",
        ],
        "Personal Care": ["nykaa"],
        "Others": [
            "dunzo",
            "blinkit",
            "zepto",
            "instamart",
            "bigbasket",
            "grofers",
            "amazon",
            "flipkart",
            "meesho",
            "jiomart",
            "one97",
            "paytm",
            "phonepe",
            "gpay",
            "google pay",
            "supermarket",
            "mart",
            "store",
            "govind dande and sons",
            "p n gadgil and sons",
            "nike",
        ],
    },
    "Home Office": {
        "Other": [
            "linkedin",
            "resume",
            "zety",
            "amazon internet",
            "godaddy",
            "namecheap",
            "digitalocean",
            "linode",
            "notion",
            "slack",
            "zoom",
            "github",
            "atlassian",
            "canva",
            "figma",
            "adobe",
            "chatgpt",
            "openai",
            "claude",
            "workspace",
            "office",
        ]
    },
    "Entertainment": {
        "Other": ["itunes", "netflix"],
        "Streaming": [
            "itunes",
            "netflix",
            "prime video",
            "amazon prime",
            "hotstar",
            "disney",
            "spotify",
            "youtube premium",
            "gaana",
            "jiosaavn",
            "sony liv",
            "zee5",
        ],
        "Movies": ["bookmyshow", "pvr", "inox", "cinepolis", "movie"],
        "Gaming": ["steam", "playstation", "xbox", "epic games", "game"],
    },
    "Household": {
        "Rent": ["rent", "house rent", "flat rent", "lease"],
        "Maintenance": ["society", "maintenance", "apartment", "rwa"],
        "Furniture": [
            "ikea",
            "pepperfry",
            "urban ladder",
            "urbanladder",
            "home centre",
            "kieraya furnishing",
            "furniture",
        ],
        "Maintenance Services": ["housejoy", "urbanclap"],
        "Groceries": [
            "dmart",
            "more",
            "reliance fresh",
            "star bazaar",
            "spencer",
            "grocery",
            "provision",
        ],
    },
    "Health Care": {
        "Medical": ["apollo", "medplus", "sreedhar medicals"],
        "Pharmacy": [
            "apollo pharmacy",
            "medplus",
            "1mg",
            "pharmeasy",
            "netmeds",
            "pharmacy",
            "medical",
        ],
        "Health Insurance": ["icicipruli", "maxbupa"],
        "Hospital": ["mother hood"],
        "Consultation": ["practo", "clinic", "hospital", "diagnostic", "lab", "health"],
        "Insurance": ["star health", "niva bupa", "hdfc ergo", "icici lombard", "insurance"],
    },
    "Insurance": {
        "Life": ["lic", "hdfclife"],
    },
    "Savings": {
        "RD": ["monthlyrd", "postrd", "rd installment", "recurring deposit"],
        "PPF": ["ppf", "provisionalppf", "public provident fund"],
        "Investments": [
            "sip",
            "mutual fund",
            "zerodha",
            "groww",
            "upstox",
            "kuvera",
            "coin",
            "smallcase",
        ],
        "Fixed Deposit": ["fd", "fixed deposit"],
    },
    "Vacation": {
        "Hotel": ["wildernest hilltop res", "oyo", "makemytrip"],
        "Other": ["cleartrip", "yatra"],
    },
}


def normalize_merchant_text(text):
    if not text:
        return ""
    normalized = re.sub(r"[^a-z0-9\s]", " ", str(text).lower())
    return " ".join(normalized.split())


def _iter_rules():
    for category, subcategories in CATEGORY_RULES.items():
        for sub_category, merchants in subcategories.items():
            for merchant in merchants:
                yield category, sub_category, merchant


def _get_learned_mapping(merchant_text):
    merchant_key = normalize_merchant_text(merchant_text)
    if not merchant_key:
        return None

    from .models import MerchantCategoryMapping

    return MerchantCategoryMapping.objects.filter(merchant_key=merchant_key).first()


def learn_merchant_mapping(merchant_text, category, sub_category, source="manual", confidence=1.0):
    merchant_key = normalize_merchant_text(merchant_text)
    if not merchant_key or not category:
        return None

    from .models import MerchantCategoryMapping

    mapping, created = MerchantCategoryMapping.objects.get_or_create(
        merchant_key=merchant_key,
        defaults={
            "merchant_display": str(merchant_text).strip(),
            "category": category,
            "sub_category": sub_category or "Unknown",
            "source": source,
            "confidence": float(confidence),
            "times_used": 1,
        },
    )

    if not created:
        mapping.merchant_display = str(merchant_text).strip() or mapping.merchant_display
        mapping.times_used += 1

        if mapping.source != "manual" or source == "manual":
            mapping.category = category
            mapping.sub_category = sub_category or mapping.sub_category or "Unknown"
            mapping.source = source
            mapping.confidence = float(confidence)
            mapping.save(update_fields=["merchant_display", "category", "sub_category", "source", "confidence", "times_used", "updated_at"])
        else:
            mapping.save(update_fields=["merchant_display", "times_used", "updated_at"])
    return mapping


def classify_transaction(payee_text, description_text="", min_confidence=0.72):
    candidate = payee_text or description_text
    merchant_key = normalize_merchant_text(candidate)

    if not merchant_key:
        return "Unknown", "Unknown", 0.0, "empty"

    learned = _get_learned_mapping(merchant_key)
    if learned:
        return learned.category, learned.sub_category, 1.0, "learned"

    for category, sub_category, merchant in _iter_rules():
        if merchant in merchant_key:
            return category, sub_category, 0.95, "keyword"

    best_match = (None, None, 0.0)
    for category, sub_category, merchant in _iter_rules():
        score = SequenceMatcher(None, merchant_key, merchant).ratio()
        if score > best_match[2]:
            best_match = (category, sub_category, score)

    if best_match[0] and best_match[2] >= min_confidence:
        return best_match[0], best_match[1], round(best_match[2], 3), "fuzzy"

    return "Unknown", "Unknown", round(best_match[2], 3), "fallback"