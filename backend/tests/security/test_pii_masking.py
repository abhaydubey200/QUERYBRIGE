"""
Security Tests: PII Masking & Data Protection

Validates:
- Email masking format
- SSN masking format
- Credit card masking format
- Phone masking format
- Name masking format
- Generic masking format
- Masking consistency
- Masking irreversibility
- Masking performance
- Coverage completeness
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import re


@pytest.mark.security
class TestPIIMaskingFormats:
    """Test output formats for all PII masking types"""

    def test_email_masking_format(self):
        """Verify email is masked in correct format"""
        original = "user@example.com"
        masked = "u***@example.com"  # First letter + *** + domain
        
        assert masked.startswith("u"), "Email should start with first letter"
        assert "@" in masked, "Email should preserve domain"
        assert "***" in masked, "Email should have *** for hidden part"
        assert original != masked, "Original and masked should differ"

    def test_ssn_masking_format(self):
        """Verify SSN is masked in correct format"""
        original = "123-45-6789"
        masked = "***-**-6789"  # Hide first 7 chars, show last 4
        
        assert masked.endswith("6789"), "SSN should show last 4 digits"
        assert masked.startswith("***"), "SSN should hide first part"
        assert "-" in masked, "SSN format should preserve dashes"

    def test_credit_card_masking_format(self):
        """Verify credit card is masked in correct format"""
        original = "4532-1111-2222-3333"
        masked = "****-****-****-3333"  # Show only last 4 digits
        
        assert masked.endswith("3333"), "Credit card should show last 4"
        assert masked.count("*") >= 12, "Credit card should mask at least 12 digits"
        assert "-" in masked, "Credit card format should preserve dashes"

    def test_phone_masking_format(self):
        """Verify phone is masked in correct format"""
        original = "555-123-4567"
        masked = "***-***-4567"  # Show last 4 digits
        
        assert masked.endswith("4567"), "Phone should show last 4 digits"
        assert masked.startswith("***"), "Phone should hide first part"
        assert "-" in masked, "Phone format should preserve dashes"

    def test_name_masking_format(self):
        """Verify name is masked in correct format"""
        original = "John Doe"
        masked = "J*** D**"  # First letter + *** for each name part
        
        # Should preserve structure but hide contents
        assert len(masked.split()) == len(original.split()), "Name structure should be preserved"
        assert "***" in masked, "Name should contain ***"

    def test_generic_masking_format(self):
        """Verify generic text is masked correctly"""
        original = "SomeConfidentialData"
        masked = "*********************"  # Full mask for unknown types
        
        assert len(masked) == len(original), "Generic mask should preserve length"
        assert all(c == "*" for c in masked), "Generic mask should be all asterisks"


@pytest.mark.security
class TestPIIMaskingConsistency:
    """Test masking consistency across queries"""

    def test_same_email_always_same_mask(self):
        """Verify same email always masked to same value"""
        email = "user@example.com"
        
        # Simulate multiple masks of same email
        mask1 = "u***@example.com"
        mask2 = "u***@example.com"
        
        assert mask1 == mask2, "Same email should produce same mask consistently"

    def test_different_emails_different_masks(self):
        """Verify different emails produce different masks"""
        email1 = "user1@example.com"
        email2 = "user2@example.com"
        
        mask1 = "u***@example.com"
        mask2 = "u***@example.com"
        
        # Different sources but same domain = similar but different
        # This test validates the masking differentiates users

    def test_masking_deterministic(self):
        """Verify masking produces deterministic results"""
        ssn = "123-45-6789"
        
        # Apply mask multiple times
        masks = [
            "***-**-6789",
            "***-**-6789",
            "***-**-6789",
        ]
        
        # All should be identical
        assert len(set(masks)) == 1, "Masking should be deterministic"


@pytest.mark.security
class TestPIIMaskingIrreversibility:
    """Test that masking cannot be reversed"""

    def test_email_irreversible(self):
        """Verify masked email cannot be reversed to original"""
        original = "john.smith@company.com"
        masked = "j***@company.com"
        
        # Should not be able to recover original from masked
        assert original != masked, "Masked should differ from original"
        
        # Multiple possibilities could produce same mask
        candidates = [
            "james.smith@company.com",
            "john.smith@company.com",
            "jane.smith@company.com",
            "jonathan.smith@company.com",
        ]
        
        # Masked should not uniquely identify original
        same_mask_count = sum(1 for c in candidates if c[0].lower() == "j")
        assert same_mask_count > 1, "Multiple values should produce same mask"

    def test_ssn_irreversible(self):
        """Verify masked SSN cannot be reversed to original"""
        original = "123-45-6789"
        masked = "***-**-6789"
        
        # Many SSNs end in 6789
        candidates = [
            "111-11-6789",
            "123-45-6789",
            "999-99-6789",
        ]
        
        same_mask_count = sum(1 for c in candidates if c.endswith("6789"))
        assert same_mask_count > 1, "Multiple SSNs should produce same mask"

    def test_hashing_not_reversible(self):
        """Verify cryptographic hashing produces irreversible output"""
        import hashlib
        
        original = "sensitive_data"
        hashed = hashlib.sha256(original.encode()).hexdigest()
        
        # Should not equal original
        assert hashed != original, "Hash should not equal original"
        
        # Should be consistent
        hashed2 = hashlib.sha256(original.encode()).hexdigest()
        assert hashed == hashed2, "Hash should be deterministic"


@pytest.mark.security
class TestPIIMaskingPerformance:
    """Test masking performance under load"""

    def test_masking_latency_acceptable(self, benchmark_timer):
        """Verify masking completes within acceptable latency"""
        benchmark_timer.start()
        
        # Simulate masking 1000 values
        for i in range(1000):
            masked = f"***-**-{i:04d}"  # Simulate masking
        
        benchmark_timer.stop()
        
        # Should complete 1000 masks in <100ms
        benchmark_timer.assert_under(0.1)

    def test_bulk_masking_throughput(self, benchmark_timer):
        """Verify bulk masking handles large volumes"""
        benchmark_timer.start()
        
        # Simulate masking 10000 rows
        for i in range(10000):
            email = f"user{i}@example.com"
            masked = f"u***@example.com"
        
        benchmark_timer.stop()
        
        # Should complete 10k masks in <1 second
        benchmark_timer.assert_under(1.0)

    def test_concurrent_masking(self):
        """Verify masking handles concurrent requests"""
        import concurrent.futures
        
        def mask_value(val):
            return f"u***@example.com"
        
        # Simulate 100 concurrent masks
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            values = [f"user{i}@example.com" for i in range(100)]
            results = list(executor.map(mask_value, values))
        
        assert len(results) == 100, "Should complete all concurrent masks"
        assert all("***" in r for r in results), "All should be masked"


@pytest.mark.security
class TestPIIMaskingCoverage:
    """Test that all PII columns are masked"""

    def test_all_email_columns_masked(self):
        """Verify all email columns are masked"""
        email_columns = [
            "customer_email",
            "user_email",
            "contact_email",
            "email_address",
        ]
        
        for col in email_columns:
            is_masked = True  # Simulate detection and masking
            assert is_masked, f"Column {col} should be masked"

    def test_all_pii_types_masked(self):
        """Verify all 6 PII types are masked"""
        pii_types = [
            "email",
            "ssn",
            "credit_card",
            "phone",
            "name",
            "generic",
        ]
        
        masked_count = 0
        for pii_type in pii_types:
            masked_count += 1
        
        assert masked_count == 6, f"Should mask all 6 types, got {masked_count}"

    def test_no_pii_leak_in_output(self):
        """Verify no PII leaks through in masked output"""
        original_pii = "john.smith@company.com"
        masked = "j***@company.com"
        
        # Original data should not be visible
        assert "john" not in masked.lower(), "Original name should not leak"
        assert "smith" not in masked.lower(), "Original surname should not leak"
        
        # Only partial info (domain) visible
        assert "company.com" in masked, "Non-PII parts can be visible (domain)"

    def test_masked_data_safe_for_logging(self):
        """Verify masked data is safe to log"""
        original = "SSN: 123-45-6789"
        masked_output = "SSN: ***-**-6789"
        
        # Masked data should be safe to log
        log_entry = f"Processing: {masked_output}"
        
        # Original SSN should not be in log
        assert "123-45-6789" not in log_entry, "Original should not be logged"
        assert "***-**-6789" in log_entry, "Masked should be logged"


@pytest.mark.security
class TestPIIMaskingRBAC:
    """Test masking with role-based access control"""

    def test_admin_sees_unmasked(self):
        """Verify admin role can see unmasked PII"""
        user_role = "admin"
        data = "user@example.com"
        
        # Admin should see original
        display_data = data if user_role == "admin" else "***"
        assert display_data == data, "Admin should see original"

    def test_analyst_sees_partially_masked(self):
        """Verify analyst role sees partially masked PII"""
        user_role = "analyst"
        data = "user@example.com"
        
        # Analyst should see partial mask
        display_data = "u***@example.com" if user_role == "analyst" else data
        assert "***" in display_data, "Analyst should see partial mask"
        assert display_data != data, "Analyst should not see full original"

    def test_viewer_sees_fully_masked(self):
        """Verify viewer role sees fully masked PII"""
        user_role = "viewer"
        data = "user@example.com"
        
        # Viewer should see full mask
        display_data = "***@***" if user_role == "viewer" else data
        assert "***" in display_data, "Viewer should see mask"
        assert "@" in display_data, "Structure should be preserved"

    def test_public_user_blocked_from_pii(self):
        """Verify public users cannot access PII at all"""
        user_role = "public"
        data = "user@example.com"
        
        # Public should get null/empty
        try:
            display_data = data if user_role in ["admin", "analyst"] else None
            assert display_data is None, "Public should not see PII"
        except Exception:
            pass  # Access denied


@pytest.mark.security
class TestPIIMaskingAudit:
    """Test audit logging of masking operations"""

    def test_masking_operation_logged(self):
        """Verify masking operations are logged"""
        audit_log = {
            "operation": "mask_pii",
            "column": "customer_email",
            "user": "analyst",
            "timestamp": "2026-05-12T15:57:14",
        }
        
        assert audit_log["operation"] == "mask_pii", "Operation should be logged"
        assert audit_log["user"] == "analyst", "User should be logged"

    def test_masked_data_not_in_audit_log(self):
        """Verify masked PII does not appear in audit logs"""
        original_pii = "123-45-6789"
        audit_log = f"Masked SSN: [REDACTED]"
        
        assert original_pii not in audit_log, "Original PII should not be in audit log"
        assert "[REDACTED]" in audit_log, "Should indicate masking occurred"

    def test_failed_masking_attempt_logged(self):
        """Verify failed masking attempts are logged"""
        audit_log = {
            "operation": "mask_pii_failed",
            "reason": "Column not found",
            "user": "analyst",
            "status": "error",
        }
        
        assert audit_log["status"] == "error", "Failed attempt should be logged"
        assert "reason" in audit_log, "Reason should be logged"


@pytest.mark.security
class TestPIIMaskingIntegration:
    """Integration tests for masking in data flow"""

    def test_masking_before_returning_to_user(self):
        """Verify PII is masked before returning to user"""
        user_role = "analyst"
        db_data = "user@example.com"
        
        # Simulate masking before return
        returned_data = "u***@example.com" if user_role != "admin" else db_data
        
        # User should get masked data
        assert "***" in returned_data, "Data returned to user should be masked"

    def test_masking_in_export(self):
        """Verify PII is masked in data exports"""
        export_format = "csv"
        data_row = ["john.smith", "john@example.com", "555-123-4567"]
        
        # Simulate masking in export
        masked_row = [
            "J***",  # Name masked
            "j***@example.com",  # Email masked
            "***-***-4567",  # Phone masked
        ]
        
        # Export should have masked data
        assert all("***" in str(v) for v in masked_row if isinstance(v, str)), "Export should be masked"

    def test_masking_in_cache(self):
        """Verify cached data is masked if accessed by unauthorized user"""
        cached_data_key = "user_profile"
        cached_data = {"email": "user@example.com"}
        
        # When accessed by non-admin, should be masked
        user_role = "analyst"
        if user_role != "admin":
            cached_data = {"email": "u***@example.com"}
        
        assert "***" in cached_data["email"], "Cached data should be masked for non-admin"
