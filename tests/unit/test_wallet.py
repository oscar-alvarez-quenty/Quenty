import pytest
from decimal import Decimal
from src.domain.entities.wallet import Wallet, WalletTransaction
from src.domain.value_objects.customer_id import CustomerId

class TestWallet:
    
    def create_test_wallet(self):
        return Wallet(
            customer_id=CustomerId.generate(),
            balance=Decimal('1000.00'),
            credit_limit=Decimal('500.00')
        )
    
    def test_create_wallet_with_valid_data(self):
        # Arrange
        customer_id = CustomerId.generate()
        
        # Act
        wallet = Wallet(
            customer_id=customer_id,
            balance=Decimal('1000.00'),
            credit_limit=Decimal('500.00')
        )
        
        # Assert
        assert wallet.customer_id == customer_id
        assert wallet.balance == Decimal('1000.00')
        assert wallet.credit_limit == Decimal('500.00')
        assert wallet.is_active == True
        assert len(wallet.transactions) == 0
    
    def test_add_funds(self):
        # Arrange
        wallet = self.create_test_wallet()
        initial_balance = wallet.balance
        amount = Decimal('200.00')
        
        # Act
        wallet.add_funds(amount, "Test deposit")
        
        # Assert
        assert wallet.balance == initial_balance + amount
        assert len(wallet.transactions) == 1
        assert wallet.transactions[0].amount == amount
        assert wallet.transactions[0].transaction_type == "credit"
        assert wallet.transactions[0].description == "Test deposit"
    
    def test_cannot_add_negative_funds(self):
        # Arrange
        wallet = self.create_test_wallet()
        
        # Act & Assert
        with pytest.raises(ValueError, match="Amount must be positive"):
            wallet.add_funds(Decimal('-100.00'), "Invalid deposit")
    
    def test_cannot_add_zero_funds(self):
        # Arrange
        wallet = self.create_test_wallet()
        
        # Act & Assert
        with pytest.raises(ValueError, match="Amount must be positive"):
            wallet.add_funds(Decimal('0.00'), "Invalid deposit")
    
    def test_debit_funds_within_balance(self):
        # Arrange
        wallet = self.create_test_wallet()
        initial_balance = wallet.balance
        amount = Decimal('300.00')
        
        # Act
        wallet.debit_funds(amount, "Test payment")
        
        # Assert
        assert wallet.balance == initial_balance - amount
        assert len(wallet.transactions) == 1
        assert wallet.transactions[0].amount == amount
        assert wallet.transactions[0].transaction_type == "debit"
        assert wallet.transactions[0].description == "Test payment"
    
    def test_debit_funds_using_credit_limit(self):
        # Arrange
        wallet = self.create_test_wallet()
        amount = Decimal('1200.00')  # More than balance but within credit limit
        
        # Act
        wallet.debit_funds(amount, "Large payment")
        
        # Assert
        assert wallet.balance == Decimal('-200.00')  # 1000 - 1200
        assert len(wallet.transactions) == 1
    
    def test_cannot_debit_more_than_available_balance(self):
        # Arrange
        wallet = self.create_test_wallet()
        amount = Decimal('2000.00')  # More than balance + credit limit
        
        # Act & Assert
        with pytest.raises(ValueError, match="Insufficient funds"):
            wallet.debit_funds(amount, "Excessive payment")
    
    def test_cannot_debit_negative_amount(self):
        # Arrange
        wallet = self.create_test_wallet()
        
        # Act & Assert
        with pytest.raises(ValueError, match="Amount must be positive"):
            wallet.debit_funds(Decimal('-100.00'), "Invalid payment")
    
    def test_get_available_balance(self):
        # Arrange
        wallet = self.create_test_wallet()
        
        # Act
        available_balance = wallet.get_available_balance()
        
        # Assert
        assert available_balance == Decimal('1500.00')  # 1000 + 500 credit limit
    
    def test_has_overdue_balance_false(self):
        # Arrange
        wallet = self.create_test_wallet()
        
        # Act & Assert
        assert wallet.has_overdue_balance() == False
    
    def test_has_overdue_balance_true(self):
        # Arrange
        wallet = self.create_test_wallet()
        wallet.debit_funds(Decimal('1200.00'), "Large payment")
        
        # Act & Assert
        assert wallet.has_overdue_balance() == True