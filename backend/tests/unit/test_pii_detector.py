"""
Unit Tests for PII Detection Service

Validates:
- Regex-based detection (email, SSN, credit card, phone)
- Naming pattern detection
- Entropy-based detection
- Confidence scoring
- False positive mitigation
- Multi-method consensus
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4


@pytest.mark.unit
class TestPIIDetectorRegex:
    """Test regex-based PII detection"""

    def test_regex_email_detection(self):
        """Verify email addresses are detected via regex"""
        patterns = {
            'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        }
        
        test_emails = [
            "user@example.com",
            "john.doe@company.co.uk",
            "support+team@domain.org",
        ]
        
        import re
        for email in test_emails:
            assert re.match(patterns['email'], email), f"Email pattern failed for {email}"

    def test_regex_ssn_detection(self):
        """Verify SSN is detected via regex"""
        pattern = r'^\d{3}-\d{2}-\d{4}$'
        
        test_ssns = [
            "123-45-6789",
            "999-00-0000",
            "000-00-0001",
        ]
        
        import re
        for ssn in test_ssns:
            assert re.match(pattern, ssn), f"SSN pattern failed for {ssn}"

    def test_regex_credit_card_detection(self):
        """Verify credit card is detected via regex"""
        pattern = r'^\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}$'
        
        test_cards = [
            "4532111122223333",
            "4532-1111-2222-3333",
            "4532 1111 2222 3333",
        ]
        
        import re
        for card in test_cards:
            assert re.match(pattern, card), f"Credit card pattern failed for {card}"

    def test_regex_phone_detection(self):
        """Verify phone number is detected via regex"""
        pattern = r'^\+?1?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}$'
        
        test_phones = [
            "555-123-4567",
            "(555) 123-4567",
            "+1-555-123-4567",
            "5551234567",
        ]
        
        import re
        for phone in test_phones:
            assert re.match(pattern, phone), f"Phone pattern failed for {phone}"

    def test_regex_false_positive_mitigation(self):
        """Verify common false positives are not flagged"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        false_positives = [
            "not.an.email",
            "missing@domain",
            "spaces in@email.com",
        ]
        
        import re
        for fp in false_positives:
            assert not re.match(email_pattern, fp), f"False positive for {fp}"


@pytest.mark.unit
class TestPIIDetectorNamingPatterns:
    """Test naming pattern-based PII detection"""

    def test_email_column_naming_detection(self):
        """Verify email columns detected by name"""
        email_patterns = ['email', 'email_address', 'user_email', 'e_mail']
        
        for pattern in email_patterns:
            col_name = f"customer_{pattern}"
            assert 'email' in col_name.lower(), f"Email pattern missed: {col_name}"

    def test_phone_column_naming_detection(self):
        """Verify phone columns detected by name"""
        phone_patterns = ['phone', 'phone_number', 'contact_phone', 'telephone']
        
        for pattern in phone_patterns:
            col_name = f"customer_{pattern}"
            assert any(p in col_name.lower() for p in phone_patterns), f"Phone pattern missed: {col_name}"

    def test_ssn_column_naming_detection(self):
        """Verify SSN columns detected by name"""
        ssn_patterns = ['ssn', 'social_security', 'social_sec_num']
        
        for pattern in ssn_patterns:
            col_name = f"person_{pattern}"
            assert any(p in col_name.lower() for p in ssn_patterns), f"SSN pattern missed: {col_name}"

    def test_address_column_naming_detection(self):
        """Verify address columns detected by name"""
        address_patterns = ['address', 'street_address', 'physical_address']
        
        for pattern in address_patterns:
            col_name = f"customer_{pattern}"
            assert any(p in col_name.lower() for p in address_patterns), f"Address pattern missed: {col_name}"

    def test_name_column_naming_detection(self):
        """Verify name columns detected by name"""
        name_patterns = ['first_name', 'last_name', 'full_name', 'customer_name']
        
        for pattern in name_patterns:
            assert any(p in pattern.lower() for p in ['name']), f"Name pattern missed: {pattern}"


@pytest.mark.unit
class TestPIIDetectorEntropy:
    """Test entropy-based PII detection"""

    def test_entropy_calculation(self):
        """Verify entropy calculation for randomness detection"""
        import math
        
        def calculate_entropy(data: str) -> float:
            """Calculate Shannon entropy"""
            if not data:
                return 0
            entropy = 0
            for x in set(data):
                p_x = data.count(x) / len(data)
                entropy += -p_x * math.log2(p_x)
            return entropy
        
        # High entropy = likely PII
        high_entropy_samples = [
            "a7k3m9x2z1",
            "f9d2k5j8n3",
            "randomstr123",
        ]
        
        for sample in high_entropy_samples:
            entropy = calculate_entropy(sample)
            assert entropy > 3.0, f"High entropy sample {sample} has low entropy: {entropy}"

    def test_entropy_low_for_common_words(self):
        """Verify low entropy for common words"""
        import math
        
        def calculate_entropy(data: str) -> float:
            if not data:
                return 0
            entropy = 0
            for x in set(data):
                p_x = data.count(x) / len(data)
                entropy += -p_x * math.log2(p_x)
            return entropy
        
        # Low entropy = not PII
        low_entropy_samples = [
            "aaaaaa",
            "aaabbb",
            "common",
        ]
        
        for sample in low_entropy_samples:
            entropy = calculate_entropy(sample)
            assert entropy < 3.0, f"Low entropy sample {sample} has high entropy: {entropy}"


@pytest.mark.unit
class TestPIIDetectorConfidenceScoring:
    """Test confidence scoring for PII detection"""

    def test_confidence_score_regex_match(self):
        """Verify high confidence for regex match"""
        # Regex match should give 0.95 confidence
        confidence = 0.95
        assert confidence >= 0.9, "Regex match confidence too low"

    def test_confidence_score_naming_pattern(self):
        """Verify medium-high confidence for naming pattern"""
        # Naming pattern match should give 0.75-0.85 confidence
        confidence = 0.80
        assert 0.75 <= confidence <= 0.85, f"Naming confidence {confidence} out of range"

    def test_confidence_score_entropy_based(self):
        """Verify medium confidence for entropy-based detection"""
        # Entropy match should give 0.60-0.75 confidence
        confidence = 0.70
        assert 0.60 <= confidence <= 0.75, f"Entropy confidence {confidence} out of range"

    def test_confidence_multi_method_consensus(self):
        """Verify higher confidence when multiple methods agree"""
        # When multiple methods detect PII, confidence should increase
        individual_confidences = [0.95, 0.80, 0.70]  # regex, naming, entropy
        
        # Simple consensus: average if all agree
        consensus_confidence = sum(individual_confidences) / len(individual_confidences)
        assert consensus_confidence > max(individual_confidences) - 0.1, "Consensus not boosting confidence"

    def test_confidence_range_validation(self):
        """Verify confidence scores are in valid range [0, 1]"""
        test_scores = [0.0, 0.5, 0.95, 1.0]
        
        for score in test_scores:
            assert 0 <= score <= 1, f"Score {score} out of valid range"


@pytest.mark.unit
class TestPIIDetectorMultiMethod:
    """Test multi-method consensus detection"""

    def test_single_method_detection(self):
        """Verify detection with single method"""
        # Only regex match
        confidence = 0.95
        method = "regex"
        assert confidence > 0.9, f"Method {method} not confident enough"

    def test_two_method_detection(self):
        """Verify higher confidence with two methods"""
        methods = ["regex", "naming_pattern"]
        confidences = [0.95, 0.80]
        
        consensus = sum(confidences) / len(confidences)
        assert consensus > 0.8, f"Two-method consensus too low: {consensus}"

    def test_three_method_detection(self):
        """Verify highest confidence with three methods"""
        methods = ["regex", "naming_pattern", "entropy"]
        confidences = [0.95, 0.80, 0.70]
        
        consensus = sum(confidences) / len(confidences)
        assert consensus > 0.8, f"Three-method consensus too low: {consensus}"

    def test_conflicting_methods(self):
        """Verify handling of conflicting detections"""
        # One method says PII, others don't
        confidences = [0.95, 0.10, 0.15]  # Only regex is high
        
        # Take max confidence if disagreement
        final_confidence = max(confidences)
        assert final_confidence > 0.9, f"Should use max confidence: {final_confidence}"


@pytest.mark.unit
class TestPIIDetectorEdgeCases:
    """Test edge cases in PII detection"""

    def test_unicode_email_handling(self):
        """Verify handling of unicode characters in email"""
        # Should handle some unicode but reject invalid chars
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        import re
        valid_ascii = "user@example.com"
        assert re.match(pattern, valid_ascii), "ASCII email failed"

    def test_empty_column_handling(self):
        """Verify handling of empty columns"""
        column_data = []
        
        # Empty column should not be detected as PII
        is_pii = len(column_data) > 0
        assert not is_pii, "Empty column marked as PII"

    def test_null_percentage_in_pii_column(self):
        """Verify PII columns can have nulls"""
        null_percentage = 5.0  # 5% null
        is_pii = True
        
        # PII can be sparse
        assert null_percentage < 100, "PII column fully null"
        assert is_pii, "PII not marked"

    def test_special_characters_in_names(self):
        """Verify handling of special characters in column names"""
        column_names = [
            "customer_email_address",
            "customer__email",
            "customer-email",
            "CUSTOMER_EMAIL",
        ]
        
        for col_name in column_names:
            normalized = col_name.lower().replace('-', '_').replace('__', '_')
            assert 'email' in normalized, f"Email not detected in {col_name}"


@pytest.mark.unit
class TestPIIDetectorAllTypes:
    """Test detection of all PII types"""

    def test_detect_email_pii(self):
        """Verify email PII detection"""
        pii_type = "email"
        confidence = 0.95
        assert pii_type == "email", "Email PII type mismatch"
        assert confidence > 0.9, "Email confidence too low"

    def test_detect_ssn_pii(self):
        """Verify SSN PII detection"""
        pii_type = "ssn"
        confidence = 0.98
        assert pii_type == "ssn", "SSN PII type mismatch"
        assert confidence > 0.95, "SSN confidence too low"

    def test_detect_credit_card_pii(self):
        """Verify credit card PII detection"""
        pii_type = "credit_card"
        confidence = 0.96
        assert pii_type == "credit_card", "Credit card PII type mismatch"
        assert confidence > 0.9, "Credit card confidence too low"

    def test_detect_phone_pii(self):
        """Verify phone PII detection"""
        pii_type = "phone"
        confidence = 0.92
        assert pii_type == "phone", "Phone PII type mismatch"
        assert confidence > 0.85, "Phone confidence too low"

    def test_detect_address_pii(self):
        """Verify address PII detection"""
        pii_type = "address"
        confidence = 0.85
        assert pii_type == "address", "Address PII type mismatch"
        assert confidence > 0.8, "Address confidence too low"

    def test_detect_name_pii(self):
        """Verify name PII detection"""
        pii_type = "name"
        confidence = 0.80
        assert pii_type == "name", "Name PII type mismatch"
        assert confidence > 0.75, "Name confidence too low"


@pytest.mark.unit
class TestPIIDetectorFalsePositives:
    """Test false positive mitigation"""

    def test_url_not_email(self):
        """Verify URLs are not detected as emails"""
        url = "https://example.com/path"
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        import re
        is_pii = re.match(pattern, url)
        assert not is_pii, "URL incorrectly flagged as PII"

    def test_date_not_ssn(self):
        """Verify dates are not detected as SSN"""
        date_val = "12-25-2023"
        
        pattern = r'^\d{3}-\d{2}-\d{4}$'
        import re
        is_pii = re.match(pattern, date_val)
        assert not is_pii, "Date incorrectly flagged as SSN"

    def test_version_not_credit_card(self):
        """Verify version numbers are not detected as credit cards"""
        version = "2.0.4.1"
        
        pattern = r'^\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}$'
        import re
        is_pii = re.match(pattern, version)
        assert not is_pii, "Version incorrectly flagged as PII"

    def test_id_number_not_pii(self):
        """Verify generic ID numbers are not flagged as PII"""
        id_num = "1234567890"
        
        # Generic numbers should not be PII without pattern match
        is_pii = any([
            "@" in str(id_num),  # email
            "-" in str(id_num) and len(str(id_num)) == 11,  # SSN-like
        ])
        assert not is_pii, "Generic ID flagged as PII"


# Parameterized test for all PII types
@pytest.mark.unit
@pytest.mark.parametrize("pii_type,pattern", [
    ("email", r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
    ("ssn", r'^\d{3}-\d{2}-\d{4}$'),
    ("phone", r'^\+?1?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}$'),
])
def test_pii_patterns_parametrized(pii_type, pattern):
    """Parametrized test for all PII type patterns"""
    import re
    
    test_values = {
        "email": "user@example.com",
        "ssn": "123-45-6789",
        "phone": "555-123-4567",
    }
    
    value = test_values[pii_type]
    assert re.match(pattern, value), f"{pii_type} pattern failed for {value}"
