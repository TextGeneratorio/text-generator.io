from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_backend_price_ids_are_updated():
    main_py = _read("main.py")
    assert 'MONTHLY_SUBSCRIPTION_PRICE_ID = "price_0TMflXDtz2XsjQROwqDwU3Pt"' in main_py
    assert 'ANNUAL_SUBSCRIPTION_PRICE_ID = "price_0TMfntDtz2XsjQROebse1At5"' in main_py


def test_checkout_ui_prices_are_updated():
    checkout_js = _read("static/js/checkout-dialog.js")
    assert "monthly: '$9.99'" in checkout_js
    assert "annual: '$99.99'" in checkout_js
    assert "save 17%" in checkout_js


def test_subscription_modal_prices_are_updated():
    subscription_modal_js = _read("static/js/subscription-modal.js")
    assert "monthly: '$9.99/mo'" in subscription_modal_js
    assert "annual: '$99.99/year'" in subscription_modal_js
