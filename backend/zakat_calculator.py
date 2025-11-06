"""
Zakat Calculator Module for ZAKIA Chatbot
Handles zakat calculations for income, savings, and gold
"""

class ZakatCalculator:
    """
    Calculate zakat amounts based on different types
    All amounts in Malaysian Ringgit (RM)
    """
    
    # Nisab values 
    NISAB_INCOME = 38618.66  # Annual income nisab in RM
    NISAB_SAVINGS = 38618.66 # Savings nisab in RM (equivalent to 85g gold)
    NISAB_GOLD_GRAMS = 85  # Gold nisab in grams
    ZAKAT_RATE = 0.02577  # 2.5%
    
    # Current gold price per gram (should be updated regularly)
    GOLD_PRICE_PER_GRAM = 300  # RM per gram (update this value)
    
    def __init__(self):
        """Initialize calculator with current rates"""
        self.nisab_gold_value = self.NISAB_GOLD_GRAMS * self.GOLD_PRICE_PER_GRAM
    
    def calculate_income_zakat(self, annual_income, annual_expenses):
        """
        Calculate zakat on income (pendapatan)
        
        Args:
            annual_income (float): Total annual income in RM
            annual_expenses (float): Total essential annual expenses in RM
        
        Returns:
            dict: Calculation results with zakat amount and nisab status
        """
        try:
            income = float(annual_income)
            expenses = float(annual_expenses)
            
            # Calculate zakatable amount
            zakatable_amount = income - expenses
            
            # Check if below zero
            if zakatable_amount <= 0:
                return {
                    'success': True,
                    'zakat_amount': 0.0,
                    'zakatable_amount': 0.0,
                    'reaches_nisab': False,
                    'nisab_value': self.NISAB_INCOME,
                    'message': 'Perbelanjaan anda melebihi pendapatan. Tiada zakat perlu dibayar.',
                    'type': 'income'
                }
            
            # Check if reaches nisab
            reaches_nisab = zakatable_amount >= self.NISAB_INCOME
            
            # Calculate zakat if reaches nisab
            zakat_amount = zakatable_amount * self.ZAKAT_RATE if reaches_nisab else 0.0
            
            # Generate message
            if reaches_nisab:
                message = (
                    f" Pendapatan bersih anda (RM{zakatable_amount:,.2f}) mencapai nisab.\n\n"
                    f"**Zakat pendapatan anda ialah RM{zakat_amount:,.2f}**\n\n"
                    f" Butiran:\n"
                    f"• Pendapatan tahunan: RM{income:,.2f}\n"
                    f"• Perbelanjaan asas: RM{expenses:,.2f}\n"
                    f"• Pendapatan bersih: RM{zakatable_amount:,.2f}\n"
                    f"• Kadar zakat: {self.ZAKAT_RATE * 100}%"
                )
            else:
                shortfall = self.NISAB_INCOME - zakatable_amount
                message = (
                    f"ℹ️ Pendapatan bersih anda (RM{zakatable_amount:,.2f}) tidak mencapai nisab (RM{self.NISAB_INCOME:,.2f}).\n\n"
                    f"Tiada zakat perlu dibayar.\n\n"
                    f"Kekurangan: RM{shortfall:,.2f} untuk mencapai nisab."
                )
            
            return {
                'success': True,
                'zakat_amount': round(zakat_amount, 2),
                'zakatable_amount': round(zakatable_amount, 2),
                'reaches_nisab': reaches_nisab,
                'nisab_value': self.NISAB_INCOME,
                'message': message,
                'type': 'income',
                'details': {
                    'income': round(income, 2),
                    'expenses': round(expenses, 2),
                    'rate': self.ZAKAT_RATE
                }
            }
            
        except ValueError as e:
            return {
                'success': False,
                'error': 'Sila masukkan nilai yang sah (nombor sahaja)',
                'type': 'income'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Ralat pengiraan: {str(e)}',
                'type': 'income'
            }
    
    def calculate_savings_zakat(self, savings_amount):
        """
        Calculate zakat on savings (simpanan)
        
        Args:
            savings_amount (float): Total savings in RM
        
        Returns:
            dict: Calculation results with zakat amount and nisab status
        """
        try:
            savings = float(savings_amount)
            
            if savings <= 0:
                return {
                    'success': True,
                    'zakat_amount': 0.0,
                    'reaches_nisab': False,
                    'nisab_value': self.NISAB_SAVINGS,
                    'message': 'Jumlah simpanan tidak sah. Sila masukkan nilai yang betul.',
                    'type': 'savings'
                }
            
            # Check if reaches nisab
            reaches_nisab = savings >= self.NISAB_SAVINGS
            
            # Calculate zakat if reaches nisab
            zakat_amount = savings * self.ZAKAT_RATE if reaches_nisab else 0.0
            
            # Generate message
            if reaches_nisab:
                message = (
                    f"Simpanan anda (RM{savings:,.2f}) mencapai nisab.\n\n"
                    f"**Zakat simpanan anda ialah RM{zakat_amount:,.2f}**\n\n"
                    f"Butiran:\n"
                    f"• Jumlah simpanan: RM{savings:,.2f}\n"
                    f"• Nisab simpanan: RM{self.NISAB_SAVINGS:,.2f}\n"
                    f"• Kadar zakat: {self.ZAKAT_RATE * 100}%"
                )
            else:
                shortfall = self.NISAB_SAVINGS - savings
                message = (
                    f"ℹ️ Simpanan anda (RM{savings:,.2f}) tidak mencapai nisab (RM{self.NISAB_SAVINGS:,.2f}).\n\n"
                    f"Tiada zakat perlu dibayar.\n\n"
                    f"Kekurangan: RM{shortfall:,.2f} untuk mencapai nisab."
                )
            
            return {
                'success': True,
                'zakat_amount': round(zakat_amount, 2),
                'zakatable_amount': round(savings, 2),
                'reaches_nisab': reaches_nisab,
                'nisab_value': self.NISAB_SAVINGS,
                'message': message,
                'type': 'savings',
                'details': {
                    'savings': round(savings, 2),
                    'rate': self.ZAKAT_RATE
                }
            }
            
        except ValueError:
            return {
                'success': False,
                'error': 'Sila masukkan nilai yang sah (nombor sahaja)',
                'type': 'savings'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Ralat pengiraan: {str(e)}',
                'type': 'savings'
            }
    
    def calculate_gold_zakat(self, gold_weight_grams, gold_price_per_gram=None):
        """
        Calculate zakat on gold (emas)
        
        Args:
            gold_weight_grams (float): Total gold weight in grams
            gold_price_per_gram (float, optional): Current gold price per gram
        
        Returns:
            dict: Calculation results with zakat amount and nisab status
        """
        try:
            weight = float(gold_weight_grams)
            price = float(gold_price_per_gram) if gold_price_per_gram else self.GOLD_PRICE_PER_GRAM
            
            if weight <= 0:
                return {
                    'success': True,
                    'zakat_amount': 0.0,
                    'reaches_nisab': False,
                    'nisab_value': self.NISAB_GOLD_GRAMS,
                    'message': 'Berat emas tidak sah. Sila masukkan nilai yang betul.',
                    'type': 'gold'
                }
            
            # Calculate total value
            total_value = weight * price
            
            # Check if reaches nisab
            reaches_nisab = weight >= self.NISAB_GOLD_GRAMS
            
            # Calculate zakat if reaches nisab
            zakat_amount = total_value * self.ZAKAT_RATE if reaches_nisab else 0.0
            zakat_weight = weight * self.ZAKAT_RATE if reaches_nisab else 0.0
            
            # Generate message
            if reaches_nisab:
                message = (
                    f"Emas anda ({weight}g) mencapai nisab.\n\n"
                    f"**Zakat emas anda ialah:**\n"
                    f"• RM{zakat_amount:,.2f}\n"
                    f"• atau {zakat_weight:.2f}g emas\n\n"
                    f"Butiran:\n"
                    f"• Berat emas: {weight}g\n"
                    f"• Harga emas semasa: RM{price:,.2f}/g\n"
                    f"• Nilai emas: RM{total_value:,.2f}\n"
                    f"• Nisab emas: {self.NISAB_GOLD_GRAMS}g\n"
                    f"• Kadar zakat: {self.ZAKAT_RATE * 100}%"
                )
            else:
                shortfall = self.NISAB_GOLD_GRAMS - weight
                message = (
                    f"ℹ️ Emas anda ({weight}g) tidak mencapai nisab ({self.NISAB_GOLD_GRAMS}g).\n\n"
                    f"Tiada zakat perlu dibayar.\n\n"
                    f"Kekurangan: {shortfall}g untuk mencapai nisab."
                )
            
            return {
                'success': True,
                'zakat_amount': round(zakat_amount, 2),
                'zakat_weight': round(zakat_weight, 2),
                'zakatable_amount': round(total_value, 2),
                'reaches_nisab': reaches_nisab,
                'nisab_value': self.NISAB_GOLD_GRAMS,
                'message': message,
                'type': 'gold',
                'details': {
                    'weight': round(weight, 2),
                    'price_per_gram': round(price, 2),
                    'total_value': round(total_value, 2),
                    'rate': self.ZAKAT_RATE
                }
            }
            
        except ValueError:
            return {
                'success': False,
                'error': 'Sila masukkan nilai yang sah (nombor sahaja)',
                'type': 'gold'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Ralat pengiraan: {str(e)}',
                'type': 'gold'
            }
    
    def get_nisab_info(self):
        """Get current nisab values"""
        return {
            'income': self.NISAB_INCOME,
            'savings': self.NISAB_SAVINGS,
            'gold_grams': self.NISAB_GOLD_GRAMS,
            'gold_value': self.nisab_gold_value,
            'gold_price_per_gram': self.GOLD_PRICE_PER_GRAM,
            'zakat_rate': self.ZAKAT_RATE
        }