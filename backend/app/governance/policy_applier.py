"""
Policy Applier Service - Apply governance rules based on classification

Handles:
- Matching classification → policies
- Executing actions (masking, access restriction, audit)
- Enforcing RBAC
- Logging compliance actions
"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.catalog_models import (
    GovernancePolicy, MetadataClassification, CatalogTable, CatalogColumn, AuditLog
)
import re
import datetime
import uuid

logger = logging.getLogger(__name__)


class PolicyApplier:
    """
    Applies governance policies to data access and masking.
    
    Workflow:
    1. User queries table
    2. Get table classification
    3. Find matching policies
    4. For each policy, execute action
    5. Return masked/restricted result
    6. Log to AuditLog
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def apply_policies(self, query_result: List[Dict], 
                            query: str, user_id: str, table_id: str,
                            user_roles: List[str] = None) -> Dict[str, Any]:
        """
        Apply all matching policies to query result.
        
        Returns:
        {
            'original_rows': N,
            'masked_rows': M,
            'result': [masked result],
            'policies_applied': [policy_names],
            'access_level': 'full' | 'masked' | 'denied',
            'audit_id': UUID
        }
        """
        logger.info(f"Applying policies for user={user_id}, table={table_id}")
        
        if user_roles is None:
            user_roles = []
        
        # Get table classification
        stmt = select(MetadataClassification).where(MetadataClassification.table_id == table_id)
        result = await self.db.execute(stmt)
        classification = result.scalar_one_or_none()
        
        if not classification:
            logger.debug(f"No classification for table {table_id}, no policies apply")
            await self._log_audit(
                user_id=user_id,
                action='query_executed',
                resource_id=table_id,
                resource_type='table',
                access_level='full',
                rows_returned=len(query_result),
                rows_masked=0
            )
            return {
                'original_rows': len(query_result),
                'masked_rows': 0,
                'result': query_result,
                'policies_applied': [],
                'access_level': 'full'
            }
        
        # Find matching policies
        policies = await self._find_matching_policies(classification, user_roles)
        logger.info(f"Found {len(policies)} matching policies")
        
        # Check access restrictions first
        for policy in policies:
            if policy.action_type == 'restrict_access':
                # Check if user has bypass role
                if not any(role in (policy.allowed_roles or []) for role in user_roles):
                    logger.warning(f"Access denied for user {user_id} on table {table_id}")
                    await self._log_audit(
                        user_id=user_id,
                        action='access_denied',
                        resource_id=table_id,
                        resource_type='table',
                        access_level='denied',
                        denial_reason='Restricted access policy enforced',
                        rows_returned=0,
                        rows_masked=0
                    )
                    return {
                        'original_rows': len(query_result),
                        'masked_rows': len(query_result),
                        'result': [],
                        'policies_applied': [p.name for p in policies],
                        'access_level': 'denied'
                    }
        
        # Apply masking policies
        masked_result = query_result.copy()
        columns_masked = []
        total_values_masked = 0
        
        for policy in policies:
            if policy.action_type == 'mask':
                masked_result, count, cols = await self._apply_masking_policy(
                    masked_result, policy, classification
                )
                total_values_masked += count
                columns_masked.extend(cols)
        
        # Log audit
        audit_id = await self._log_audit(
            user_id=user_id,
            action='query_executed',
            resource_id=table_id,
            resource_type='table',
            query_executed=query,
            access_level='masked' if total_values_masked > 0 else 'full',
            rows_returned=len(query_result),
            rows_masked=total_values_masked,
            columns_masked=list(set(columns_masked))
        )
        
        result = {
            'original_rows': len(query_result),
            'masked_rows': total_values_masked,
            'result': masked_result,
            'policies_applied': [p.name for p in policies],
            'access_level': 'masked' if total_values_masked > 0 else 'full',
            'audit_id': audit_id
        }
        
        logger.info(f"Policies applied: {len(policies)}, values masked: {total_values_masked}")
        return result
    
    async def _find_matching_policies(self, classification: MetadataClassification,
                                     user_roles: List[str]) -> List[GovernancePolicy]:
        """Find all policies matching this classification"""
        stmt = select(GovernancePolicy).where(
            GovernancePolicy.enabled == True
        )
        result = await self.db.execute(stmt)
        all_policies = result.scalars().all()
        
        matching = []
        for policy in all_policies:
            # Check sensitivity level match
            if policy.sensitivity_level and policy.sensitivity_level != classification.sensitivity_level:
                continue
            
            # Check PII condition match
            if policy.contains_pii_condition is not None:
                if policy.contains_pii_condition != classification.contains_pii:
                    continue
            
            # Check if user has bypass role
            bypass_roles = policy.allowed_roles or []
            if any(role in bypass_roles for role in user_roles):
                logger.debug(f"User has bypass role for policy {policy.name}")
                continue
            
            matching.append(policy)
        
        return matching
    
    async def _apply_masking_policy(self, data: List[Dict], policy: GovernancePolicy,
                                   classification: MetadataClassification) -> tuple:
        """
        Apply masking policy to data.
        
        Returns: (masked_data, values_masked_count, columns_masked_list)
        """
        logger.debug(f"Applying masking policy: {policy.name}")
        
        masked_data = []
        values_masked = 0
        columns_masked = []
        
        for row in data:
            masked_row = row.copy()
            
            for col_name, col_value in row.items():
                if col_value is None:
                    continue
                
                # Apply masking based on policy params
                mask_type = policy.action_params.get('mask_type') if policy.action_params else 'generic'
                masked_value, was_masked = self._mask_value(col_value, mask_type)
                
                if was_masked:
                    masked_row[col_name] = masked_value
                    values_masked += 1
                    if col_name not in columns_masked:
                        columns_masked.append(col_name)
            
            masked_data.append(masked_row)
        
        return masked_data, values_masked, columns_masked
    
    def _mask_value(self, value: Any, mask_type: str) -> tuple:
        """
        Mask a single value.
        
        Returns: (masked_value, was_masked)
        """
        value_str = str(value)
        
        if mask_type == 'email' and '@' in value_str:
            # Show first 3 + ****@domain
            parts = value_str.split('@')
            if len(parts[0]) > 3:
                masked = parts[0][:3] + '****@' + parts[1]
            else:
                masked = '*' * len(parts[0]) + '@' + parts[1]
            return masked, True
        
        elif mask_type == 'ssn' and len(value_str) >= 9:
            # Show last 4 only
            return '***-**-' + value_str[-4:], True
        
        elif mask_type == 'credit_card' and len(value_str) >= 4:
            # Show last 4 only
            return '****-****-****-' + value_str[-4:], True
        
        elif mask_type == 'phone' and len(value_str) >= 4:
            # Show last 4 only
            return '****-****-' + value_str[-4:], True
        
        elif mask_type == 'name':
            # Show first letter + ****
            if len(value_str) > 0:
                return value_str[0] + '****', True
        
        elif mask_type == 'generic':
            # Default: show ****
            return '****', True
        
        elif mask_type == 'custom' and 'mask_pattern' in mask_type:
            # Use regex pattern
            pattern = mask_type.get('mask_pattern', '****')
            return pattern, True
        
        return value, False
    
    async def check_policy_compliance(self, table_id: str) -> Dict:
        """
        Verify all policies are properly applied to a table.
        
        Returns compliance status and violations.
        """
        logger.info(f"Checking policy compliance for table {table_id}")
        
        # Get classification
        stmt = select(MetadataClassification).where(MetadataClassification.table_id == table_id)
        result = await self.db.execute(stmt)
        classification = result.scalar_one_or_none()
        
        if not classification:
            return {
                'table_id': table_id,
                'compliant': True,
                'message': 'No classification, no policies apply'
            }
        
        violations = []
        
        # Check PII is properly masked
        if classification.contains_pii and not classification.masking_enabled:
            violations.append('PII detected but masking not enabled')
        
        # Check access restrictions
        if classification.access_restricted and not classification.allowed_roles:
            violations.append('Access restricted but no allowed roles defined')
        
        # Check masking policies exist
        policies = await self._find_matching_policies(classification, [])
        if classification.contains_pii and not any(p.action_type == 'mask' for p in policies):
            violations.append('PII detected but no masking policy applies')
        
        compliant = len(violations) == 0
        
        return {
            'table_id': table_id,
            'compliant': compliant,
            'violations': violations,
            'policies_applied': len(policies),
            'pii_detected': classification.contains_pii,
            'masking_enabled': classification.masking_enabled,
            'access_restricted': classification.access_restricted
        }
    
    async def _log_audit(self, user_id: str, action: str, resource_id: str,
                        resource_type: str, access_level: str = 'full',
                        query_executed: Optional[str] = None,
                        rows_returned: int = 0, rows_masked: int = 0,
                        columns_masked: Optional[List[str]] = None,
                        denial_reason: Optional[str] = None) -> str:
        """Log audit entry for compliance"""
        audit_id = str(uuid.uuid4())
        
        audit_log = AuditLog(
            id=audit_id,
            workspace_id="default",
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            query_executed=query_executed,
            rows_returned=rows_returned,
            rows_masked=rows_masked,
            columns_masked=columns_masked or [],
            access_level=access_level,
            denial_reason=denial_reason,
            timestamp=datetime.datetime.utcnow()
        )
        
        self.db.add(audit_log)
        await self.db.commit()
        
        logger.debug(f"Audit logged: {audit_id}")
        return audit_id
