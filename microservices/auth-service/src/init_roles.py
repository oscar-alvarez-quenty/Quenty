"""
Initialize default roles and permissions for the authentication system
"""

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from .models import Role, Permission
from .database import get_db, engine
import asyncio

# Define default permissions
DEFAULT_PERMISSIONS = [
    # User Management
    {"name": "Create Users", "code": "users:create", "category": "users", "resource": "user", "action": "create"},
    {"name": "Read Users", "code": "users:read", "category": "users", "resource": "user", "action": "read"},
    {"name": "Update Users", "code": "users:update", "category": "users", "resource": "user", "action": "update"},
    {"name": "Delete Users", "code": "users:delete", "category": "users", "resource": "user", "action": "delete"},
    {"name": "All User Operations", "code": "users:*", "category": "users", "resource": "user", "action": "*"},
    
    # Profile Management
    {"name": "Read Profile", "code": "profile:read", "category": "profile", "resource": "profile", "action": "read"},
    {"name": "Update Profile", "code": "profile:update", "category": "profile", "resource": "profile", "action": "update"},
    {"name": "All Profile Operations", "code": "profile:*", "category": "profile", "resource": "profile", "action": "*"},
    
    # Company Management
    {"name": "Create Companies", "code": "companies:create", "category": "companies", "resource": "company", "action": "create"},
    {"name": "Read Companies", "code": "companies:read", "category": "companies", "resource": "company", "action": "read"},
    {"name": "Update Companies", "code": "companies:update", "category": "companies", "resource": "company", "action": "update"},
    {"name": "Delete Companies", "code": "companies:delete", "category": "companies", "resource": "company", "action": "delete"},
    {"name": "All Company Operations", "code": "companies:*", "category": "companies", "resource": "company", "action": "*"},
    
    # Customer Management
    {"name": "Create Customers", "code": "customers:create", "category": "customers", "resource": "customer", "action": "create"},
    {"name": "Read Own Customer Data", "code": "customers:read:own", "category": "customers", "resource": "customer", "action": "read:own"},
    {"name": "Read All Customer Data", "code": "customers:read:all", "category": "customers", "resource": "customer", "action": "read:all"},
    {"name": "Update Own Customer Data", "code": "customers:update:own", "category": "customers", "resource": "customer", "action": "update:own"},
    {"name": "Update All Customer Data", "code": "customers:update:all", "category": "customers", "resource": "customer", "action": "update:all"},
    {"name": "Delete Customers", "code": "customers:delete", "category": "customers", "resource": "customer", "action": "delete"},
    {"name": "All Customer Operations", "code": "customers:*", "category": "customers", "resource": "customer", "action": "*"},
    
    # Order Management
    {"name": "Create Orders", "code": "orders:create", "category": "orders", "resource": "order", "action": "create"},
    {"name": "Read Own Orders", "code": "orders:read:own", "category": "orders", "resource": "order", "action": "read:own"},
    {"name": "Read All Orders", "code": "orders:read:all", "category": "orders", "resource": "order", "action": "read:all"},
    {"name": "Read Orders", "code": "orders:read", "category": "orders", "resource": "order", "action": "read"},
    {"name": "Update Orders", "code": "orders:update", "category": "orders", "resource": "order", "action": "update"},
    {"name": "Delete Orders", "code": "orders:delete", "category": "orders", "resource": "order", "action": "delete"},
    {"name": "All Order Operations", "code": "orders:*", "category": "orders", "resource": "order", "action": "*"},
    
    # Product Management
    {"name": "Create Products", "code": "products:create", "category": "products", "resource": "product", "action": "create"},
    {"name": "Read Products", "code": "products:read", "category": "products", "resource": "product", "action": "read"},
    {"name": "Update Products", "code": "products:update", "category": "products", "resource": "product", "action": "update"},
    {"name": "Delete Products", "code": "products:delete", "category": "products", "resource": "product", "action": "delete"},
    {"name": "All Product Operations", "code": "products:*", "category": "products", "resource": "product", "action": "*"},
    
    # Inventory Management
    {"name": "Read Inventory", "code": "inventory:read", "category": "inventory", "resource": "inventory", "action": "read"},
    {"name": "Update Inventory", "code": "inventory:update", "category": "inventory", "resource": "inventory", "action": "update"},
    {"name": "All Inventory Operations", "code": "inventory:*", "category": "inventory", "resource": "inventory", "action": "*"},
    
    # Shipping Management
    {"name": "Create Shipping", "code": "shipping:create", "category": "shipping", "resource": "shipping", "action": "create"},
    {"name": "Read Shipping", "code": "shipping:read", "category": "shipping", "resource": "shipping", "action": "read"},
    {"name": "Update Shipping", "code": "shipping:update", "category": "shipping", "resource": "shipping", "action": "update"},
    {"name": "Delete Shipping", "code": "shipping:delete", "category": "shipping", "resource": "shipping", "action": "delete"},
    {"name": "View Shipping Rates", "code": "shipping:rates:view", "category": "shipping", "resource": "rates", "action": "view"},
    {"name": "All Shipping Operations", "code": "shipping:*", "category": "shipping", "resource": "shipping", "action": "*"},
    
    # Manifest Management
    {"name": "Create Manifests", "code": "manifests:create", "category": "manifests", "resource": "manifest", "action": "create"},
    {"name": "Read Manifests", "code": "manifests:read", "category": "manifests", "resource": "manifest", "action": "read"},
    {"name": "Update Manifests", "code": "manifests:update", "category": "manifests", "resource": "manifest", "action": "update"},
    {"name": "Delete Manifests", "code": "manifests:delete", "category": "manifests", "resource": "manifest", "action": "delete"},
    {"name": "All Manifest Operations", "code": "manifests:*", "category": "manifests", "resource": "manifest", "action": "*"},
    
    # Role Management
    {"name": "Create Roles", "code": "roles:create", "category": "roles", "resource": "role", "action": "create"},
    {"name": "Read Roles", "code": "roles:read", "category": "roles", "resource": "role", "action": "read"},
    {"name": "Update Roles", "code": "roles:update", "category": "roles", "resource": "role", "action": "update"},
    {"name": "Delete Roles", "code": "roles:delete", "category": "roles", "resource": "role", "action": "delete"},
    {"name": "All Role Operations", "code": "roles:*", "category": "roles", "resource": "role", "action": "*"},
    
    # Admin Operations
    {"name": "Create Admin Resources", "code": "admin:create", "category": "admin", "resource": "admin", "action": "create"},
    {"name": "Read Admin Resources", "code": "admin:read", "category": "admin", "resource": "admin", "action": "read"},
    {"name": "Update Admin Resources", "code": "admin:update", "category": "admin", "resource": "admin", "action": "update"},
    {"name": "Delete Admin Resources", "code": "admin:delete", "category": "admin", "resource": "admin", "action": "delete"},
    {"name": "All Admin Operations", "code": "admin:*", "category": "admin", "resource": "admin", "action": "*"},
    
    # Analytics & Reports
    {"name": "View Reports", "code": "reports:view", "category": "reports", "resource": "report", "action": "view"},
    {"name": "View Analytics", "code": "analytics:view", "category": "analytics", "resource": "analytics", "action": "view"},
    
    # All Permissions (Superuser)
    {"name": "All Permissions", "code": "*", "category": "system", "resource": "*", "action": "*"},
]

# Define default roles
DEFAULT_ROLES = [
    {
        "name": "Super Administrator",
        "code": "superuser", 
        "description": "Full system access with all permissions",
        "permissions": ["*"],
        "is_system_role": True,
        "is_default": False
    },
    {
        "name": "Administrator", 
        "code": "admin", 
        "description": "Administrative access to all resources",
        "permissions": [
            "users:*", "companies:*", "roles:*", "customers:*", 
            "orders:*", "products:*", "inventory:*", "shipping:*", 
            "manifests:*", "reports:view", "analytics:view", "admin:*"
        ], 
        "is_system_role": True,
        "is_default": False
    },
    {
        "name": "Manager", 
        "code": "manager", 
        "description": "Management access to operations and customer data",
        "permissions": [
            "users:read", "customers:*", "orders:*", "products:read", 
            "products:update", "inventory:read", "inventory:update", 
            "shipping:*", "manifests:*", "reports:view", "analytics:view"
        ], 
        "is_system_role": True,
        "is_default": False
    },
    {
        "name": "Customer Service Representative", 
        "code": "customer_service", 
        "description": "Customer service and support access",
        "permissions": [
            "customers:read:all", "customers:update:all", "orders:read:all", 
            "orders:update", "products:read", "inventory:read", 
            "shipping:read", "shipping:rates:view"
        ], 
        "is_system_role": True,
        "is_default": False
    },
    {
        "name": "Customer", 
        "code": "customer", 
        "description": "Customer access to own data and basic operations",
        "permissions": [
            "profile:*", "customers:read:own", "customers:update:own",
            "orders:read:own", "orders:create", "products:read",
            "shipping:rates:view"
        ], 
        "is_system_role": True, 
        "is_default": True
    },
    {
        "name": "Viewer", 
        "code": "viewer", 
        "description": "Read-only access to own data",
        "permissions": [
            "profile:read", "orders:read:own", "customers:read:own",
            "products:read"
        ], 
        "is_system_role": True,
        "is_default": False
    },
    {
        "name": "Shipping Coordinator",
        "code": "shipping_coordinator",
        "description": "Shipping and logistics management",
        "permissions": [
            "orders:read:all", "shipping:*", "manifests:*", 
            "inventory:read", "products:read"
        ],
        "is_system_role": True,
        "is_default": False
    }
]

async def init_permissions(db: AsyncSession):
    """Initialize default permissions"""
    print("Initializing permissions...")
    
    for perm_data in DEFAULT_PERMISSIONS:
        # Check if permission already exists
        stmt = select(Permission).where(Permission.code == perm_data["code"])
        result = await db.execute(stmt)
        existing_perm = result.scalar_one_or_none()
        
        if not existing_perm:
            permission = Permission(
                name=perm_data["name"],
                code=perm_data["code"],
                category=perm_data["category"],
                resource=perm_data["resource"],
                action=perm_data["action"],
                is_system_permission=True
            )
            db.add(permission)
            print(f"  Added permission: {perm_data['code']}")
        else:
            print(f"  Permission already exists: {perm_data['code']}")
    
    await db.commit()
    print(f"Initialized {len(DEFAULT_PERMISSIONS)} permissions")

async def init_roles(db: AsyncSession):
    """Initialize default roles"""
    print("Initializing roles...")
    
    for role_data in DEFAULT_ROLES:
        # Check if role already exists
        stmt = select(Role).where(Role.code == role_data["code"])
        result = await db.execute(stmt)
        existing_role = result.scalar_one_or_none()
        
        if not existing_role:
            role = Role(
                name=role_data["name"],
                code=role_data["code"],
                description=role_data["description"],
                permissions=role_data["permissions"],
                is_system_role=role_data["is_system_role"],
                is_default=role_data["is_default"]
            )
            db.add(role)
            print(f"  Added role: {role_data['code']}")
        else:
            # Update existing role permissions
            existing_role.permissions = role_data["permissions"]
            existing_role.description = role_data["description"]
            print(f"  Updated role: {role_data['code']}")
    
    await db.commit()
    print(f"Initialized {len(DEFAULT_ROLES)} roles")

async def init_roles_and_permissions():
    """Initialize all default roles and permissions"""
    print("Starting role and permission initialization...")
    
    async with engine.begin() as conn:
        # Import here to avoid circular import
        from .database import Base
        # Create tables if they don't exist
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSession(engine) as db:
        await init_permissions(db)
        await init_roles(db)
    
    print("Role and permission initialization completed!")

if __name__ == "__main__":
    asyncio.run(init_roles_and_permissions())