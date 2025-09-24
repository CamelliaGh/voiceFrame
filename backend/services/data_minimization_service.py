"""
Data Minimization Service for GDPR Compliance

This service ensures that only necessary data is collected and processed,
implementing the GDPR principle of data minimization (Article 5(1)(c)).
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class DataCategory(Enum):
    """Categories of personal data for minimization purposes"""
    IDENTITY = "identity"  # Name, email, user ID
    CONTACT = "contact"    # Email, phone, address
    TECHNICAL = "technical"  # IP, browser, device info
    USAGE = "usage"       # Session data, preferences
    FINANCIAL = "financial"  # Payment data, billing
    CONTENT = "content"   # Uploaded files, generated content
    ANALYTICS = "analytics"  # Usage statistics, performance data

class ProcessingPurpose(Enum):
    """Purposes for data processing"""
    SERVICE_DELIVERY = "service_delivery"
    PAYMENT_PROCESSING = "payment_processing"
    EMAIL_COMMUNICATIONS = "email_communications"
    ANALYTICS = "analytics"
    LEGAL_COMPLIANCE = "legal_compliance"
    SECURITY = "security"
    CUSTOMER_SUPPORT = "customer_support"

@dataclass
class DataMinimizationRule:
    """Rule for data minimization"""
    category: DataCategory
    purpose: ProcessingPurpose
    required: bool
    retention_days: int
    justification: str
    alternatives: List[str]

@dataclass
class ValidationResult:
    """Result of data minimization validation"""
    is_valid: bool
    violations: List[str]
    recommendations: List[str]
    score: float  # 0-100, higher is better

class DataMinimizationService:
    """Service for enforcing data minimization principles"""

    def __init__(self):
        self.rules = self._initialize_rules()
        self.logger = logging.getLogger(__name__)

    def _initialize_rules(self) -> List[DataMinimizationRule]:
        """Initialize data minimization rules based on GDPR requirements"""
        return [
            # Identity Data
            DataMinimizationRule(
                category=DataCategory.IDENTITY,
                purpose=ProcessingPurpose.SERVICE_DELIVERY,
                required=True,
                retention_days=90,
                justification="Required for user identification and service delivery",
                alternatives=["Anonymous session tokens"]
            ),

            # Contact Data
            DataMinimizationRule(
                category=DataCategory.CONTACT,
                purpose=ProcessingPurpose.EMAIL_COMMUNICATIONS,
                required=False,
                retention_days=365,
                justification="Optional for email notifications and support",
                alternatives=["In-app notifications only"]
            ),

            # Technical Data
            DataMinimizationRule(
                category=DataCategory.TECHNICAL,
                purpose=ProcessingPurpose.SECURITY,
                required=True,
                retention_days=30,
                justification="Required for security monitoring and fraud prevention",
                alternatives=["Minimal logging, IP anonymization"]
            ),

            # Usage Data
            DataMinimizationRule(
                category=DataCategory.USAGE,
                purpose=ProcessingPurpose.SERVICE_DELIVERY,
                required=True,
                retention_days=90,
                justification="Required for session management and user preferences",
                alternatives=["Stateless sessions"]
            ),

            # Financial Data
            DataMinimizationRule(
                category=DataCategory.FINANCIAL,
                purpose=ProcessingPurpose.PAYMENT_PROCESSING,
                required=True,
                retention_days=2555,  # 7 years
                justification="Required by law for financial record keeping",
                alternatives=["Third-party payment processors only"]
            ),

            # Content Data
            DataMinimizationRule(
                category=DataCategory.CONTENT,
                purpose=ProcessingPurpose.SERVICE_DELIVERY,
                required=True,
                retention_days=90,
                justification="Required for core service functionality",
                alternatives=["User-controlled storage"]
            ),

            # Analytics Data
            DataMinimizationRule(
                category=DataCategory.ANALYTICS,
                purpose=ProcessingPurpose.ANALYTICS,
                required=False,
                retention_days=365,
                justification="Optional for service improvement",
                alternatives=["Anonymous aggregated data only"]
            )
        ]

    def validate_data_collection(self,
                                data_categories: List[DataCategory],
                                processing_purposes: List[ProcessingPurpose],
                                user_consent: Optional[Dict[str, bool]] = None) -> ValidationResult:
        """
        Validate that data collection follows minimization principles

        Args:
            data_categories: Categories of data being collected
            processing_purposes: Purposes for processing the data
            user_consent: User consent preferences

        Returns:
            ValidationResult with validation status and recommendations
        """
        violations = []
        recommendations = []

        # Check if all data categories are justified by processing purposes
        for category in data_categories:
            if not self._is_category_justified(category, processing_purposes):
                violations.append(f"Data category '{category.value}' not justified by processing purposes")
                recommendations.append(f"Consider removing '{category.value}' data or add justifying purpose")

        # Check for unnecessary data collection
        for category in data_categories:
            rule = self._get_rule_for_category(category)
            if rule and not rule.required:
                if not user_consent or not user_consent.get(category.value, False):
                    violations.append(f"Collecting optional data '{category.value}' without user consent")
                    recommendations.append(f"Either obtain consent for '{category.value}' or remove it")

        # Check for excessive data collection
        if len(data_categories) > 5:  # Arbitrary threshold
            violations.append("Collecting too many data categories")
            recommendations.append("Review if all data categories are necessary")

        # Calculate compliance score
        total_checks = len(data_categories) + len(processing_purposes)
        passed_checks = total_checks - len(violations)
        score = (passed_checks / total_checks * 100) if total_checks > 0 else 100

        return ValidationResult(
            is_valid=len(violations) == 0,
            violations=violations,
            recommendations=recommendations,
            score=score
        )

    def validate_data_retention(self,
                               data_category: DataCategory,
                               created_at: datetime,
                               current_time: Optional[datetime] = None) -> ValidationResult:
        """
        Validate that data retention follows minimization principles

        Args:
            data_category: Category of data to check
            created_at: When the data was created
            current_time: Current time (defaults to now)

        Returns:
            ValidationResult with retention validation
        """
        if current_time is None:
            current_time = datetime.utcnow()

        rule = self._get_rule_for_category(data_category)
        if not rule:
            return ValidationResult(
                is_valid=False,
                violations=[f"No retention rule found for category '{data_category.value}'"],
                recommendations=["Define retention policy for this data category"],
                score=0
            )

        age_days = (current_time - created_at).days
        violations = []
        recommendations = []

        if age_days > rule.retention_days:
            violations.append(
                f"Data category '{data_category.value}' retained for {age_days} days, "
                f"exceeds limit of {rule.retention_days} days"
            )
            recommendations.append(f"Delete data older than {rule.retention_days} days")

        # Check if data is approaching retention limit
        if age_days > rule.retention_days * 0.8:  # 80% of retention period
            recommendations.append(
                f"Data will expire in {rule.retention_days - age_days} days. "
                f"Consider cleanup process."
            )

        score = max(0, 100 - (age_days / rule.retention_days * 100))

        return ValidationResult(
            is_valid=len(violations) == 0,
            violations=violations,
            recommendations=recommendations,
            score=score
        )

    def get_minimization_recommendations(self,
                                       current_data: Dict[str, Any],
                                       processing_purposes: List[ProcessingPurpose]) -> List[str]:
        """
        Get recommendations for data minimization

        Args:
            current_data: Current data being collected
            processing_purposes: Purposes for processing

        Returns:
            List of minimization recommendations
        """
        recommendations = []

        # Check for unnecessary fields
        for field, value in current_data.items():
            if value is None or value == "":
                recommendations.append(f"Remove empty field '{field}'")

        # Check for excessive data collection
        if len(current_data) > 10:  # Arbitrary threshold
            recommendations.append("Consider reducing the number of data fields collected")

        # Check for sensitive data that might not be necessary
        sensitive_fields = ['ssn', 'passport', 'drivers_license', 'credit_card']
        for field in sensitive_fields:
            if field in current_data:
                recommendations.append(f"Review if '{field}' is necessary for service delivery")

        # Check for data that could be anonymized
        identifiable_fields = ['email', 'phone', 'address', 'ip_address']
        for field in identifiable_fields:
            if field in current_data:
                recommendations.append(f"Consider anonymizing '{field}' if not essential")

        return recommendations

    def audit_data_processing(self,
                             session_data: Dict[str, Any],
                             processing_purposes: List[ProcessingPurpose]) -> Dict[str, Any]:
        """
        Audit data processing for minimization compliance

        Args:
            session_data: Session data to audit
            processing_purposes: Purposes for processing

        Returns:
            Audit results with compliance status
        """
        audit_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "data_fields": list(session_data.keys()),
            "processing_purposes": [p.value for p in processing_purposes],
            "compliance_score": 0,
            "violations": [],
            "recommendations": [],
            "data_categories": []
        }

        # Identify data categories
        data_categories = self._identify_data_categories(session_data)
        audit_results["data_categories"] = [c.value for c in data_categories]

        # Validate data collection
        validation = self.validate_data_collection(data_categories, processing_purposes)
        audit_results["compliance_score"] = validation.score
        audit_results["violations"] = validation.violations
        audit_results["recommendations"] = validation.recommendations

        # Get additional recommendations
        additional_recommendations = self.get_minimization_recommendations(session_data, processing_purposes)
        audit_results["recommendations"].extend(additional_recommendations)

        return audit_results

    def _is_category_justified(self,
                              category: DataCategory,
                              purposes: List[ProcessingPurpose]) -> bool:
        """Check if a data category is justified by processing purposes"""
        rule = self._get_rule_for_category(category)
        if not rule:
            return False

        return any(rule.purpose == purpose for purpose in purposes)

    def _get_rule_for_category(self, category: DataCategory) -> Optional[DataMinimizationRule]:
        """Get the rule for a specific data category"""
        return next((rule for rule in self.rules if rule.category == category), None)

    def _identify_data_categories(self, data: Dict[str, Any]) -> List[DataCategory]:
        """Identify data categories from session data"""
        categories = []

        # Identity data
        if any(field in data for field in ['email', 'user_id', 'session_token']):
            categories.append(DataCategory.IDENTITY)

        # Contact data
        if any(field in data for field in ['email', 'phone', 'address']):
            categories.append(DataCategory.CONTACT)

        # Technical data
        if any(field in data for field in ['ip_address', 'user_agent', 'device_info']):
            categories.append(DataCategory.TECHNICAL)

        # Usage data
        if any(field in data for field in ['preferences', 'customizations', 'session_data']):
            categories.append(DataCategory.USAGE)

        # Content data
        if any(field in data for field in ['photo_s3_key', 'audio_s3_key', 'pdf_s3_key']):
            categories.append(DataCategory.CONTENT)

        return categories

# Global instance
data_minimization_service = DataMinimizationService()
