# Enterprise Security Architecture & Compliance Framework

## 🛡️ Executive Summary

This document outlines a comprehensive security architecture and compliance framework for the enterprise-scale League of Legends prediction system. The security model implements defense-in-depth principles, zero-trust architecture, and enterprise-grade compliance requirements to protect user data, intellectual property, and system integrity.

---

## 🔒 Security Architecture Overview

### Security Principles

```yaml
Core Security Principles:
  - Zero Trust: Never trust, always verify
  - Defense in Depth: Multiple layers of security controls
  - Least Privilege: Minimum necessary access rights
  - Fail Secure: Default to secure state on failures
  - Privacy by Design: Privacy considerations in all decisions
  - Continuous Monitoring: Real-time threat detection and response

Security Objectives:
  - Confidentiality: Protect sensitive data and intellectual property
  - Integrity: Ensure data accuracy and prevent unauthorized modification
  - Availability: Maintain system availability against attacks
  - Authenticity: Verify identity of users and systems
  - Non-repudiation: Provide proof of transactions and actions
```

### Threat Model

```yaml
Primary Threats:
  External Threats:
    - DDoS attacks and availability disruption
    - Data breaches and unauthorized access
    - API abuse and rate limit bypassing
    - Injection attacks (SQL, NoSQL, XSS)
    - Man-in-the-middle attacks
    - Social engineering and phishing

  Internal Threats:
    - Insider threats and privileged access abuse
    - Accidental data exposure
    - Configuration errors and misconfigurations
    - Supply chain attacks through dependencies
    - Data exfiltration and intellectual property theft

  Compliance Risks:
    - GDPR violations and privacy breaches
    - Data residency requirement violations
    - Audit trail and logging deficiencies
    - Inadequate access controls and monitoring
```

---

## 🌐 Network Security Architecture

### Zero Trust Network Model

```yaml
Network Segmentation:
  DMZ (Public):
    - Load balancers and API gateways
    - CDN edge nodes
    - Public-facing services only
    - No direct database access

  Application Tier (Private):
    - Microservices and application logic
    - Service mesh with mTLS
    - No internet access (NAT Gateway only)
    - Encrypted inter-service communication

  Data Tier (Highly Restricted):
    - Database and storage systems
    - ML model serving infrastructure
    - No direct external access
    - Strict access controls and auditing

  Management Tier (Admin Only):
    - Administrative tools and dashboards
    - CI/CD infrastructure
    - Monitoring and logging systems
    - VPN and bastion host access only
```

### Kubernetes Network Policies

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: prediction-engine-policy
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: prediction-engine
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: api-gateway
    - podSelector:
        matchLabels:
          app: api-gateway
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: data
    - podSelector:
        matchLabels:
          app: redis-cluster
    ports:
    - protocol: TCP
      port: 6379
  - to:
    - namespaceSelector:
        matchLabels:
          name: data
    - podSelector:
        matchLabels:
          app: postgresql
    ports:
    - protocol: TCP
      port: 5432
  - to: []  # Allow DNS resolution
    ports:
    - protocol: UDP
      port: 53

---
# Database tier - highly restricted
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: database-isolation-policy
  namespace: data
spec:
  podSelector:
    matchLabels:
      tier: database
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: production
    - podSelector:
        matchLabels:
          tier: application
    ports:
    - protocol: TCP
      port: 5432
  egress:
  - to: []  # Deny all egress except DNS
    ports:
    - protocol: UDP
      port: 53
```

### Service Mesh Security (Istio)

```yaml
# mTLS Policy - Enforce mutual TLS for all services
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: production
spec:
  mtls:
    mode: STRICT

---
# Authorization Policy - Service-level access control
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: prediction-engine-authz
  namespace: production
spec:
  selector:
    matchLabels:
      app: prediction-engine
  rules:
  - from:
    - source:
        principals: ["cluster.local/ns/production/sa/api-gateway"]
  - to:
    - operation:
        methods: ["POST"]
        paths: ["/predict", "/predict-batch"]
  - when:
    - key: request.headers[authorization]
      values: ["Bearer *"]

---
# Rate Limiting Policy
apiVersion: networking.istio.io/v1alpha3
kind: EnvoyFilter
metadata:
  name: rate-limit-filter
  namespace: production
spec:
  configPatches:
  - applyTo: HTTP_FILTER
    match:
      context: SIDECAR_INBOUND
      listener:
        filterChain:
          filter:
            name: "envoy.filters.network.http_connection_manager"
    patch:
      operation: INSERT_BEFORE
      value:
        name: envoy.filters.http.local_ratelimit
        typed_config:
          "@type": type.googleapis.com/udpa.type.v1.TypedStruct
          type_url: type.googleapis.com/envoy.extensions.filters.http.local_ratelimit.v3.LocalRateLimit
          value:
            stat_prefix: local_rate_limiter
            token_bucket:
              max_tokens: 1000
              tokens_per_fill: 1000
              fill_interval: 60s
            filter_enabled:
              runtime_key: local_rate_limit_enabled
              default_value:
                numerator: 100
                denominator: HUNDRED
            filter_enforced:
              runtime_key: local_rate_limit_enforced
              default_value:
                numerator: 100
                denominator: HUNDRED
```

### VPC Security Configuration

```hcl
# Terraform configuration for secure VPC
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = {
    Name        = "lol-prediction-vpc"
    Environment = "production"
    Security    = "high"
  }
}

# Private subnets for application and data tiers
resource "aws_subnet" "private" {
  count             = 3
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 1}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]
  
  tags = {
    Name = "private-subnet-${count.index + 1}"
    Tier = "private"
  }
}

# Public subnets for load balancers only
resource "aws_subnet" "public" {
  count                   = 3
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.${count.index + 101}.0/24"
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true
  
  tags = {
    Name = "public-subnet-${count.index + 1}"
    Tier = "public"
  }
}

# Database subnets with enhanced isolation
resource "aws_subnet" "database" {
  count             = 3
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 201}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]
  
  tags = {
    Name = "database-subnet-${count.index + 1}"
    Tier = "database"
  }
}

# Security groups with least privilege
resource "aws_security_group" "api_gateway" {
  name_prefix = "api-gateway-"
  vpc_id      = aws_vpc.main.id
  
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS from internet"
  }
  
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTP redirect to HTTPS"
  }
  
  egress {
    from_port       = 8080
    to_port         = 8080
    protocol        = "tcp"
    security_groups = [aws_security_group.application.id]
    description     = "To application tier"
  }
  
  tags = {
    Name = "api-gateway-sg"
    Tier = "public"
  }
}

resource "aws_security_group" "application" {
  name_prefix = "application-"
  vpc_id      = aws_vpc.main.id
  
  ingress {
    from_port       = 8080
    to_port         = 8080
    protocol        = "tcp"
    security_groups = [aws_security_group.api_gateway.id]
    description     = "From API gateway"
  }
  
  egress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.database.id]
    description     = "To PostgreSQL"
  }
  
  egress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.cache.id]
    description     = "To Redis cache"
  }
  
  tags = {
    Name = "application-sg"
    Tier = "private"
  }
}

resource "aws_security_group" "database" {
  name_prefix = "database-"
  vpc_id      = aws_vpc.main.id
  
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.application.id]
    description     = "From application tier"
  }
  
  # No egress rules - database should not initiate outbound connections
  tags = {
    Name = "database-sg"
    Tier = "database"
  }
}
```

---

## 🔐 Identity & Access Management

### Authentication Architecture

#### Multi-Factor Authentication
```yaml
Primary Authentication Methods:
  - Username/Password with bcrypt hashing (cost factor 12)
  - OAuth2/OpenID Connect (Google, Discord, Riot Games)
  - API keys for programmatic access
  - Service-to-service JWT tokens

MFA Requirements:
  - Required for all admin accounts
  - Required for premium/enterprise users
  - Optional but incentivized for free users
  - TOTP (Google Authenticator, Authy)
  - SMS backup (rate-limited)
  - Hardware security keys (FIDO2/WebAuthn)

Session Management:
  - JWT tokens with 15-minute expiration
  - Refresh tokens with 30-day expiration
  - Secure, HttpOnly, SameSite cookies
  - Session invalidation on suspicious activity
  - Concurrent session limits by user tier
```

#### OAuth2 Implementation
```python
# Secure OAuth2 implementation with PKCE
import hashlib
import base64
import secrets
from authlib.integrations.flask_oauth2 import ResourceProtector
from authlib.oauth2.rfc7636 import CodeChallenge

class SecureOAuth2Server:
    def __init__(self):
        self.require_proof_key = True
        self.supported_response_types = ['code']
        self.supported_grant_types = ['authorization_code', 'refresh_token']
        self.token_expires_in = 900  # 15 minutes
        self.refresh_token_expires_in = 86400 * 30  # 30 days
    
    def generate_authorization_code(self, client_id: str, user_id: str, scope: str, 
                                  code_challenge: str, code_challenge_method: str):
        """Generate secure authorization code with PKCE"""
        
        # Validate PKCE parameters
        if not code_challenge or code_challenge_method != 'S256':
            raise ValueError("PKCE required with S256 method")
        
        # Generate cryptographically secure authorization code
        code = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
        
        # Store code with associated data (Redis with 10-minute expiration)
        code_data = {
            'client_id': client_id,
            'user_id': user_id,
            'scope': scope,
            'code_challenge': code_challenge,
            'code_challenge_method': code_challenge_method,
            'created_at': time.time()
        }
        
        redis_client.setex(f"auth_code:{code}", 600, json.dumps(code_data))
        return code
    
    def validate_code_challenge(self, code_verifier: str, code_challenge: str):
        """Validate PKCE code challenge"""
        derived_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        ).decode().rstrip('=')
        
        return secrets.compare_digest(derived_challenge, code_challenge)
    
    def generate_tokens(self, user_id: str, client_id: str, scope: str):
        """Generate access and refresh tokens"""
        
        # Access token (JWT)
        access_token_payload = {
            'sub': user_id,
            'client_id': client_id,
            'scope': scope,
            'iat': time.time(),
            'exp': time.time() + self.token_expires_in,
            'aud': 'lol-prediction-api',
            'iss': 'lol-prediction-auth'
        }
        
        access_token = jwt.encode(access_token_payload, JWT_SECRET_KEY, algorithm='HS256')
        
        # Refresh token (random, stored in database)
        refresh_token = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8')
        
        # Store refresh token in database
        store_refresh_token(refresh_token, user_id, client_id, scope, 
                          expires_at=time.time() + self.refresh_token_expires_in)
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': self.token_expires_in,
            'scope': scope
        }
```

### Authorization Framework (RBAC + ABAC)

#### Role-Based Access Control
```yaml
User Roles:
  guest:
    permissions:
      - read:public_predictions
      - create:free_predictions (rate limited)
    limits:
      - 10 predictions/day
      - Basic features only

  registered:
    inherits: guest
    permissions:
      - read:own_predictions
      - create:predictions (increased limit)
      - update:own_profile
    limits:
      - 100 predictions/day
      - Access to prediction history

  premium:
    inherits: registered
    permissions:
      - read:advanced_analytics
      - create:unlimited_predictions
      - access:premium_features
    limits:
      - Unlimited predictions
      - Advanced analytics dashboard

  pro:
    inherits: premium
    permissions:
      - access:api_keys
      - read:bulk_analytics
      - create:custom_models
    limits:
      - API access
      - Bulk operations
      - Custom model training

  enterprise:
    inherits: pro
    permissions:
      - access:admin_dashboard
      - manage:team_users
      - access:white_label
    limits:
      - Team management
      - White-label customization
      - Priority support

Administrative Roles:
  support:
    permissions:
      - read:user_profiles
      - read:prediction_history
      - update:user_support_flags
    restrictions:
      - Cannot modify predictions
      - Cannot access financial data
      - All actions audited

  analyst:
    permissions:
      - read:analytics_data
      - read:model_performance
      - create:analytics_reports
    restrictions:
      - Read-only access
      - No user data modification
      - Aggregated data only

  admin:
    permissions:
      - ALL (with audit logging)
    restrictions:
      - Requires MFA
      - All actions logged
      - Break-glass access only

  system:
    permissions:
      - service:to:service communication
      - automated:operations
    restrictions:
      - No user data access
      - Service accounts only
      - Certificate-based auth
```

#### Attribute-Based Access Control
```python
# ABAC policy engine for fine-grained access control
class ABACPolicyEngine:
    def __init__(self):
        self.policies = self.load_policies()
    
    def evaluate_access(self, subject: dict, resource: dict, action: str, context: dict) -> bool:
        """Evaluate access request against ABAC policies"""
        
        # Subject attributes
        user_id = subject.get('user_id')
        user_role = subject.get('role')
        user_tier = subject.get('subscription_tier')
        user_location = subject.get('location')
        
        # Resource attributes
        resource_type = resource.get('type')
        resource_owner = resource.get('owner_id')
        resource_sensitivity = resource.get('sensitivity_level')
        
        # Context attributes
        request_time = context.get('timestamp')
        request_ip = context.get('ip_address')
        request_source = context.get('source')
        
        # Apply policies in order
        for policy in self.policies:
            result = self.evaluate_policy(policy, subject, resource, action, context)
            if result in ['PERMIT', 'DENY']:
                self.log_access_decision(policy['id'], result, subject, resource, action)
                return result == 'PERMIT'
        
        # Default deny
        self.log_access_decision('default', 'DENY', subject, resource, action)
        return False
    
    def evaluate_policy(self, policy: dict, subject: dict, resource: dict, 
                       action: str, context: dict) -> str:
        """Evaluate a single ABAC policy"""
        
        # Example policy: Users can only access their own predictions
        if policy['id'] == 'own_data_access':
            if (resource.get('type') == 'prediction' and 
                resource.get('owner_id') == subject.get('user_id')):
                return 'PERMIT'
        
        # Example policy: Premium users can access advanced features
        if policy['id'] == 'premium_features':
            if (subject.get('subscription_tier') in ['premium', 'pro', 'enterprise'] and
                resource.get('type') == 'advanced_feature'):
                return 'PERMIT'
        
        # Example policy: Geographic data restrictions
        if policy['id'] == 'data_residency':
            user_region = self.get_region_from_location(subject.get('location'))
            data_region = resource.get('data_region')
            
            if user_region == 'EU' and data_region != 'EU':
                return 'DENY'  # GDPR compliance
        
        # Example policy: Time-based access restrictions
        if policy['id'] == 'business_hours':
            current_hour = datetime.now().hour
            if resource.get('type') == 'admin_feature' and not (9 <= current_hour <= 17):
                return 'DENY'
        
        return 'NOT_APPLICABLE'

# Policy definitions in JSON
ABAC_POLICIES = [
    {
        "id": "own_data_access",
        "description": "Users can only access their own data",
        "version": "1.0",
        "rule": {
            "target": {
                "subject": {"role": ["registered", "premium", "pro", "enterprise"]},
                "resource": {"type": ["prediction", "profile", "analytics"]},
                "action": ["read", "update", "delete"]
            },
            "condition": "subject.user_id == resource.owner_id"
        },
        "effect": "PERMIT"
    },
    {
        "id": "api_rate_limiting",
        "description": "API rate limits based on subscription tier",
        "version": "1.0",
        "rule": {
            "target": {
                "subject": {"source": "api"},
                "resource": {"type": "prediction_request"},
                "action": "create"
            },
            "condition": {
                "free": "request_count_today < 10",
                "registered": "request_count_today < 100",
                "premium": "request_count_per_minute < 60",
                "pro": "request_count_per_minute < 600",
                "enterprise": "request_count_per_minute < 6000"
            }
        },
        "effect": "CONDITIONAL_PERMIT"
    }
]
```

### API Security

#### API Gateway Security
```yaml
Kong Gateway Security Configuration:
  Authentication Plugins:
    - JWT validation with RS256 algorithm
    - API key authentication for service accounts
    - OAuth2 introspection for third-party access
    - Rate limiting per consumer and globally

  Security Plugins:
    - CORS handling with strict origin validation
    - Request size limiting (1MB max)
    - Response transformation to hide internal data
    - IP restriction for admin endpoints
    - Bot detection and CAPTCHA integration

  Rate Limiting Strategy:
    Global Limits:
      - 10,000 requests/minute (burst: 15,000)
      - 1,000 requests/minute per IP
      - 100 concurrent connections per IP

    Per-User Limits:
      - Free: 100 requests/day
      - Premium: 10,000 requests/day
      - Pro: 100,000 requests/day
      - Enterprise: Unlimited (monitored)

    Per-Endpoint Limits:
      - /predict: 60 requests/minute (premium+)
      - /predict-batch: 10 requests/minute (pro+)
      - /analytics: 600 requests/hour (premium+)
```

#### API Security Headers
```nginx
# Security headers configuration
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' fonts.googleapis.com; font-src 'self' fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self' api.outscaled.gg wss://api.outscaled.gg; frame-ancestors 'none';" always;
add_header Permissions-Policy "geolocation=(), microphone=(), camera=(), fullscreen=(self), payment=()" always;

# Remove server identification
server_tokens off;
more_clear_headers Server;
```

---

## 🔒 Data Protection & Privacy

### Data Classification & Handling

```yaml
Data Classification Levels:
  Public:
    - Marketing materials and public documentation
    - Aggregated, anonymized statistics
    - Public API documentation
    Handling: Standard web security practices

  Internal:
    - Business intelligence reports
    - Operational metrics and logs
    - Non-sensitive configuration data
    Handling: Access controls, audit logging

  Confidential:
    - User profiles and preferences
    - Prediction history and analytics
    - Business strategy and financial data
    Handling: Encryption at rest, role-based access

  Restricted:
    - Authentication credentials and tokens
    - Personal identification information (PII)
    - Payment and financial information
    - ML model algorithms and parameters
    Handling: Strong encryption, strict access controls, audit trails

  Top Secret:
    - Master encryption keys
    - Administrative credentials
    - Security vulnerability information
    Handling: Hardware security modules, multi-person control
```

### Encryption Strategy

#### Data at Rest Encryption
```yaml
Database Encryption:
  PostgreSQL:
    - Transparent Data Encryption (TDE) with AES-256
    - Column-level encryption for PII data
    - Key rotation every 90 days
    - Hardware Security Module (HSM) key storage

  Redis:
    - Encryption at rest with customer-managed keys
    - In-memory encryption for sensitive cache data
    - Automatic key rotation
    - Cluster-wide encryption consistency

  ClickHouse:
    - Full disk encryption with dm-crypt
    - Application-level encryption for sensitive columns
    - Compressed encryption for optimal performance

File Storage Encryption:
  S3 Data Lake:
    - Server-side encryption with AWS KMS
    - Customer-managed encryption keys (CMK)
    - Bucket key optimization for cost efficiency
    - Cross-region replication with encryption

  Container Images:
    - Encrypted container registry
    - Signed images with Docker Content Trust
    - Vulnerability scanning and remediation
    - Base image security and patching
```

#### Data in Transit Encryption
```yaml
Network Encryption:
  External Communications:
    - TLS 1.3 for all client connections
    - Perfect Forward Secrecy (PFS)
    - Certificate pinning for mobile apps
    - HSTS with long max-age and preload

  Internal Communications:
    - mTLS for all service-to-service communication
    - Istio service mesh encryption
    - VPN tunnels for admin access
    - Database connection encryption

API Security:
  - HTTPS everywhere with HTTP -> HTTPS redirects
  - API request/response encryption
  - Webhook payload signing and verification
  - GraphQL query depth limiting and analysis
```

#### Key Management System
```python
# Enterprise key management implementation
import boto3
import hvac
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class EnterpriseKeyManager:
    def __init__(self):
        self.kms_client = boto3.client('kms')
        self.vault_client = hvac.Client(url='https://vault.internal')
        self.key_hierarchy = {
            'master': 'aws-kms',  # AWS KMS for master key
            'dek': 'vault',       # HashiCorp Vault for data encryption keys
            'session': 'local'    # Local generation for session keys
        }
    
    def get_data_encryption_key(self, purpose: str, context: dict = None):
        """Get or create data encryption key for specific purpose"""
        
        key_path = f"secret/data/dek/{purpose}"
        
        try:
            # Try to retrieve existing key from Vault
            response = self.vault_client.secrets.kv.v2.read_secret_version(path=key_path)
            key_data = response['data']['data']
            
            return {
                'key': key_data['key'],
                'version': key_data['version'],
                'created_at': key_data['created_at']
            }
        
        except hvac.exceptions.InvalidPath:
            # Generate new key if not exists
            return self.create_data_encryption_key(purpose, context)
    
    def create_data_encryption_key(self, purpose: str, context: dict = None):
        """Create new data encryption key using AWS KMS"""
        
        # Generate data key using AWS KMS
        response = self.kms_client.generate_data_key(
            KeyId='alias/lol-prediction-master-key',
            KeySpec='AES_256',
            EncryptionContext=context or {}
        )
        
        # Store encrypted key in Vault
        key_data = {
            'key': response['CiphertextBlob'].hex(),
            'plaintext_key': response['Plaintext'].hex(),
            'purpose': purpose,
            'created_at': time.time(),
            'version': 1,
            'encryption_context': context
        }
        
        # Store in Vault (only encrypted version)
        vault_data = {k: v for k, v in key_data.items() if k != 'plaintext_key'}
        
        self.vault_client.secrets.kv.v2.create_or_update_secret(
            path=f"secret/data/dek/{purpose}",
            secret=vault_data
        )
        
        return key_data
    
    def rotate_key(self, purpose: str):
        """Rotate data encryption key"""
        
        # Create new version of the key
        new_key = self.create_data_encryption_key(f"{purpose}_v2")
        
        # Update key version in Vault
        self.vault_client.secrets.kv.v2.create_or_update_secret(
            path=f"secret/data/dek/{purpose}",
            secret={
                **new_key,
                'version': new_key['version'] + 1,
                'rotated_at': time.time()
            }
        )
        
        # Schedule old key deprecation
        self.schedule_key_deprecation(purpose, delay_days=30)
        
        return new_key

    def encrypt_sensitive_data(self, data: str, purpose: str, context: dict = None):
        """Encrypt sensitive data with purpose-specific key"""
        
        # Get data encryption key
        key_info = self.get_data_encryption_key(purpose, context)
        
        # Decrypt the key using KMS
        decrypted_key = self.kms_client.decrypt(
            CiphertextBlob=bytes.fromhex(key_info['key']),
            EncryptionContext=context or {}
        )
        
        # Create Fernet cipher
        fernet = Fernet(base64.urlsafe_b64encode(decrypted_key['Plaintext']))
        
        # Encrypt data
        encrypted_data = fernet.encrypt(data.encode())
        
        return {
            'encrypted_data': encrypted_data.hex(),
            'key_version': key_info['version'],
            'purpose': purpose,
            'encrypted_at': time.time()
        }
```

### Privacy Compliance (GDPR/CCPA)

#### Data Minimization & Purpose Limitation
```yaml
Data Collection Principles:
  - Collect only necessary data for service functionality
  - Explicit consent for each data processing purpose
  - Regular data audits and cleanup procedures
  - Automated data retention and deletion policies

Purpose Definitions:
  Service Delivery:
    - User account management and authentication
    - Prediction generation and result delivery
    - Performance monitoring and optimization
    - Customer support and issue resolution

  Analytics & Improvement:
    - Service usage analytics (aggregated)
    - Model performance analysis
    - User experience optimization
    - Product development insights

  Marketing & Communication:
    - Newsletter and product updates (opt-in only)
    - Promotional offers and feature announcements
    - User surveys and feedback collection

  Legal & Compliance:
    - Audit trails and security monitoring
    - Fraud prevention and detection
    - Legal obligation compliance
    - Regulatory reporting requirements
```

#### Right to Deletion Implementation
```python
# GDPR Right to Deletion (Right to be Forgotten)
class GDPRDeletionService:
    def __init__(self):
        self.deletion_queue = Queue()
        self.data_sources = [
            'postgresql_primary',
            'redis_cache',
            'clickhouse_analytics',
            's3_data_lake',
            'elasticsearch_logs'
        ]
    
    async def process_deletion_request(self, user_id: str, verification_token: str):
        """Process user's right to deletion request"""
        
        # Verify user identity and request legitimacy
        if not await self.verify_deletion_request(user_id, verification_token):
            raise InvalidDeletionRequest("Invalid verification token")
        
        # Create deletion task
        deletion_task = {
            'user_id': user_id,
            'requested_at': datetime.utcnow(),
            'status': 'pending',
            'data_sources': self.data_sources,
            'verification_token': verification_token,
            'deletion_id': str(uuid.uuid4())
        }
        
        # Add to processing queue
        await self.deletion_queue.put(deletion_task)
        
        # Log deletion request for audit
        await self.log_deletion_request(deletion_task)
        
        return {
            'deletion_id': deletion_task['deletion_id'],
            'status': 'pending',
            'estimated_completion': datetime.utcnow() + timedelta(days=30),
            'contact_info': 'privacy@outscaled.gg'
        }
    
    async def execute_deletion(self, deletion_task: dict):
        """Execute the actual data deletion across all systems"""
        
        user_id = deletion_task['user_id']
        deletion_results = []
        
        try:
            # 1. PostgreSQL - User data and predictions
            pg_result = await self.delete_from_postgresql(user_id)
            deletion_results.append(('postgresql', pg_result))
            
            # 2. Redis - Cache and session data
            redis_result = await self.delete_from_redis(user_id)
            deletion_results.append(('redis', redis_result))
            
            # 3. ClickHouse - Analytics data (anonymize rather than delete)
            ch_result = await self.anonymize_analytics_data(user_id)
            deletion_results.append(('clickhouse', ch_result))
            
            # 4. S3 Data Lake - User-specific data
            s3_result = await self.delete_from_s3(user_id)
            deletion_results.append(('s3', s3_result))
            
            # 5. Elasticsearch - Search indexes and logs
            es_result = await self.delete_from_elasticsearch(user_id)
            deletion_results.append(('elasticsearch', es_result))
            
            # 6. External services notification
            await self.notify_external_services(user_id, 'deletion')
            
            # Create deletion certificate
            certificate = await self.generate_deletion_certificate(
                deletion_task['deletion_id'], 
                deletion_results
            )
            
            return {
                'status': 'completed',
                'completed_at': datetime.utcnow(),
                'deletion_results': deletion_results,
                'certificate': certificate
            }
            
        except Exception as e:
            # Log error and create partial deletion report
            await self.log_deletion_error(deletion_task['deletion_id'], str(e))
            
            return {
                'status': 'failed',
                'error': str(e),
                'partial_results': deletion_results,
                'manual_intervention_required': True
            }
    
    async def delete_from_postgresql(self, user_id: str):
        """Delete user data from PostgreSQL with transaction safety"""
        
        deletion_queries = [
            "DELETE FROM prediction_feedback WHERE user_id = %s",
            "DELETE FROM prediction_requests WHERE user_id = %s",
            "DELETE FROM user_sessions WHERE user_id = %s",
            "DELETE FROM user_auth_methods WHERE user_id = %s",
            "DELETE FROM user_profiles WHERE user_id = %s",
            "DELETE FROM audit_logs WHERE user_id = %s",
            "DELETE FROM users WHERE user_id = %s"
        ]
        
        async with get_db_transaction() as tx:
            deleted_counts = {}
            
            for query in deletion_queries:
                table_name = query.split(" FROM ")[1].split(" WHERE")[0]
                result = await tx.execute(query, (user_id,))
                deleted_counts[table_name] = result.rowcount
            
            await tx.commit()
            
        return {
            'status': 'success',
            'deleted_records': deleted_counts,
            'total_records': sum(deleted_counts.values())
        }
    
    async def anonymize_analytics_data(self, user_id: str):
        """Anonymize rather than delete analytics data for business intelligence"""
        
        # Replace user_id with anonymous hash
        anonymous_id = hashlib.sha256(f"anon_{user_id}_{secrets.token_hex(16)}".encode()).hexdigest()
        
        anonymization_queries = [
            f"ALTER TABLE user_events UPDATE user_id = '{anonymous_id}' WHERE user_id = '{user_id}'",
            f"ALTER TABLE prediction_analytics UPDATE user_id = '{anonymous_id}' WHERE user_id = '{user_id}'"
        ]
        
        anonymized_records = 0
        for query in anonymization_queries:
            result = await clickhouse_client.execute(query)
            anonymized_records += result
        
        return {
            'status': 'anonymized',
            'anonymized_records': anonymized_records,
            'anonymous_id': anonymous_id[:16] + "..."  # Partial ID for verification
        }
```

---

## 🔍 Security Monitoring & Incident Response

### Security Information and Event Management (SIEM)

#### Log Aggregation & Analysis
```yaml
Log Sources:
  Application Logs:
    - Authentication events (success/failure)
    - Authorization decisions
    - Prediction requests and responses
    - User actions and state changes
    - Error conditions and exceptions

  Infrastructure Logs:
    - Network traffic and firewall logs
    - Load balancer access logs
    - Database connection and query logs
    - Container lifecycle events
    - Kubernetes API server logs

  Security Logs:
    - IDS/IPS alerts and signatures
    - DDoS protection events
    - Certificate and TLS events
    - Vulnerability scan results
    - Patch management activities

Analysis Rules:
  Authentication Anomalies:
    - Multiple failed login attempts from same IP
    - Login from unusual geographic location
    - Multiple simultaneous sessions
    - Credential stuffing patterns
    - Privilege escalation attempts

  Data Access Anomalies:
    - Unusual data access patterns
    - Large-scale data exports
    - Access to sensitive data outside business hours
    - API abuse and rate limit violations
    - Bulk operations by single user

  Infrastructure Anomalies:
    - Unusual network traffic patterns
    - Resource utilization spikes
    - Unauthorized service communications
    - Configuration changes outside change windows
    - New processes or network connections
```

#### Elasticsearch Security Monitoring
```json
{
  "index_patterns": ["security-logs-*"],
  "settings": {
    "number_of_shards": 3,
    "number_of_replicas": 1,
    "index.lifecycle.name": "security-logs-policy",
    "index.lifecycle.rollover_alias": "security-logs"
  },
  "mappings": {
    "properties": {
      "@timestamp": {"type": "date"},
      "event_type": {"type": "keyword"},
      "severity": {"type": "keyword"},
      "user_id": {"type": "keyword"},
      "ip_address": {"type": "ip"},
      "user_agent": {"type": "text"},
      "endpoint": {"type": "keyword"},
      "status_code": {"type": "integer"},
      "response_time": {"type": "integer"},
      "geolocation": {
        "properties": {
          "country": {"type": "keyword"},
          "region": {"type": "keyword"},
          "city": {"type": "keyword"},
          "coordinates": {"type": "geo_point"}
        }
      },
      "threat_indicators": {
        "properties": {
          "risk_score": {"type": "integer"},
          "threat_type": {"type": "keyword"},
          "confidence": {"type": "float"}
        }
      }
    }
  }
}
```

### Threat Detection & Response

#### Automated Threat Detection
```python
# Real-time threat detection system
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

class ThreatDetectionEngine:
    def __init__(self):
        self.models = {
            'authentication_anomaly': IsolationForest(contamination=0.1),
            'api_abuse_detection': IsolationForest(contamination=0.05),
            'data_access_anomaly': IsolationForest(contamination=0.02)
        }
        self.scalers = {}
        self.baseline_metrics = {}
        
    def train_models(self, historical_data: pd.DataFrame):
        """Train anomaly detection models on historical data"""
        
        # Authentication anomaly detection
        auth_features = [
            'login_frequency', 'failed_attempts', 'session_duration',
            'geographic_distance', 'device_change', 'time_since_last_login'
        ]
        
        auth_data = historical_data[auth_features].fillna(0)
        self.scalers['authentication'] = StandardScaler()
        auth_scaled = self.scalers['authentication'].fit_transform(auth_data)
        self.models['authentication_anomaly'].fit(auth_scaled)
        
        # API abuse detection
        api_features = [
            'requests_per_minute', 'error_rate', 'response_time_avg',
            'unique_endpoints', 'data_volume', 'geographic_diversity'
        ]
        
        api_data = historical_data[api_features].fillna(0)
        self.scalers['api'] = StandardScaler()
        api_scaled = self.scalers['api'].fit_transform(api_data)
        self.models['api_abuse_detection'].fit(api_scaled)
        
        # Data access anomaly detection
        data_features = [
            'data_volume_accessed', 'access_frequency', 'unusual_hours',
            'sensitive_data_ratio', 'export_frequency', 'query_complexity'
        ]
        
        data_access = historical_data[data_features].fillna(0)
        self.scalers['data'] = StandardScaler()
        data_scaled = self.scalers['data'].fit_transform(data_access)
        self.models['data_access_anomaly'].fit(data_scaled)
    
    def detect_threats(self, current_metrics: dict):
        """Detect threats in real-time metrics"""
        
        threats = []
        
        # Authentication anomaly detection
        auth_score = self.detect_authentication_anomaly(current_metrics)
        if auth_score < -0.5:  # Anomaly threshold
            threats.append({
                'type': 'authentication_anomaly',
                'severity': 'high' if auth_score < -0.8 else 'medium',
                'score': auth_score,
                'details': self.analyze_auth_anomaly(current_metrics)
            })
        
        # API abuse detection
        api_score = self.detect_api_abuse(current_metrics)
        if api_score < -0.3:
            threats.append({
                'type': 'api_abuse',
                'severity': 'high' if api_score < -0.7 else 'medium',
                'score': api_score,
                'details': self.analyze_api_abuse(current_metrics)
            })
        
        # Data access anomaly
        data_score = self.detect_data_anomaly(current_metrics)
        if data_score < -0.4:
            threats.append({
                'type': 'data_access_anomaly',
                'severity': 'critical' if data_score < -0.8 else 'high',
                'score': data_score,
                'details': self.analyze_data_anomaly(current_metrics)
            })
        
        return threats
    
    def respond_to_threat(self, threat: dict, user_context: dict):
        """Automated threat response based on threat type and severity"""
        
        responses = []
        
        if threat['severity'] == 'critical':
            # Immediate account suspension
            responses.append(self.suspend_user_account(user_context['user_id']))
            responses.append(self.notify_security_team(threat, user_context))
            responses.append(self.preserve_forensic_evidence(threat, user_context))
        
        elif threat['severity'] == 'high':
            # Require additional authentication
            responses.append(self.require_mfa_challenge(user_context['user_id']))
            responses.append(self.increase_monitoring(user_context['user_id']))
            responses.append(self.alert_security_team(threat, user_context))
        
        elif threat['severity'] == 'medium':
            # Enhanced monitoring and rate limiting
            responses.append(self.apply_rate_limiting(user_context['user_id']))
            responses.append(self.log_security_event(threat, user_context))
        
        return responses

# Real-time threat monitoring
async def monitor_threats():
    detector = ThreatDetectionEngine()
    
    while True:
        # Collect current metrics
        current_metrics = await collect_security_metrics()
        
        # Detect threats
        threats = detector.detect_threats(current_metrics)
        
        # Respond to threats
        for threat in threats:
            user_context = await get_user_context(threat)
            responses = detector.respond_to_threat(threat, user_context)
            
            # Execute responses
            for response in responses:
                await execute_security_response(response)
        
        # Wait before next check
        await asyncio.sleep(10)  # 10-second monitoring interval
```

### Incident Response Plan

#### Incident Classification & Response
```yaml
Incident Severity Levels:
  P1 - Critical:
    Definition: Data breach, service unavailable, security compromise
    Response Time: 15 minutes
    Escalation: Immediate CEO and legal notification
    Actions:
      - Activate incident response team
      - Isolate affected systems
      - Preserve forensic evidence
      - Notify legal and compliance teams
      - Prepare public communication

  P2 - High:
    Definition: Performance degradation, partial service outage, security vulnerability
    Response Time: 1 hour
    Escalation: CTO and security team notification
    Actions:
      - Deploy incident response team
      - Implement temporary mitigations
      - Begin root cause analysis
      - Monitor for escalation

  P3 - Medium:
    Definition: Minor service issues, non-critical security events
    Response Time: 4 hours
    Escalation: Team lead notification
    Actions:
      - Assign to on-call engineer
      - Implement standard procedures
      - Document incident details

  P4 - Low:
    Definition: Monitoring alerts, routine maintenance issues
    Response Time: 24 hours
    Escalation: Create ticket for next business day
    Actions:
      - Schedule during business hours
      - Follow standard procedures
```

#### Security Incident Response Team
```yaml
Team Structure:
  Incident Commander:
    - Overall incident coordination
    - Communication with stakeholders
    - Decision-making authority
    - Resource allocation

  Security Lead:
    - Technical security analysis
    - Threat assessment and containment
    - Forensic evidence preservation
    - Security tool coordination

  Engineering Lead:
    - System restoration and recovery
    - Technical mitigation implementation
    - Performance and availability monitoring
    - Infrastructure coordination

  Communications Lead:
    - Internal stakeholder communication
    - External customer communication
    - Legal and regulatory notification
    - Media and public relations

  Legal/Compliance Lead:
    - Regulatory requirement assessment
    - Legal liability evaluation
    - Compliance notification requirements
    - Evidence handling procedures

On-Call Rotation:
  - 24/7 coverage with 2-person minimum
  - Primary and secondary responders
  - Escalation procedures for no-response
  - Cross-training for role coverage
```

This comprehensive security architecture provides enterprise-grade protection for the League of Legends prediction system, with defense-in-depth strategies, zero-trust principles, and robust compliance frameworks to protect user data and maintain system integrity at scale.