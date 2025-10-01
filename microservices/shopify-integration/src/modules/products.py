"""
Shopify Products Module
Handles product catalog, variants, images, and metafields
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import json
from decimal import Decimal

logger = logging.getLogger(__name__)


class ProductsModule:
    """
    Manage Shopify products, variants, and related data
    """
    
    def __init__(self, client):
        """
        Initialize Products module
        
        Args:
            client: ShopifyAPIClient instance
        """
        self.client = client
    
    # Product CRUD Operations
    
    def create_product(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new product
        
        Args:
            product_data: Product information including title, body_html, vendor, etc.
        
        Returns:
            Created product data
        """
        logger.info(f"Creating product: {product_data.get('title')}")
        response = self.client.post('products', {'product': product_data})
        return response.get('product', {})
    
    def get_product(self, product_id: int, fields: List[str] = None) -> Dict[str, Any]:
        """
        Get a single product by ID
        
        Args:
            product_id: Product ID
            fields: List of fields to include
        
        Returns:
            Product data
        """
        params = {}
        if fields:
            params['fields'] = ','.join(fields)
        
        response = self.client.get(f'products/{product_id}', params)
        return response.get('product', {})
    
    def update_product(self, product_id: int, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing product
        
        Args:
            product_id: Product ID
            product_data: Updated product information
        
        Returns:
            Updated product data
        """
        logger.info(f"Updating product {product_id}")
        response = self.client.put(f'products/{product_id}', {'product': product_data})
        return response.get('product', {})
    
    def delete_product(self, product_id: int) -> bool:
        """
        Delete a product
        
        Args:
            product_id: Product ID
        
        Returns:
            True if successful
        """
        logger.info(f"Deleting product {product_id}")
        self.client.delete(f'products/{product_id}')
        return True
    
    def list_products(self, **kwargs) -> List[Dict[str, Any]]:
        """
        List products with optional filters
        
        Args:
            limit: Number of products to retrieve
            page: Page number
            since_id: Restrict results after specified ID
            title: Filter by product title
            vendor: Filter by product vendor
            handle: Filter by product handle
            product_type: Filter by product type
            status: Filter by status (active, archived, draft)
            published_status: Filter by published status (published, unpublished, any)
            created_at_min: Show products created after date
            created_at_max: Show products created before date
            updated_at_min: Show products updated after date
            updated_at_max: Show products updated before date
            published_at_min: Show products published after date
            published_at_max: Show products published before date
            fields: Comma-separated list of fields to include
            
        Returns:
            List of products
        """
        return self.client.paginate('products', kwargs)
    
    def count_products(self, **kwargs) -> int:
        """
        Count products matching criteria
        
        Args:
            Same filters as list_products
        
        Returns:
            Product count
        """
        response = self.client.get('products/count', kwargs)
        return response.get('count', 0)
    
    # Product Variants
    
    def create_variant(self, product_id: int, variant_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new product variant
        
        Args:
            product_id: Product ID
            variant_data: Variant information
        
        Returns:
            Created variant data
        """
        logger.info(f"Creating variant for product {product_id}")
        response = self.client.post(f'products/{product_id}/variants', {'variant': variant_data})
        return response.get('variant', {})
    
    def get_variant(self, variant_id: int) -> Dict[str, Any]:
        """
        Get a single variant by ID
        
        Args:
            variant_id: Variant ID
        
        Returns:
            Variant data
        """
        response = self.client.get(f'variants/{variant_id}')
        return response.get('variant', {})
    
    def update_variant(self, variant_id: int, variant_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a product variant
        
        Args:
            variant_id: Variant ID
            variant_data: Updated variant information
        
        Returns:
            Updated variant data
        """
        logger.info(f"Updating variant {variant_id}")
        response = self.client.put(f'variants/{variant_id}', {'variant': variant_data})
        return response.get('variant', {})
    
    def delete_variant(self, product_id: int, variant_id: int) -> bool:
        """
        Delete a product variant
        
        Args:
            product_id: Product ID
            variant_id: Variant ID
        
        Returns:
            True if successful
        """
        logger.info(f"Deleting variant {variant_id} from product {product_id}")
        self.client.delete(f'products/{product_id}/variants/{variant_id}')
        return True
    
    def list_variants(self, product_id: int, **kwargs) -> List[Dict[str, Any]]:
        """
        List all variants for a product
        
        Args:
            product_id: Product ID
            limit: Number of variants to retrieve
            page: Page number
            since_id: Restrict results after specified ID
            fields: Comma-separated list of fields to include
        
        Returns:
            List of variants
        """
        return self.client.paginate(f'products/{product_id}/variants', kwargs)
    
    def count_variants(self, product_id: int) -> int:
        """
        Count variants for a product
        
        Args:
            product_id: Product ID
        
        Returns:
            Variant count
        """
        response = self.client.get(f'products/{product_id}/variants/count')
        return response.get('count', 0)
    
    # Product Images
    
    def create_image(self, product_id: int, image_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a product image
        
        Args:
            product_id: Product ID
            image_data: Image information (attachment or src URL)
        
        Returns:
            Created image data
        """
        logger.info(f"Creating image for product {product_id}")
        response = self.client.post(f'products/{product_id}/images', {'image': image_data})
        return response.get('image', {})
    
    def get_image(self, product_id: int, image_id: int) -> Dict[str, Any]:
        """
        Get a single product image
        
        Args:
            product_id: Product ID
            image_id: Image ID
        
        Returns:
            Image data
        """
        response = self.client.get(f'products/{product_id}/images/{image_id}')
        return response.get('image', {})
    
    def update_image(self, product_id: int, image_id: int, 
                    image_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a product image
        
        Args:
            product_id: Product ID
            image_id: Image ID
            image_data: Updated image information
        
        Returns:
            Updated image data
        """
        logger.info(f"Updating image {image_id} for product {product_id}")
        response = self.client.put(f'products/{product_id}/images/{image_id}', 
                                  {'image': image_data})
        return response.get('image', {})
    
    def delete_image(self, product_id: int, image_id: int) -> bool:
        """
        Delete a product image
        
        Args:
            product_id: Product ID
            image_id: Image ID
        
        Returns:
            True if successful
        """
        logger.info(f"Deleting image {image_id} from product {product_id}")
        self.client.delete(f'products/{product_id}/images/{image_id}')
        return True
    
    def list_images(self, product_id: int, **kwargs) -> List[Dict[str, Any]]:
        """
        List all images for a product
        
        Args:
            product_id: Product ID
            since_id: Restrict results after specified ID
            fields: Comma-separated list of fields to include
        
        Returns:
            List of images
        """
        return self.client.paginate(f'products/{product_id}/images', kwargs)
    
    def count_images(self, product_id: int) -> int:
        """
        Count images for a product
        
        Args:
            product_id: Product ID
        
        Returns:
            Image count
        """
        response = self.client.get(f'products/{product_id}/images/count')
        return response.get('count', 0)
    
    # Metafields
    
    def create_product_metafield(self, product_id: int, 
                                 metafield_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a product metafield
        
        Args:
            product_id: Product ID
            metafield_data: Metafield information
        
        Returns:
            Created metafield data
        """
        logger.info(f"Creating metafield for product {product_id}")
        response = self.client.post(f'products/{product_id}/metafields', 
                                   {'metafield': metafield_data})
        return response.get('metafield', {})
    
    def get_product_metafields(self, product_id: int, **kwargs) -> List[Dict[str, Any]]:
        """
        Get metafields for a product
        
        Args:
            product_id: Product ID
            namespace: Filter by namespace
            key: Filter by key
            value_type: Filter by value type
        
        Returns:
            List of metafields
        """
        return self.client.paginate(f'products/{product_id}/metafields', kwargs)
    
    def update_product_metafield(self, product_id: int, metafield_id: int,
                                 metafield_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a product metafield
        
        Args:
            product_id: Product ID
            metafield_id: Metafield ID
            metafield_data: Updated metafield information
        
        Returns:
            Updated metafield data
        """
        logger.info(f"Updating metafield {metafield_id} for product {product_id}")
        response = self.client.put(f'products/{product_id}/metafields/{metafield_id}',
                                  {'metafield': metafield_data})
        return response.get('metafield', {})
    
    def delete_product_metafield(self, product_id: int, metafield_id: int) -> bool:
        """
        Delete a product metafield
        
        Args:
            product_id: Product ID
            metafield_id: Metafield ID
        
        Returns:
            True if successful
        """
        logger.info(f"Deleting metafield {metafield_id} from product {product_id}")
        self.client.delete(f'products/{product_id}/metafields/{metafield_id}')
        return True
    
    # Bulk Operations
    
    def bulk_update_products(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Bulk update multiple products
        
        Args:
            products: List of products with IDs and update data
        
        Returns:
            List of updated products
        """
        updated_products = []
        for product in products:
            try:
                product_id = product.pop('id')
                updated = self.update_product(product_id, product)
                updated_products.append(updated)
            except Exception as e:
                logger.error(f"Failed to update product {product.get('id')}: {e}")
                updated_products.append({'error': str(e), 'product_id': product.get('id')})
        
        return updated_products
    
    def bulk_update_inventory(self, inventory_updates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Bulk update inventory levels
        
        Args:
            inventory_updates: List of inventory updates with variant_id and quantity
        
        Returns:
            List of update results
        """
        results = []
        for update in inventory_updates:
            try:
                variant_id = update['variant_id']
                inventory_quantity = update['inventory_quantity']
                
                result = self.update_variant(variant_id, {
                    'inventory_quantity': inventory_quantity
                })
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to update inventory for variant {update.get('variant_id')}: {e}")
                results.append({'error': str(e), 'variant_id': update.get('variant_id')})
        
        return results
    
    def import_products_from_csv(self, csv_data: str) -> Dict[str, Any]:
        """
        Import products from CSV data
        
        Args:
            csv_data: CSV formatted product data
        
        Returns:
            Import results
        """
        import csv
        from io import StringIO
        
        imported = []
        failed = []
        
        csv_file = StringIO(csv_data)
        reader = csv.DictReader(csv_file)
        
        for row in reader:
            try:
                product_data = self._csv_row_to_product(row)
                product = self.create_product(product_data)
                imported.append(product)
            except Exception as e:
                logger.error(f"Failed to import product from row: {e}")
                failed.append({'row': row, 'error': str(e)})
        
        return {
            'imported': len(imported),
            'failed': len(failed),
            'products': imported,
            'errors': failed
        }
    
    def _csv_row_to_product(self, row: Dict[str, str]) -> Dict[str, Any]:
        """
        Convert CSV row to product data
        
        Args:
            row: CSV row as dictionary
        
        Returns:
            Product data dictionary
        """
        product = {
            'title': row.get('title', ''),
            'body_html': row.get('body_html', ''),
            'vendor': row.get('vendor', ''),
            'product_type': row.get('product_type', ''),
            'tags': row.get('tags', ''),
            'published': row.get('published', 'true').lower() == 'true'
        }
        
        # Handle variants
        if row.get('variant_sku') or row.get('variant_price'):
            product['variants'] = [{
                'sku': row.get('variant_sku', ''),
                'price': row.get('variant_price', '0.00'),
                'inventory_quantity': int(row.get('variant_inventory', 0)),
                'weight': float(row.get('variant_weight', 0)),
                'weight_unit': row.get('variant_weight_unit', 'kg'),
                'requires_shipping': row.get('variant_requires_shipping', 'true').lower() == 'true'
            }]
        
        # Handle images
        if row.get('image_src'):
            product['images'] = [{'src': row['image_src']}]
        
        return product
    
    # Search and Filter
    
    def search_products(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Search products using GraphQL
        
        Args:
            query: Search query
            limit: Number of results
            
        Returns:
            Search results
        """
        graphql_query = """
        query searchProducts($query: String!, $first: Int) {
            products(first: $first, query: $query) {
                edges {
                    node {
                        id
                        title
                        handle
                        description
                        vendor
                        productType
                        tags
                        status
                        totalInventory
                        variants(first: 10) {
                            edges {
                                node {
                                    id
                                    title
                                    sku
                                    price
                                    inventoryQuantity
                                }
                            }
                        }
                        images(first: 5) {
                            edges {
                                node {
                                    url
                                    altText
                                }
                            }
                        }
                    }
                }
            }
        }
        """
        
        variables = {
            'query': query,
            'first': kwargs.get('limit', 50)
        }
        
        result = self.client.graphql(graphql_query, variables)
        
        products = []
        for edge in result.get('data', {}).get('products', {}).get('edges', []):
            products.append(edge['node'])
        
        return products
    
    def get_product_recommendations(self, product_id: int) -> List[Dict[str, Any]]:
        """
        Get product recommendations
        
        Args:
            product_id: Product ID
        
        Returns:
            List of recommended products
        """
        graphql_query = """
        query getRecommendations($productId: ID!) {
            productRecommendations(productId: $productId) {
                id
                title
                handle
                images(first: 1) {
                    edges {
                        node {
                            url
                        }
                    }
                }
                priceRange {
                    minVariantPrice {
                        amount
                        currencyCode
                    }
                }
            }
        }
        """
        
        variables = {'productId': f'gid://shopify/Product/{product_id}'}
        result = self.client.graphql(graphql_query, variables)
        
        return result.get('data', {}).get('productRecommendations', [])