import re
import math
from typing import Dict, Any, List, Optional, Tuple
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.catalog_models import CatalogTable, CatalogColumn, CatalogProfile, MetadataClassification
from app.connectors.connector_factory import ConnectorFactory
from app.services.connection_manager import ConnectionManager


class PIIDetector:
    """
    Enterprise PII Detection Engine.
    Uses regex, column name analysis, entropy detection, and sample data inspection.
    Provides confidence scoring (0-1) for each detection method.
    """
    
    PII_PATTERNS = {
        "email": r"^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$",
        "phone": r"^(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}$",
        "ssn": r"^\d{3}-\d{2}-\d{4}$",
        "credit_card": r"^\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}$",
        "passport": r"^[A-Z]{1,2}\d{6,9}$",
        "pan": r"^[A-Z]{5}\d{4}[A-Z]{1}$",  # Indian PAN
        "aadhaar": r"^\d{4}\s?\d{4}\s?\d{4}$",  # Indian Aadhaar
        "ipv4": r"^(\d{1,3}\.){3}\d{1,3}$",
    }

    COLUMN_NAME_HINTS = {
        "email": ["email", "mail", "e_mail", "email_addr", "email_address"],
        "phone": ["phone", "tel", "telephone", "mobile", "contact_no", "contact_number"],
        "ssn": ["ssn", "social_security", "social_security_number", "ssn_number"],
        "name": ["name", "first_name", "last_name", "full_name", "person_name"],
        "address": ["address", "street", "street_address", "city", "zip", "postal_code"],
        "password": ["password", "pwd", "passwd", "secret", "token", "apikey", "api_key"],
        "credit_card": ["credit_card", "card_number", "cc_number", "cardno"],
        "passport": ["passport", "passport_no", "passport_number"],
        "pan": ["pan", "pan_number", "tax_id"],
        "aadhaar": ["aadhaar", "aadhaar_no", "aadhaar_number", "uid"],
    }

    def is_sensitive_key(self, key: str) -> bool:
        """
        Fast check to see if a key (column name) is likely sensitive.
        Used for real-time masking in streams.
        """
        key_lower = key.lower()
        for pii_type, hints in self.COLUMN_NAME_HINTS.items():
            if any(hint == key_lower for hint in hints):
                return True
        return False

    def __init__(self, db: AsyncSession):
        self.db = db

    async def scan_column(self, column_id: str) -> Optional[Dict[str, Any]]:
        """
        Scans a column for PII using multiple methods.
        Returns: {pii_type, confidence, methods_used}
        """
        stmt = select(CatalogColumn).where(CatalogColumn.id == column_id).options(
            selectinload(CatalogColumn.table)
        )
        result = await self.db.execute(stmt)
        column = result.scalar_one_or_none()
        if not column:
            return None

        logger.info(f"Scanning column for PII: {column.name}")

        # Multi-method detection with confidence scoring
        detection_result = await self._multi_method_detect(column)

        if detection_result:
            pii_type = detection_result['pii_type']
            confidence = detection_result['confidence']
            
            # Update column metadata
            column.pii_tag = pii_type
            
            # Set sensitivity level based on PII type
            if pii_type in ["ssn", "credit_card", "password", "passport", "pan", "aadhaar"]:
                sensitivity_level = "restricted"
            elif pii_type in ["email", "phone", "name"]:
                sensitivity_level = "confidential"
            else:
                sensitivity_level = "internal"
            
            column.sensitivity_level = sensitivity_level
            
            # Create or update classification record
            stmt = select(MetadataClassification).where(
                MetadataClassification.column_id == column_id
            )
            res = await self.db.execute(stmt)
            classification = res.scalar_one_or_none()
            
            if not classification:
                classification = MetadataClassification(
                    table_id=column.table_id,
                    column_id=column_id
                )
                self.db.add(classification)
            
            classification.contains_pii = True
            classification.pii_types = [pii_type]
            classification.sensitivity_level = sensitivity_level
            classification.auto_detected = True
            classification.detection_confidence = confidence
            classification.classified_by = "pii_detector_auto"
            
            await self.db.commit()
            logger.info(f"PII Detected in {column.name}: {pii_type} (confidence: {confidence:.2f})")
            
            return detection_result
        
        return None

    async def _multi_method_detect(self, column: CatalogColumn) -> Optional[Dict[str, Any]]:
        """
        Detect PII using multiple methods and combine scores.
        Returns best detection or None.
        """
        detections = []

        # Method 1: Column name analysis (high weight)
        name_result = self._analyze_name(column.name)
        if name_result:
            detections.append({"method": "column_name", "type": name_result, "confidence": 0.85})

        # Method 2: Data analysis (high weight)
        data_result = await self._analyze_data(column)
        if data_result:
            detections.append({"method": "data_pattern", "type": data_result["type"], "confidence": data_result["confidence"]})

        # Method 3: Entropy analysis (medium weight)
        entropy_result = await self._analyze_entropy(column)
        if entropy_result:
            detections.append({"method": "entropy", "type": entropy_result["type"], "confidence": entropy_result["confidence"]})

        # Method 4: Semantic hints (low weight)
        semantic_result = self._analyze_semantic(column.name, column.data_type if hasattr(column, 'data_type') else None)
        if semantic_result:
            detections.append({"method": "semantic", "type": semantic_result["type"], "confidence": semantic_result["confidence"]})

        if not detections:
            return None

        # Combine results: higher confidence takes precedence
        best = max(detections, key=lambda x: x['confidence'])
        
        # If multiple methods agree on same type, boost confidence
        same_type_count = sum(1 for d in detections if d['type'] == best['type'])
        if same_type_count > 1:
            boosted_confidence = min(1.0, best['confidence'] + (0.05 * (same_type_count - 1)))
        else:
            boosted_confidence = best['confidence']

        return {
            'pii_type': best['type'],
            'confidence': boosted_confidence,
            'methods': [d['method'] for d in detections]
        }

    def _analyze_name(self, name: str) -> Optional[str]:
        """Method 1: Analyze column name for PII hints"""
        name_lower = name.lower()
        for pii_type, hints in self.COLUMN_NAME_HINTS.items():
            if any(hint in name_lower for hint in hints):
                return pii_type
        return None

    def _analyze_semantic(self, name: str, data_type: Optional[str]) -> Optional[Dict[str, Any]]:
        """Method 4: Semantic hints from naming patterns and types"""
        name_lower = name.lower()
        
        # Semantic rules
        if 'uuid' in name_lower and 'token' in name_lower:
            return {"type": "password", "confidence": 0.6}
        
        if 'hash' in name_lower and ('password' in name_lower or 'pwd' in name_lower):
            return {"type": "password", "confidence": 0.7}
        
        if 'date' in data_type.lower() if data_type else False:
            if 'birth' in name_lower or 'dob' in name_lower:
                return {"type": "date_of_birth", "confidence": 0.7}
        
        return None

    async def _analyze_data(self, column: CatalogColumn) -> Optional[Dict[str, Any]]:
        """Method 2: Analyze sample data against regex patterns"""
        stmt = select(CatalogProfile).where(CatalogProfile.column_id == column.id)
        result = await self.db.execute(stmt)
        profile = result.scalar_one_or_none()
        
        if not profile or not profile.top_values:
            return None

        # Check top values against patterns
        matches = {}
        for item in profile.top_values:
            val = str(item.get("value", "")).strip()
            if not val or val == "None":
                continue
            
            for pii_type, pattern in self.PII_PATTERNS.items():
                if re.match(pattern, val, re.IGNORECASE):
                    matches[pii_type] = matches.get(pii_type, 0) + 1

        if matches:
            # Best match (highest count)
            best_type = max(matches, key=matches.get)
            match_rate = matches[best_type] / len(profile.top_values)
            confidence = min(1.0, match_rate * 1.2)  # Boost confidence for matches
            return {"type": best_type, "confidence": confidence}
        
        return None

    async def _analyze_entropy(self, column: CatalogColumn) -> Optional[Dict[str, Any]]:
        """Method 3: Entropy-based detection (high entropy = likely sensitive)"""
        stmt = select(CatalogProfile).where(CatalogProfile.column_id == column.id)
        result = await self.db.execute(stmt)
        profile = result.scalar_one_or_none()
        
        if not profile or not profile.top_values:
            return None

        # Calculate entropy of top values
        entropies = []
        for item in profile.top_values:
            val = str(item.get("value", ""))
            entropy = self._calculate_entropy(val)
            entropies.append(entropy)

        if not entropies:
            return None

        avg_entropy = sum(entropies) / len(entropies)
        
        # High entropy suggests encoded/hashed data (passwords, tokens)
        if avg_entropy > 4.5:
            return {"type": "password", "confidence": 0.7}
        
        return None

    def _calculate_entropy(self, s: str) -> float:
        """Calculate Shannon entropy of a string"""
        if not s:
            return 0.0
        
        # Frequency of characters
        freq = {}
        for char in s:
            freq[char] = freq.get(char, 0) + 1
        
        # Calculate entropy
        entropy = 0.0
        for count in freq.values():
            p = count / len(s)
            if p > 0:
                entropy -= p * math.log2(p)
        
        return entropy

    async def scan_table(self, table_id: str) -> Dict[str, Any]:
        """
        Scan all columns in a table for PII.
        Returns count of detected PII columns.
        """
        logger.info(f"Scanning table for PII: {table_id}")
        
        stmt = select(CatalogTable).where(CatalogTable.id == table_id).options(
            selectinload(CatalogTable.columns)
        )
        result = await self.db.execute(stmt)
        table = result.scalar_one_or_none()
        
        if not table:
            return {"table_id": table_id, "status": "not_found"}

        pii_count = 0
        for column in table.columns:
            detection = await self.scan_column(column.id)
            if detection:
                pii_count += 1

        return {
            "table_id": table_id,
            "total_columns": len(table.columns),
            "pii_columns_detected": pii_count,
            "status": "completed"
        }

    async def scan_connection(self, connection_id: str) -> Dict[str, Any]:
        """
        Scan all tables in a connection for PII.
        Returns statistics.
        """
        logger.info(f"Scanning connection for PII: {connection_id}")
        
        stmt = select(CatalogTable).where(CatalogTable.connection_id == connection_id)
        result = await self.db.execute(stmt)
        tables = result.scalars().all()

        total_pii = 0
        for table in tables:
            result = await self.scan_table(table.id)
            total_pii += result.get("pii_columns_detected", 0)

        return {
            "connection_id": connection_id,
            "total_tables_scanned": len(tables),
            "total_pii_columns": total_pii,
            "status": "completed"
        }

