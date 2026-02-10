"""
Encrypted Vault - AES-256 Encryption at Rest for Personal AI Employee
Platinum Tier Security Feature
"""

import os
import json
import base64
from pathlib import Path
from typing import Optional, Dict
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EncryptedVault:
    """
    AES-256-GCM encryption for vault files
    Provides encryption at rest for sensitive tenant data
    """
    
    def __init__(self, tenant_id: str, master_key: Optional[bytes] = None):
        self.tenant_id = tenant_id
        self.key = master_key or self._derive_key_from_env()
        self.metadata_suffix = ".encrypted.meta"
    
    def _derive_key_from_env(self) -> bytes:
        """
        Derive encryption key from environment variable
        In production, use AWS KMS, Azure Key Vault, or HashiCorp Vault
        """
        # Get master password from environment
        master_password = os.getenv('VAULT_MASTER_PASSWORD', f'default-{self.tenant_id}')
        
        # WARNING: In production, use proper key management service!
        logger.warning("⚠️  Using environment-based key derivation. "
                      "For production, integrate AWS KMS or Azure Key Vault!") 
        
        # Derive key using PBKDF2
        salt = self.tenant_id.encode('utf-8')  # Tenant-specific salt
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 256 bits
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        
        return kdf.derive(master_password.encode('utf-8'))
    
    def encrypt_file(self, file_path: Path, content: str) -> str:
        """
        Encrypt file content with AES-256-GCM
        
        Args:
            file_path: Path where encrypted file will be stored
            content: Plain text content to encrypt
        
        Returns:
            Path to encrypted file
        """
        try:
            # Generate random IV (nonce) for GCM mode
            iv = os.urandom(12)  # 96 bits for GCM
            
            # Create cipher
            cipher = Cipher(
                algorithms.AES(self.key),
                modes.GCM(iv),
                backend=default_backend()
            )
            encryptor = cipher.encryptor()
            
            # Encrypt content
            content_bytes = content.encode('utf-8')
            ciphertext = encryptor.update(content_bytes) + encryptor.finalize()
            
            # Get authentication tag
            tag = encryptor.tag
            
            # Combine IV + tag + ciphertext
            encrypted_data = iv + tag + ciphertext
            
            # Encode as base64 for storage
            encrypted_b64 = base64.b64encode(encrypted_data).decode('utf-8')
            
            # Write encrypted file
            encrypted_path = str(file_path) + ".encrypted"
            with open(encrypted_path, 'w') as f:
                f.write(encrypted_b64)
            
            # Write metadata
            metadata = {
                "tenant_id": self.tenant_id,
                "original_file": str(file_path),
                "encrypted_file": encrypted_path,
                "encryption": "AES-256-GCM",
                "iv_length": 12,
                "tag_length": 16
            }
            
            meta_path = encrypted_path + ".meta"
            with open(meta_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"🔒 Encrypted: {file_path} → {encrypted_path}")
            return encrypted_path
            
        except Exception as e:
            logger.error(f"❌ Encryption failed: {e}")
            raise
    
    def decrypt_file(self, encrypted_path: Path) -> str:
        """
        Decrypt file content
        
        Args:
            encrypted_path: Path to encrypted file
        
        Returns:
            Decrypted plaintext content
        """
        try:
            # Read encrypted data
            with open(encrypted_path, 'r') as f:
                encrypted_b64 = f.read()
            
            encrypted_data = base64.b64decode(encrypted_b64)
            
            # Extract IV, tag, and ciphertext
            iv = encrypted_data[:12]
            tag = encrypted_data[12:28]
            ciphertext = encrypted_data[28:]
            
            # Create cipher with tag
            cipher = Cipher(
                algorithms.AES(self.key),
                modes.GCM(iv, tag),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            
            # Decrypt
            plaintext_bytes = decryptor.update(ciphertext) + decryptor.finalize()
            plaintext = plaintext_bytes.decode('utf-8')
            
            logger.info(f"🔓 Decrypted: {encrypted_path}")
            return plaintext
            
        except Exception as e:
            logger.error(f"❌ Decryption failed: {e}")
            raise
    
    def write_encrypted(self, file_path: Path, content: str):
        """Write content to file with encryption"""
        return self.encrypt_file(file_path, content)
    
    def read_encrypted(self, file_path: Path) -> str:
        """Read and decrypt file content"""
        # Handle both .md and .md.encrypted paths
        if not str(file_path).endswith('.encrypted'):
            encrypted_path = str(file_path) + '.encrypted'
        else:
            encrypted_path = str(file_path)
        
        return self.decrypt_file(Path(encrypted_path))
    
    def migrate_to_encrypted(self, vault_path: Path):
        """
        Migrate existing vault to encrypted format
        WARNING: This is a one-way operation!
        """
        logger.warning(f"⚠️  Migrating vault to encrypted format: {vault_path}")
        logger.warning("⚠️  This is irreversible without the encryption key!")
        
        # Find all .md files in vault
        md_files = list(vault_path.rglob("*.md"))
        logger.info(f"Found {len(md_files)} files to encrypt")
        
        encrypted_count = 0
        for md_file in md_files:
            try:
                # Read original content
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Encrypt
                self.encrypt_file(md_file, content)
                
                # Delete original (optional - keep backup!)
                # md_file.unlink()
                
                encrypted_count += 1
                
            except Exception as e:
                logger.error(f"Failed to encrypt {md_file}: {e}")
        
        logger.info(f"✅ Encrypted {encrypted_count}/{len(md_files)} files")
        logger.info("💾 Original files preserved (delete manually if needed)")


# Example usage
if __name__ == "__main__":
    # Create encrypted vault
    vault = EncryptedVault(tenant_id="tenant_001")
    
    # Test encryption
    test_file = Path("test_encrypted.md")
    test_content = """# Sensitive Task

**Client**: Acme Corp
**Payment**: $50,000
**Credentials**: admin:password123

This file should be encrypted!"""
    
    print("\n📝 Original content:")
    print(test_content)
    
    # Encrypt
    encrypted_path = vault.write_encrypted(test_file, test_content)
    print(f"\n🔒 Encrypted to: {encrypted_path}")
    
    # Decrypt
    decrypted_content = vault.read_encrypted(test_file)
    print("\n🔓 Decrypted content:")
    print(decrypted_content)
    
    # Verify match
    assert test_content == decrypted_content, "Decryption failed!"
    print("\n✅ Encryption/Decryption verified!")
    
    # Clean up
    Path(encrypted_path).unlink()
    Path(encrypted_path + ".meta").unlink()
    print("\n🧹 Test files cleaned up")
