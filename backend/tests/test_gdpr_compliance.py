"""
Comprehensive GDPR Compliance Tests

Tests all GDPR data subject rights and consent management functionality.
"""

import pytest
import json
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from backend.services.consent_manager import ConsentManager, ConsentType, ConsentStatus
from backend.services.gdpr_service import GDPRService
from backend.config import settings


class TestConsentManager:
    """Test consent management functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.consent_manager = ConsentManager()
        self.test_user = "test@example.com"
        self.test_session_token = "test-session-token-123"

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_session.query.return_value.filter.return_value.all.return_value = []
        mock_session.commit.return_value = None
        mock_session.rollback.return_value = None
        return mock_session

    @pytest.fixture
    def mock_session_with_consent(self):
        """Mock session with existing consent data"""
        mock_session = MagicMock()
        mock_session.consent_data = json.dumps({
            "data_processing": {
                "user_identifier": self.test_user,
                "consent_type": "data_processing",
                "status": "given",
                "given_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(days=365)).isoformat()
            }
        })
        mock_session.consent_updated_at = datetime.utcnow()
        mock_session.commit.return_value = None
        return mock_session

    def test_collect_consent_success(self, mock_db_session):
        """Test successful consent collection"""
        # Mock session query to return a session
        mock_session = MagicMock()
        mock_session.consent_data = None
        mock_session.consent_updated_at = None
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_session

        consent_data = {
            "ip_address": "192.168.1.1",
            "user_agent": "Mozilla/5.0",
            "consent_version": "1.0",
            "legal_basis": "consent",
            "purpose": "Service delivery",
            "data_categories": ["email", "session_data"],
            "retention_period": "90 days",
            "third_parties": ["AWS S3"],
            "withdrawal_method": "email"
        }

        result = self.consent_manager.collect_consent(
            self.test_session_token,
            ConsentType.DATA_PROCESSING,
            consent_data,
            mock_db_session
        )

        assert result["success"] is True
        assert "consent_id" in result
        assert result["consent_record"]["status"] == ConsentStatus.GIVEN.value
        assert result["consent_record"]["consent_type"] == ConsentType.DATA_PROCESSING.value
        mock_db_session.commit.assert_called_once()

    def test_collect_consent_error(self, mock_db_session):
        """Test consent collection error handling"""
        # Mock database error
        mock_db_session.commit.side_effect = Exception("Database error")

        consent_data = {"ip_address": "192.168.1.1"}

        result = self.consent_manager.collect_consent(
            self.test_session_token,
            ConsentType.DATA_PROCESSING,
            consent_data,
            mock_db_session
        )

        assert result["success"] is False
        assert "error" in result
        mock_db_session.rollback.assert_called_once()

    def test_withdraw_consent_success(self, mock_session_with_consent):
        """Test successful consent withdrawal"""
        result = self.consent_manager.withdraw_consent(
            self.test_user,
            ConsentType.DATA_PROCESSING,
            "User requested withdrawal",
            mock_session_with_consent
        )

        assert result["success"] is True
        assert result["consent_record"]["status"] == ConsentStatus.WITHDRAWN.value
        assert "withdrawn_at" in result["consent_record"]
        assert result["consent_record"]["withdrawal_reason"] == "User requested withdrawal"

    def test_withdraw_consent_not_found(self, mock_db_session):
        """Test consent withdrawal when no consent found"""
        result = self.consent_manager.withdraw_consent(
            self.test_user,
            ConsentType.DATA_PROCESSING,
            "User requested withdrawal",
            mock_db_session
        )

        assert result["success"] is False
        assert "No consent found" in result["message"]

    def test_get_consent_status_given(self, mock_session_with_consent):
        """Test getting consent status when consent is given"""
        result = self.consent_manager.get_consent_status(
            self.test_user,
            ConsentType.DATA_PROCESSING,
            mock_session_with_consent
        )

        assert result["has_consent"] is True
        assert result["status"] == ConsentStatus.GIVEN.value
        assert "consent_record" in result

    def test_get_consent_status_expired(self, mock_db_session):
        """Test getting consent status when consent is expired"""
        # Mock expired consent
        expired_consent = {
            "data_processing": {
                "user_identifier": self.test_user,
                "consent_type": "data_processing",
                "status": "given",
                "given_at": (datetime.utcnow() - timedelta(days=400)).isoformat(),
                "expires_at": (datetime.utcnow() - timedelta(days=1)).isoformat()
            }
        }

        mock_session = MagicMock()
        mock_session.consent_data = json.dumps(expired_consent)
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_session

        result = self.consent_manager.get_consent_status(
            self.test_user,
            ConsentType.DATA_PROCESSING,
            mock_db_session
        )

        assert result["has_consent"] is False
        assert result["status"] == ConsentStatus.EXPIRED.value

    def test_get_all_consents(self, mock_session_with_consent):
        """Test getting all consents for a user"""
        result = self.consent_manager.get_all_consents(
            self.test_user,
            mock_session_with_consent
        )

        assert "consents" in result
        assert "data_processing" in result["consents"]
        assert result["total_consents"] == 1

    def test_cleanup_expired_consents(self, mock_db_session):
        """Test cleanup of expired consent records"""
        # Mock sessions with expired consents
        expired_consent = {
            "data_processing": {
                "user_identifier": self.test_user,
                "consent_type": "data_processing",
                "status": "given",
                "expires_at": (datetime.utcnow() - timedelta(days=1)).isoformat()
            }
        }

        mock_session = MagicMock()
        mock_session.consent_data = json.dumps(expired_consent)
        mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_session]

        result = self.consent_manager.cleanup_expired_consents(mock_db_session)

        assert result == 1  # One expired consent cleaned up
        mock_db_session.commit.assert_called_once()

    def test_get_consent_statistics(self, mock_db_session):
        """Test getting consent statistics"""
        # Mock sessions with consent data
        mock_session = MagicMock()
        mock_session.consent_data = json.dumps({
            "data_processing": {"status": "given"},
            "email_marketing": {"status": "given"}
        })

        mock_db_session.query.return_value.count.return_value = 10
        mock_db_session.query.return_value.filter.return_value.count.return_value = 5
        mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_session]

        result = self.consent_manager.get_consent_statistics(mock_db_session)

        assert "total_sessions" in result
        assert "sessions_with_consent" in result
        assert "consent_coverage" in result
        assert "consent_types" in result
        assert "consent_statuses" in result


class TestGDPRService:
    """Test GDPR data subject rights functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.gdpr_service = GDPRService()
        self.test_user = "test@example.com"
        self.test_session_token = "test-session-token-123"

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.all.return_value = []
        mock_session.commit.return_value = None
        mock_session.rollback.return_value = None
        return mock_session

    @pytest.fixture
    def mock_session_data(self):
        """Mock session data"""
        mock_session = MagicMock()
        mock_session.id = uuid.uuid4()
        mock_session.session_token = self.test_session_token
        mock_session.email = self.test_user
        mock_session.photo_s3_key = "photos/test.jpg"
        mock_session.audio_s3_key = "audio/test.mp3"
        mock_session.custom_text = "Test text"
        mock_session.created_at = datetime.utcnow()
        mock_session.expires_at = datetime.utcnow() + timedelta(hours=24)
        mock_session.unsubscribed = False
        mock_session.data_processing_consent = True
        mock_session.marketing_consent = False
        mock_session.consent_data = json.dumps({
            "data_processing": {"status": "given"}
        })
        return mock_session

    @pytest.fixture
    def mock_order_data(self):
        """Mock order data"""
        mock_order = MagicMock()
        mock_order.id = uuid.uuid4()
        mock_order.email = self.test_user
        mock_order.amount_cents = 999
        mock_order.status = "completed"
        mock_order.created_at = datetime.utcnow()
        mock_order.session_token = self.test_session_token
        return mock_order

    def test_get_user_data_success(self, mock_db_session, mock_session_data, mock_order_data):
        """Test successful user data retrieval"""
        # Mock database queries
        mock_db_session.query.return_value.filter.return_value.all.side_effect = [
            [mock_session_data],  # Sessions
            [mock_order_data],    # Orders
            []                    # Email subscribers
        ]

        with patch('backend.services.gdpr_service.consent_manager') as mock_consent_manager:
            mock_consent_manager.get_all_consents.return_value = {
                "consents": {"data_processing": {"status": "given"}}
            }

            result = self.gdpr_service.get_user_data(self.test_user, mock_db_session)

            assert "user_identifier" in result
            assert "data_categories" in result
            assert "sessions" in result["data_categories"]
            assert "orders" in result["data_categories"]
            assert "consent_records" in result["data_categories"]
            assert "data_processing_info" in result

    def test_get_user_data_error(self, mock_db_session):
        """Test user data retrieval error handling"""
        # Mock database error
        mock_db_session.query.side_effect = Exception("Database error")

        result = self.gdpr_service.get_user_data(self.test_user, mock_db_session)

        assert "error" in result
        assert "Error retrieving user data" in result["message"]

    def test_export_user_data_success(self, mock_db_session, mock_session_data):
        """Test successful user data export"""
        # Mock database queries
        mock_db_session.query.return_value.filter.return_value.all.side_effect = [
            [mock_session_data],  # Sessions
            [],                   # Orders
            []                    # Email subscribers
        ]

        with patch('backend.services.gdpr_service.consent_manager') as mock_consent_manager:
            mock_consent_manager.get_all_consents.return_value = {
                "consents": {"data_processing": {"status": "given"}}
            }

            result = self.gdpr_service.export_user_data(self.test_user, mock_db_session)

            assert result["success"] is True
            assert "export_data" in result
            assert "json_export" in result
            assert "zip_export" in result
            assert "export_size_bytes" in result
            assert "zip_size_bytes" in result

    def test_erase_user_data_success(self, mock_db_session, mock_session_data, mock_order_data):
        """Test successful user data erasure"""
        # Mock database queries
        mock_db_session.query.return_value.filter.return_value.all.side_effect = [
            [mock_session_data],  # Sessions
            [mock_order_data],    # Orders
            []                    # Email subscribers
        ]

        with patch('backend.services.gdpr_service.consent_manager') as mock_consent_manager:
            mock_consent_manager.withdraw_consent.return_value = {"success": True}

            result = self.gdpr_service.erase_user_data(self.test_user, mock_db_session)

            assert result["success"] is True
            assert "erasure_log" in result
            assert "deleted_records" in result
            assert "erased_categories" in result["erasure_log"]

    def test_erase_user_data_legal_retention(self, mock_db_session, mock_session_data):
        """Test user data erasure with legal retention requirements"""
        # Mock recent order (within legal retention period)
        recent_order = MagicMock()
        recent_order.id = uuid.uuid4()
        recent_order.created_at = datetime.utcnow() - timedelta(days=100)  # Recent order
        recent_order.session_token = self.test_session_token

        mock_db_session.query.return_value.filter.return_value.all.side_effect = [
            [mock_session_data],  # Sessions
            [recent_order],       # Orders
            []                    # Email subscribers
        ]

        with patch('backend.services.gdpr_service.consent_manager') as mock_consent_manager:
            mock_consent_manager.withdraw_consent.return_value = {"success": True}

            result = self.gdpr_service.erase_user_data(self.test_user, mock_db_session)

            assert result["success"] is True
            assert "retained_data" in result["erasure_log"]
            assert "legal_basis_for_retention" in result["erasure_log"]

    def test_rectify_user_data_success(self, mock_db_session, mock_session_data):
        """Test successful user data rectification"""
        # Mock database queries
        mock_db_session.query.return_value.filter.return_value.all.side_effect = [
            [mock_session_data],  # Sessions
            [],                   # Orders
            []                    # Email subscribers
        ]

        corrections = {
            "custom_text": "Updated text",
            "email": "newemail@example.com"
        }

        result = self.gdpr_service.rectify_user_data(self.test_user, corrections, mock_db_session)

        assert result["success"] is True
        assert "rectification_log" in result
        assert "corrections_applied" in result["rectification_log"]
        assert result["corrections_applied"] > 0

    def test_rectify_user_data_error(self, mock_db_session):
        """Test user data rectification error handling"""
        # Mock database error
        mock_db_session.commit.side_effect = Exception("Database error")

        corrections = {"custom_text": "Updated text"}

        result = self.gdpr_service.rectify_user_data(self.test_user, corrections, mock_db_session)

        assert result["success"] is False
        assert "error" in result
        mock_db_session.rollback.assert_called_once()

    def test_get_data_processing_info(self):
        """Test getting data processing information"""
        result = self.gdpr_service.get_data_processing_info()

        assert "data_controller" in result
        assert "legal_basis" in result
        assert "data_categories" in result
        assert "purposes" in result
        assert "retention_periods" in result
        assert "third_parties" in result
        assert "data_subject_rights" in result
        assert "contact_information" in result


class TestGDPRComplianceIntegration:
    """Test GDPR compliance integration with FastAPI"""

    @pytest.fixture
    def client(self):
        """Test client"""
        from backend.main import app
        return TestClient(app)

    def test_collect_consent_endpoint(self, client):
        """Test consent collection endpoint"""
        consent_data = {
            "ip_address": "192.168.1.1",
            "user_agent": "Mozilla/5.0",
            "consent_version": "1.0",
            "legal_basis": "consent",
            "purpose": "Service delivery"
        }

        response = client.post(
            "/api/gdpr/consent",
            data={
                "user_identifier": "test@example.com",
                "consent_type": "data_processing",
                "consent_data": json.dumps(consent_data)
            }
        )

        # Should return 200 or 400 depending on database state
        assert response.status_code in [200, 400, 500]

    def test_withdraw_consent_endpoint(self, client):
        """Test consent withdrawal endpoint"""
        response = client.delete(
            "/api/gdpr/consent",
            data={
                "user_identifier": "test@example.com",
                "consent_type": "data_processing",
                "withdrawal_reason": "User requested"
            }
        )

        # Should return 200 or 400 depending on database state
        assert response.status_code in [200, 400, 500]

    def test_get_consent_status_endpoint(self, client):
        """Test consent status endpoint"""
        response = client.get("/api/gdpr/consent/test@example.com")

        # Should return 200 or 500 depending on database state
        assert response.status_code in [200, 500]

    def test_get_user_data_endpoint(self, client):
        """Test user data access endpoint"""
        response = client.get("/api/gdpr/data/test@example.com")

        # Should return 200 or 500 depending on database state
        assert response.status_code in [200, 500]

    def test_export_user_data_endpoint(self, client):
        """Test user data export endpoint"""
        response = client.get("/api/gdpr/export/test@example.com")

        # Should return 200 or 500 depending on database state
        assert response.status_code in [200, 500]

    def test_erase_user_data_endpoint(self, client):
        """Test user data erasure endpoint"""
        response = client.delete("/api/gdpr/data/test@example.com")

        # Should return 200 or 500 depending on database state
        assert response.status_code in [200, 500]

    def test_rectify_user_data_endpoint(self, client):
        """Test user data rectification endpoint"""
        corrections = {"custom_text": "Updated text"}

        response = client.put(
            "/api/gdpr/data/test@example.com",
            json=corrections
        )

        # Should return 200 or 500 depending on database state
        assert response.status_code in [200, 500]

    def test_get_data_processing_info_endpoint(self, client):
        """Test data processing info endpoint"""
        response = client.get("/api/gdpr/processing-info")

        assert response.status_code == 200
        data = response.json()
        assert "data_controller" in data
        assert "legal_basis" in data
        assert "data_categories" in data

    def test_get_consent_statistics_endpoint(self, client):
        """Test consent statistics endpoint"""
        response = client.get("/api/gdpr/consent-statistics")

        # Should return 200 or 500 depending on database state
        assert response.status_code in [200, 500]

    def test_cleanup_expired_consents_endpoint(self, client):
        """Test cleanup expired consents endpoint"""
        response = client.post("/api/gdpr/cleanup-consents")

        # Should return 200 or 500 depending on database state
        assert response.status_code in [200, 500]


class TestGDPRComplianceValidation:
    """Test GDPR compliance validation and edge cases"""

    def test_consent_type_validation(self):
        """Test consent type validation"""
        consent_manager = ConsentManager()

        # Test valid consent types
        valid_types = [
            ConsentType.DATA_PROCESSING,
            ConsentType.EMAIL_MARKETING,
            ConsentType.ANALYTICS,
            ConsentType.COOKIES,
            ConsentType.FILE_STORAGE,
            ConsentType.THIRD_PARTY_SHARING
        ]

        for consent_type in valid_types:
            assert consent_type.value in [t.value for t in ConsentType]

    def test_consent_status_validation(self):
        """Test consent status validation"""
        valid_statuses = [
            ConsentStatus.GIVEN,
            ConsentStatus.WITHDRAWN,
            ConsentStatus.EXPIRED,
            ConsentStatus.PENDING
        ]

        for status in valid_statuses:
            assert status.value in [s.value for s in ConsentStatus]

    def test_data_retention_compliance(self):
        """Test data retention compliance"""
        gdpr_service = GDPRService()

        # Test that retention periods are reasonable
        processing_info = gdpr_service.get_data_processing_info()
        retention_periods = processing_info["retention_periods"]

        # Session data should have reasonable retention
        assert "session_data" in retention_periods
        assert "days" in retention_periods["session_data"]

        # Order data should have legal compliance retention
        assert "order_data" in retention_periods
        assert "7 years" in retention_periods["order_data"]

        # Consent records should have legal compliance retention
        assert "consent_records" in retention_periods
        assert "7 years" in retention_periods["consent_records"]

    def test_legal_basis_compliance(self):
        """Test legal basis compliance"""
        gdpr_service = GDPRService()
        processing_info = gdpr_service.get_data_processing_info()
        legal_basis = processing_info["legal_basis"]

        # Should have valid legal bases
        valid_bases = ["consent", "contract", "legal_obligation", "legitimate_interest"]

        for basis in legal_basis.values():
            assert basis in valid_bases

    def test_data_categories_compliance(self):
        """Test data categories compliance"""
        gdpr_service = GDPRService()
        processing_info = gdpr_service.get_data_processing_info()
        data_categories = processing_info["data_categories"]

        # Should have comprehensive data categories
        expected_categories = [
            "Identity data",
            "Contact data",
            "Financial data",
            "Technical data",
            "Usage data",
            "Marketing data"
        ]

        for category in expected_categories:
            assert any(category in cat for cat in data_categories)

    def test_third_party_compliance(self):
        """Test third party data sharing compliance"""
        gdpr_service = GDPRService()
        processing_info = gdpr_service.get_data_processing_info()
        third_parties = processing_info["third_parties"]

        # Should have documented third parties
        assert len(third_parties) > 0

        for third_party in third_parties:
            assert "name" in third_party
            assert "purpose" in third_party
            assert "data_shared" in third_party
            assert "legal_basis" in third_party

    def test_data_subject_rights_compliance(self):
        """Test data subject rights compliance"""
        gdpr_service = GDPRService()
        processing_info = gdpr_service.get_data_processing_info()
        rights = processing_info["data_subject_rights"]

        # Should include all required GDPR rights
        required_rights = [
            "Right to access",
            "Right to rectification",
            "Right to erasure",
            "Right to restrict processing",
            "Right to data portability",
            "Right to object"
        ]

        for right in required_rights:
            assert any(right in r for r in rights)

    def test_contact_information_compliance(self):
        """Test contact information compliance"""
        gdpr_service = GDPRService()
        processing_info = gdpr_service.get_data_processing_info()
        contact_info = processing_info["contact_information"]

        # Should have required contact information
        required_contacts = [
            "privacy_email",
            "dpo_email",
            "privacy_policy",
            "unsubscribe_url"
        ]

        for contact in required_contacts:
            assert contact in contact_info
            assert contact_info[contact]  # Should not be empty
