import unittest

from quant_lab.brokers import (
    IbkrPaperBroker,
    ManualConfirmationRequired,
    OrderRequest,
    PaperSafetyError,
)


class FakeTransport:
    def __init__(self):
        self.calls = []
        self.order_response = [{"order_id": "42", "order_status": "Submitted"}]

    def __call__(self, method, path, payload=None):
        self.calls.append((method, path, payload))
        if path == "/iserver/auth/status":
            return {"authenticated": True, "connected": True}
        if path == "/iserver/accounts":
            return {"accounts": ["DU123"]}
        if path == "/portfolio/accounts":
            return [{"id": "DU123"}]
        if path.endswith("/positions"):
            return [
                {
                    "conid": 123,
                    "description": "TEST",
                    "position": 5,
                    "marketValue": 500,
                    "currency": "USD",
                }
            ]
        if path.endswith("/orders/whatif"):
            return {"amount": {"commission": "1.00"}}
        if path.endswith("/orders"):
            return self.order_response
        return {"order_status": "Submitted"}


class IbkrPaperBrokerTests(unittest.TestCase):
    def test_rejects_live_account(self):
        with self.assertRaisesRegex(PaperSafetyError, "DU"):
            IbkrPaperBroker("U123")

    def test_rejects_remote_or_live_api_url(self):
        with self.assertRaisesRegex(PaperSafetyError, "loopback"):
            IbkrPaperBroker("DU123", "https://api.ibkr.com/v1/api")

    def test_account_requires_authenticated_matching_paper_session(self):
        broker = IbkrPaperBroker("DU123", transport=FakeTransport())
        self.assertEqual(broker.account().mode, "PAPER")

    def test_preview_uses_whatif_and_does_not_require_submission_flag(self):
        transport = FakeTransport()
        broker = IbkrPaperBroker("DU123", transport=transport)
        broker.preview_order(OrderRequest(123, "BUY", 2))
        preview_call = next(call for call in transport.calls if call[1].endswith("/orders/whatif"))
        self.assertEqual(preview_call[2]["orders"][0]["conid"], 123)
        self.assertEqual(preview_call[2]["orders"][0]["quantity"], 2)

    def test_submission_is_disabled_by_default(self):
        broker = IbkrPaperBroker("DU123", transport=FakeTransport())
        with self.assertRaisesRegex(PaperSafetyError, "disabled"):
            broker.submit_order(OrderRequest(123, "BUY", 2))

    def test_sell_cannot_exceed_position(self):
        broker = IbkrPaperBroker("DU123", allow_order_submission=True, transport=FakeTransport())
        with self.assertRaisesRegex(PaperSafetyError, "short"):
            broker.submit_order(OrderRequest(123, "SELL", 6))

    def test_warning_requires_manual_confirmation(self):
        transport = FakeTransport()
        transport.order_response = [{"id": "confirm-1", "message": ["Price warning"]}]
        broker = IbkrPaperBroker("DU123", allow_order_submission=True, transport=transport)
        with self.assertRaises(ManualConfirmationRequired) as caught:
            broker.submit_order(OrderRequest(123, "BUY", 2))
        self.assertEqual(caught.exception.confirmation_id, "confirm-1")
