import pytest
from decimal import Decimal
from src.domain.value_objects.money import Money
from src.domain.value_objects.address import Address
from src.domain.value_objects.phone import Phone
from src.domain.value_objects.email import Email

class TestMoney:
    
    def test_create_money_with_valid_amount(self):
        # Arrange & Act
        money = Money(Decimal('100.50'), "COP")
        
        # Assert
        assert money.amount == Decimal('100.50')
        assert money.currency == "COP"
    
    def test_cannot_create_negative_money(self):
        # Act & Assert
        with pytest.raises(ValueError, match="Money amount cannot be negative"):
            Money(Decimal('-10.00'), "COP")
    
    def test_cannot_create_money_invalid_currency(self):
        # Act & Assert
        with pytest.raises(ValueError, match="Currency must be a 3-letter code"):
            Money(Decimal('100.00'), "PESO")
    
    def test_add_money_same_currency(self):
        # Arrange
        money1 = Money(Decimal('100.00'), "COP")
        money2 = Money(Decimal('50.00'), "COP")
        
        # Act
        result = money1.add(money2)
        
        # Assert
        assert result.amount == Decimal('150.00')
        assert result.currency == "COP"
    
    def test_cannot_add_money_different_currency(self):
        # Arrange
        money1 = Money(Decimal('100.00'), "COP")
        money2 = Money(Decimal('50.00'), "USD")
        
        # Act & Assert
        with pytest.raises(ValueError, match="Cannot add COP and USD"):
            money1.add(money2)
    
    def test_subtract_money(self):
        # Arrange
        money1 = Money(Decimal('100.00'), "COP")
        money2 = Money(Decimal('30.00'), "COP")
        
        # Act
        result = money1.subtract(money2)
        
        # Assert
        assert result.amount == Decimal('70.00')
        assert result.currency == "COP"
    
    def test_cannot_subtract_resulting_negative(self):
        # Arrange
        money1 = Money(Decimal('50.00'), "COP")
        money2 = Money(Decimal('100.00'), "COP")
        
        # Act & Assert
        with pytest.raises(ValueError, match="Result would be negative"):
            money1.subtract(money2)
    
    def test_multiply_money(self):
        # Arrange
        money = Money(Decimal('100.00'), "COP")
        
        # Act
        result = money.multiply(Decimal('1.5'))
        
        # Assert
        assert result.amount == Decimal('150.00')
        assert result.currency == "COP"
    
    def test_percentage_calculation(self):
        # Arrange
        money = Money(Decimal('1000.00'), "COP")
        
        # Act
        result = money.percentage(Decimal('15'))  # 15%
        
        # Assert
        assert result.amount == Decimal('150.00')
        assert result.currency == "COP"
    
    def test_format_with_symbol(self):
        # Arrange
        money = Money(Decimal('1234.56'), "COP")
        
        # Act
        formatted = money.format(symbol=True)
        
        # Assert
        assert formatted == "$1,234.56"
    
    def test_format_without_symbol(self):
        # Arrange
        money = Money(Decimal('1234.56'), "COP")
        
        # Act
        formatted = money.format(symbol=False)
        
        # Assert
        assert formatted == "1,234.56 COP"
    
    def test_to_cents(self):
        # Arrange
        money = Money(Decimal('123.45'), "COP")
        
        # Act
        cents = money.to_cents()
        
        # Assert
        assert cents == 12345
    
    def test_from_cents(self):
        # Act
        money = Money.from_cents(12345, "COP")
        
        # Assert
        assert money.amount == Decimal('123.45')
        assert money.currency == "COP"
    
    def test_zero_money(self):
        # Act
        money = Money.zero("USD")
        
        # Assert
        assert money.amount == Decimal('0.00')
        assert money.currency == "USD"
        assert money.is_zero() == True

class TestAddress:
    
    def test_create_valid_address(self):
        # Act
        address = Address(
            street="Calle 123 #45-67",
            city="Bogotá",
            state="Cundinamarca",
            postal_code="110111",
            country="Colombia"
        )
        
        # Assert
        assert address.street == "Calle 123 #45-67"
        assert address.city == "Bogotá"
        assert address.state == "Cundinamarca"
        assert address.postal_code == "110111"
        assert address.country == "Colombia"
    
    def test_cannot_create_address_empty_street(self):
        # Act & Assert
        with pytest.raises(ValueError, match="Street cannot be empty"):
            Address(
                street="",
                city="Bogotá",
                state="Cundinamarca",
                postal_code="110111"
            )
    
    def test_invalid_postal_code_colombia(self):
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid postal code format"):
            Address(
                street="Calle 123",
                city="Bogotá",
                state="Cundinamarca",
                postal_code="12345",  # Should be 6 digits for Colombia
                country="Colombia"
            )
    
    def test_get_full_address(self):
        # Arrange
        address = Address(
            street="Calle 123 #45-67",
            city="Bogotá",
            state="Cundinamarca",
            postal_code="110111",
            country="Colombia"
        )
        
        # Act
        full_address = address.get_full_address()
        
        # Assert
        expected = "Calle 123 #45-67, Bogotá, Cundinamarca, 110111, Colombia"
        assert full_address == expected
    
    def test_is_international(self):
        # Arrange
        domestic_address = Address(
            street="Calle 123",
            city="Bogotá",
            state="Cundinamarca",
            postal_code="110111",
            country="Colombia"
        )
        
        international_address = Address(
            street="123 Main St",
            city="Miami",
            state="Florida",
            postal_code="33101",
            country="USA"
        )
        
        # Act & Assert
        assert domestic_address.is_international() == False
        assert international_address.is_international() == True

class TestPhone:
    
    def test_create_valid_colombian_mobile(self):
        # Act
        phone = Phone("3001234567", "+57")
        
        # Assert
        assert phone.number == "3001234567"
        assert phone.country_code == "+57"
        assert phone.is_mobile() == True
    
    def test_create_valid_colombian_landline(self):
        # Act
        phone = Phone("6012345678", "+57")
        
        # Assert
        assert phone.number == "6012345678"
        assert phone.country_code == "+57"
        assert phone.is_mobile() == False
        assert phone.is_landline() == True
    
    def test_invalid_phone_number(self):
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid phone number format"):
            Phone("123", "+57")
    
    def test_clean_phone_number(self):
        # Act
        phone = Phone("(300) 123-4567", "+57")
        
        # Assert
        assert phone.number == "3001234567"
    
    def test_get_full_number(self):
        # Arrange
        phone = Phone("3001234567", "+57")
        
        # Act
        full_number = phone.get_full_number()
        
        # Assert
        assert full_number == "+573001234567"
    
    def test_get_formatted_number_colombian_mobile(self):
        # Arrange
        phone = Phone("3001234567", "+57")
        
        # Act
        formatted = phone.get_formatted_number()
        
        # Assert
        assert formatted == "300 123 4567"
    
    def test_get_country_name(self):
        # Arrange
        phone = Phone("3001234567", "+57")
        
        # Act
        country = phone.get_country_name()
        
        # Assert
        assert country == "Colombia"

class TestEmail:
    
    def test_create_valid_email(self):
        # Act
        email = Email("test@example.com")
        
        # Assert
        assert email.value == "test@example.com"
    
    def test_invalid_email_format(self):
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid email format"):
            Email("invalid-email")
    
    def test_invalid_email_no_domain(self):
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid email format"):
            Email("test@")
    
    def test_email_string_representation(self):
        # Arrange
        email = Email("test@example.com")
        
        # Act & Assert
        assert str(email) == "test@example.com"