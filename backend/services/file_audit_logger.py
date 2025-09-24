"""
File Operation Audit Logger

This service provides comprehensive logging for all file operations to maintain
an audit trail for security, compliance, and debugging purposes.
"""

import logging
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass, asdict
from pathlib import Path
import os

from sqlalchemy.orm import Session
from sqlalchemy import Column, String, DateTime, Text, Integer, Boolean
from sqlalchemy.ext.declarative import declarative_base

# Configure logging
logger = logging.getLogger(__name__)

# Create a separate base for audit logs
AuditBase = declarative_base()

class FileOperationType(Enum):
    """Types of file operations that can be logged"""
    UPLOAD = "upload"
    DOWNLOAD = "download"
    DELETE = "delete"
    MIGRATE = "migrate"
    COPY = "copy"
    MOVE = "move"
    ACCESS = "access"
    GENERATE = "generate"
    PROCESS = "process"
    ENCRYPT = "encrypt"
    DECRYPT = "decrypt"

class FileOperationStatus(Enum):
    """Status of file operations"""
    SUCCESS = "success"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"
    CANCELLED = "cancelled"

class FileType(Enum):
    """Types of files being operated on"""
    PHOTO = "photo"
    AUDIO = "audio"
    PDF = "pdf"
    WAVEFORM = "waveform"
    TEMPLATE = "template"
    BACKGROUND = "background"
    FONT = "font"
    OTHER = "other"

@dataclass
class FileOperationContext:
    """Context information for file operations"""
    user_identifier: Optional[str] = None
    session_token: Optional[str] = None
    order_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    api_endpoint: Optional[str] = None
    additional_metadata: Optional[Dict[str, Any]] = None

@dataclass
class FileOperationDetails:
    """Detailed information about a file operation"""
    source_path: Optional[str] = None
    destination_path: Optional[str] = None
    file_size: Optional[int] = None
    file_hash: Optional[str] = None
    content_type: Optional[str] = None
    encryption_status: Optional[str] = None
    processing_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    additional_details: Optional[Dict[str, Any]] = None

class FileAuditLog(AuditBase):
    """Database model for file operation audit logs"""
    __tablename__ = "file_audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    operation_type = Column(String(50), nullable=False)
    file_type = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Context information
    user_identifier = Column(String(255))
    session_token = Column(String(255))
    order_id = Column(String(255))
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(Text)
    request_id = Column(String(255))
    api_endpoint = Column(String(255))

    # File operation details
    source_path = Column(Text)
    destination_path = Column(Text)
    file_size = Column(Integer)
    file_hash = Column(String(64))
    content_type = Column(String(100))
    encryption_status = Column(String(50))
    processing_time_ms = Column(Integer)
    error_message = Column(Text)

    # Additional metadata
    additional_metadata = Column(Text)  # JSON string
    additional_details = Column(Text)   # JSON string

    # Compliance fields
    retention_date = Column(DateTime(timezone=True))
    is_sensitive = Column(Boolean, default=False)
    legal_basis = Column(String(100))

class FileAuditLogger:
    """Service for logging file operations with comprehensive audit trails"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.retention_days = 2555  # 7 years for compliance

    def log_file_operation(self,
                          operation_type: FileOperationType,
                          file_type: FileType,
                          status: FileOperationStatus,
                          context: FileOperationContext,
                          details: FileOperationDetails,
                          db: Session) -> str:
        """
        Log a file operation with comprehensive details

        Args:
            operation_type: Type of file operation
            file_type: Type of file being operated on
            status: Status of the operation
            context: Context information about the operation
            details: Detailed information about the file operation
            db: Database session

        Returns:
            Log entry ID
        """
        try:
            # Create audit log entry
            audit_log = FileAuditLog(
                operation_type=operation_type.value,
                file_type=file_type.value,
                status=status.value,
                timestamp=datetime.now(timezone.utc),

                # Context information
                user_identifier=context.user_identifier,
                session_token=context.session_token,
                order_id=context.order_id,
                ip_address=context.ip_address,
                user_agent=context.user_agent,
                request_id=context.request_id,
                api_endpoint=context.api_endpoint,

                # File operation details
                source_path=details.source_path,
                destination_path=details.destination_path,
                file_size=details.file_size,
                file_hash=details.file_hash,
                content_type=details.content_type,
                encryption_status=details.encryption_status,
                processing_time_ms=details.processing_time_ms,
                error_message=details.error_message,

                # Additional metadata
                additional_metadata=json.dumps(context.additional_metadata) if context.additional_metadata else None,
                additional_details=json.dumps(details.additional_details) if details.additional_details else None,

                # Compliance fields
                retention_date=datetime.now(timezone.utc).replace(year=datetime.now(timezone.utc).year + 7),
                is_sensitive=self._is_sensitive_file(file_type, details.content_type),
                legal_basis=self._get_legal_basis(operation_type, file_type)
            )

            db.add(audit_log)
            db.commit()
            db.refresh(audit_log)

            # Also log to application logs for immediate visibility
            self._log_to_application_logs(audit_log)

            return audit_log.id

        except Exception as e:
            self.logger.error(f"Failed to log file operation: {str(e)}")
            # Don't raise exception to avoid breaking the main operation
            return None

    def log_file_upload(self,
                       file_type: FileType,
                       file_path: str,
                       file_size: int,
                       content_type: str,
                       context: FileOperationContext,
                       status: FileOperationStatus = FileOperationStatus.SUCCESS,
                       error_message: Optional[str] = None,
                       processing_time_ms: Optional[int] = None,
                       db: Session = None) -> str:
        """Log a file upload operation"""
        details = FileOperationDetails(
            destination_path=file_path,
            file_size=file_size,
            content_type=content_type,
            processing_time_ms=processing_time_ms,
            error_message=error_message
        )

        return self.log_file_operation(
            FileOperationType.UPLOAD,
            file_type,
            status,
            context,
            details,
            db
        )

    def log_file_download(self,
                         file_type: FileType,
                         file_path: str,
                         context: FileOperationContext,
                         status: FileOperationStatus = FileOperationStatus.SUCCESS,
                         error_message: Optional[str] = None,
                         processing_time_ms: Optional[int] = None,
                         db: Session = None) -> str:
        """Log a file download operation"""
        details = FileOperationDetails(
            source_path=file_path,
            processing_time_ms=processing_time_ms,
            error_message=error_message
        )

        return self.log_file_operation(
            FileOperationType.DOWNLOAD,
            file_type,
            status,
            context,
            details,
            db
        )

    def log_file_deletion(self,
                         file_type: FileType,
                         file_path: str,
                         context: FileOperationContext,
                         status: FileOperationStatus = FileOperationStatus.SUCCESS,
                         error_message: Optional[str] = None,
                         db: Session = None) -> str:
        """Log a file deletion operation"""
        details = FileOperationDetails(
            source_path=file_path,
            error_message=error_message
        )

        return self.log_file_operation(
            FileOperationType.DELETE,
            file_type,
            status,
            context,
            details,
            db
        )

    def log_file_migration(self,
                          file_type: FileType,
                          source_path: str,
                          destination_path: str,
                          file_size: int,
                          context: FileOperationContext,
                          status: FileOperationStatus = FileOperationStatus.SUCCESS,
                          error_message: Optional[str] = None,
                          processing_time_ms: Optional[int] = None,
                          db: Session = None) -> str:
        """Log a file migration operation"""
        details = FileOperationDetails(
            source_path=source_path,
            destination_path=destination_path,
            file_size=file_size,
            processing_time_ms=processing_time_ms,
            error_message=error_message
        )

        return self.log_file_operation(
            FileOperationType.MIGRATE,
            file_type,
            status,
            context,
            details,
            db
        )

    def log_file_processing(self,
                           file_type: FileType,
                           file_path: str,
                           processing_type: str,
                           context: FileOperationContext,
                           status: FileOperationStatus = FileOperationStatus.SUCCESS,
                           error_message: Optional[str] = None,
                           processing_time_ms: Optional[int] = None,
                           db: Session = None) -> str:
        """Log a file processing operation"""
        details = FileOperationDetails(
            source_path=file_path,
            processing_time_ms=processing_time_ms,
            error_message=error_message,
            additional_details={"processing_type": processing_type}
        )

        return self.log_file_operation(
            FileOperationType.PROCESS,
            file_type,
            status,
            context,
            details,
            db
        )

    def get_audit_logs(self,
                      db: Session,
                      user_identifier: Optional[str] = None,
                      session_token: Optional[str] = None,
                      operation_type: Optional[FileOperationType] = None,
                      file_type: Optional[FileType] = None,
                      status: Optional[FileOperationStatus] = None,
                      start_date: Optional[datetime] = None,
                      end_date: Optional[datetime] = None,
                      limit: int = 100,
                      offset: int = 0) -> List[Dict[str, Any]]:
        """Retrieve audit logs with filtering options"""
        try:
            query = db.query(FileAuditLog)

            # Apply filters
            if user_identifier:
                query = query.filter(FileAuditLog.user_identifier == user_identifier)
            if session_token:
                query = query.filter(FileAuditLog.session_token == session_token)
            if operation_type:
                query = query.filter(FileAuditLog.operation_type == operation_type.value)
            if file_type:
                query = query.filter(FileAuditLog.file_type == file_type.value)
            if status:
                query = query.filter(FileAuditLog.status == status.value)
            if start_date:
                query = query.filter(FileAuditLog.timestamp >= start_date)
            if end_date:
                query = query.filter(FileAuditLog.timestamp <= end_date)

            # Order by timestamp descending and apply pagination
            logs = query.order_by(FileAuditLog.timestamp.desc()).offset(offset).limit(limit).all()

            # Convert to dictionaries
            result = []
            for log in logs:
                log_dict = {
                    "id": log.id,
                    "operation_type": log.operation_type,
                    "file_type": log.file_type,
                    "status": log.status,
                    "timestamp": log.timestamp.isoformat(),
                    "user_identifier": log.user_identifier,
                    "session_token": log.session_token,
                    "order_id": log.order_id,
                    "ip_address": log.ip_address,
                    "source_path": log.source_path,
                    "destination_path": log.destination_path,
                    "file_size": log.file_size,
                    "content_type": log.content_type,
                    "processing_time_ms": log.processing_time_ms,
                    "error_message": log.error_message,
                    "additional_metadata": json.loads(log.additional_metadata) if log.additional_metadata else None,
                    "additional_details": json.loads(log.additional_details) if log.additional_details else None
                }
                result.append(log_dict)

            return result

        except Exception as e:
            self.logger.error(f"Failed to retrieve audit logs: {str(e)}")
            return []

    def get_audit_statistics(self,
                           db: Session,
                           start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get audit statistics for monitoring and reporting"""
        try:
            query = db.query(FileAuditLog)

            if start_date:
                query = query.filter(FileAuditLog.timestamp >= start_date)
            if end_date:
                query = query.filter(FileAuditLog.timestamp <= end_date)

            logs = query.all()

            # Calculate statistics
            total_operations = len(logs)
            successful_operations = len([log for log in logs if log.status == FileOperationStatus.SUCCESS.value])
            failed_operations = len([log for log in logs if log.status == FileOperationStatus.FAILED.value])

            # Group by operation type
            operation_types = {}
            for log in logs:
                op_type = log.operation_type
                if op_type not in operation_types:
                    operation_types[op_type] = 0
                operation_types[op_type] += 1

            # Group by file type
            file_types = {}
            for log in logs:
                file_type = log.file_type
                if file_type not in file_types:
                    file_types[file_type] = 0
                file_types[file_type] += 1

            # Calculate total file size processed
            total_size = sum(log.file_size or 0 for log in logs)

            # Calculate average processing time
            processing_times = [log.processing_time_ms for log in logs if log.processing_time_ms]
            avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0

            return {
                "total_operations": total_operations,
                "successful_operations": successful_operations,
                "failed_operations": failed_operations,
                "success_rate": (successful_operations / total_operations * 100) if total_operations > 0 else 0,
                "operation_types": operation_types,
                "file_types": file_types,
                "total_file_size_bytes": total_size,
                "average_processing_time_ms": avg_processing_time,
                "date_range": {
                    "start": start_date.isoformat() if start_date else None,
                    "end": end_date.isoformat() if end_date else None
                }
            }

        except Exception as e:
            self.logger.error(f"Failed to get audit statistics: {str(e)}")
            return {}

    def cleanup_old_logs(self, db: Session) -> int:
        """Clean up audit logs older than retention period"""
        try:
            cutoff_date = datetime.now(timezone.utc).replace(year=datetime.now(timezone.utc).year - 7)

            old_logs = db.query(FileAuditLog).filter(
                FileAuditLog.timestamp < cutoff_date
            ).all()

            count = len(old_logs)

            for log in old_logs:
                db.delete(log)

            db.commit()

            self.logger.info(f"Cleaned up {count} old audit logs")
            return count

        except Exception as e:
            self.logger.error(f"Failed to cleanup old audit logs: {str(e)}")
            db.rollback()
            return 0

    def _is_sensitive_file(self, file_type: FileType, content_type: Optional[str]) -> bool:
        """Determine if a file contains sensitive data"""
        sensitive_types = {
            FileType.PHOTO: True,  # Photos may contain personal information
            FileType.AUDIO: True,  # Audio may contain personal information
            FileType.PDF: True,    # PDFs may contain personal information
        }

        return sensitive_types.get(file_type, False)

    def _get_legal_basis(self, operation_type: FileOperationType, file_type: FileType) -> str:
        """Get the legal basis for the file operation"""
        if operation_type in [FileOperationType.UPLOAD, FileOperationType.PROCESS, FileOperationType.GENERATE]:
            return "contract"  # Necessary for service delivery
        elif operation_type == FileOperationType.DELETE:
            return "legal_obligation"  # Data retention compliance
        elif operation_type == FileOperationType.DOWNLOAD:
            return "consent"  # User requested access
        else:
            return "legitimate_interest"  # System operations

    def _log_to_application_logs(self, audit_log: FileAuditLog):
        """Log to application logs for immediate visibility"""
        log_message = (
            f"File Operation: {audit_log.operation_type} | "
            f"Type: {audit_log.file_type} | "
            f"Status: {audit_log.status} | "
            f"User: {audit_log.user_identifier or 'anonymous'} | "
            f"Path: {audit_log.source_path or audit_log.destination_path}"
        )

        if audit_log.status == FileOperationStatus.SUCCESS.value:
            self.logger.info(log_message)
        elif audit_log.status == FileOperationStatus.FAILED.value:
            self.logger.error(f"{log_message} | Error: {audit_log.error_message}")
        else:
            self.logger.warning(log_message)

# Global instance
file_audit_logger = FileAuditLogger()
