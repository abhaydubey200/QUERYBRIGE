import ldap3
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class LDAPAuthProvider:
    """
    Enterprise LDAP/Active Directory Authentication Provider.
    """
    def __init__(self, server_url: str, base_dn: str, admin_user: str, admin_pass: str):
        self.server_url = server_url
        self.base_dn = base_dn
        self.admin_user = admin_user
        self.admin_pass = admin_pass

    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        """
        Authenticates a user against the LDAP server.
        Returns user info if successful, None otherwise.
        """
        try:
            server = ldap3.Server(self.server_url, get_info=ldap3.ALL)
            conn = ldap3.Connection(
                server, 
                user=f"uid={username},{self.base_dn}", 
                password=password, 
                authentication=ldap3.SIMPLE
            )
            
            if conn.bind():
                logger.info(f"LDAP Auth successful for user: {username}")
                # Fetch user attributes
                conn.search(self.base_dn, f"(uid={username})", attributes=['cn', 'mail', 'memberOf'])
                if conn.entries:
                    entry = conn.entries[0]
                    return {
                        "username": username,
                        "email": str(entry.mail),
                        "full_name": str(entry.cn),
                        "groups": [str(g) for g in entry.memberOf]
                    }
            return None
        except Exception as e:
            logger.error(f"LDAP Auth error: {str(e)}")
            return None
