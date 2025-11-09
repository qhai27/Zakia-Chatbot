"""
Enhanced Zakat Calculator Module for ZAKIA Chatbot
Integrates with LZNK API for real-time nisab values
"""

import requests
from typing import Dict, Optional, List

class ZakatCalculator:
    """
    Calculate zakat amounts using LZNK API 
    """
    
    # base URL for LZNK endpoints
    BASE_API_URL = "https://jom.zakatkedah.com.my"
    
    def __init__(self):
        """Initialize calculator with API endpoints"""
        self.current_nisab_data = {}
        self.available_years = {}
    
    def fetch_available_years(self, year_type: str = 'H') -> Dict:
        """
        Fetch available years from API
        
        Args:
            year_type: 'H' for Hijrah, 'M' for Masihi
            
        Returns:
            dict: Available years and status
        """
        try:
            url = f"{self.BASE_API_URL}/kirazakat/listjenistahun.php"
            params = {'jenistahun': year_type, 'options': 'listjenistahun'}
            headers = {'User-Agent': 'ZAKIA-Calculator/1.0'}
            resp = requests.get(url, params=params, headers=headers, timeout=10)
            resp.raise_for_status()
            try:
                data = resp.json()
            except ValueError:
                # fallback: try to parse simple year list from response text (if API returns plain text)
                text = resp.text.strip()
                # attempt to extract numbers (years)
                import re
                years = re.findall(r'\d{3,4}', text)
                data = years if years else text
            # store and normalize
            self.available_years[year_type] = data
            return {
                'success': True,
                'year_type': 'Hijrah' if year_type == 'H' else 'Masihi',
                'years': data,
                'message': f'Berjaya mendapatkan senarai tahun {year_type}'
            }
        except requests.RequestException as e:
            return {'success': False, 'error': f'Gagal mendapatkan data tahun: {e}'}
        except Exception as e:
            return {'success': False, 'error': f'Ralat sistem: {e}'}
    
    def fetch_nisab_data(self, year: str, year_type: str = 'H') -> Dict:
        """
        Fetch nisab data for specific year from API
        
        Args:
            year: Year value (e.g., '1448' for Hijrah, '2025' for Masihi)
            year_type: 'H' for Hijrah, 'M' for Masihi
            
        Returns:
            dict: Nisab data and rates
        """
        try:
            url = f"{self.BASE_API_URL}/koding/kalkulator.php"
            params = {'mode': 'semakHaul', 'haul': year}
            headers = {'User-Agent': 'ZAKIA-Calculator/1.0'}
            resp = requests.get(url, params=params, headers=headers, timeout=10)
            resp.raise_for_status()
            try:
                data = resp.json()
            except ValueError:
                # sometimes API may return HTML-wrapped JSON or plain text; try to extract JSON block
                text = resp.text
                import re, json
                m = re.search(r'(\{.*\}|\[.*\])', text, flags=re.S)
                if m:
                    try:
                        data = json.loads(m.group(1))
                    except Exception:
                        data = {}
                else:
                    data = {}
            # normalize structure: prefer dict with keys, or take first element if list
            if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                data = data[0]
            if not isinstance(data, dict):
                # fallback defaults
                data = {
                    'nisab_pendapatan': 22000,
                    'nisab_simpanan': 22000,
                    'kadar_zakat': 2.57
                }
            # store current nisab data
            self.current_nisab_data = data
            return {
                'success': True,
                'data': data,
                'year': year,
                'year_type': 'Hijrah' if year_type == 'H' else 'Masihi',
                'message': f'Berjaya mendapatkan data nisab untuk tahun {year}'
            }
        except requests.RequestException as e:
            # network error -> return fallback defaults but mark fallback
            return {
                'success': True,
                'data': {
                    'nisab_pendapatan': 22000,
                    'nisab_simpanan': 22000,
                    'kadar_zakat': 2.5
                },
                'year': year,
                'year_type': 'Hijrah' if year_type == 'H' else 'Masihi',
                'message': 'Menggunakan nilai nisab lalai (rangkaian gagal)',
                'fallback': True,
                'error': str(e)
            }
        except Exception as e:
            return {
                'success': True,
                'data': {
                    'nisab_pendapatan': 22000,
                    'nisab_simpanan': 22000,
                    'kadar_zakat': 2.5
                },
                'year': year,
                'year_type': 'Hijrah' if year_type == 'H' else 'Masihi',
                'message': 'Menggunakan nilai nisab lalai (ralat pemprosesan)',
                'fallback': True,
                'error': str(e)
            }
    
    def calculate_income_zakat(self, annual_income: float, annual_expenses: float, 
                              year: str, year_type: str = 'H') -> Dict:
        """
        Calculate zakat on income
        
        Args:
            annual_income: Total annual income in RM
            annual_expenses: Total essential annual expenses in RM
            year: Year for nisab calculation
            year_type: 'H' or 'M'
        
        Returns:
            dict: Calculation results
        """
        try:
            income = float(annual_income)
            expenses = float(annual_expenses)
            
            # Fetch nisab data
            nisab_result = self.fetch_nisab_data(year, year_type)
            
            if not nisab_result['success']:
                return nisab_result
            
            nisab_data = nisab_result['data']
            
            nisab_value = 22000  # Default value
            try:
                if isinstance(nisab_data, dict):
                    nisab_value = float(nisab_data.get('nisab_pendapatan', 22000))
                elif isinstance(nisab_data, list) and len(nisab_data) > 0:
                    nisab_value = float(nisab_data[0].get('nisab_pendapatan', 22000))
            except (ValueError, AttributeError, TypeError):
                nisab_value = 22000
            
            zakat_rate = 0.0257  # Default 2.5%
            try:
                if isinstance(nisab_data, dict):
                    zakat_rate = float(nisab_data.get('kadar_zakat', 2.5)) / 100
                elif isinstance(nisab_data, list) and len(nisab_data) > 0:
                    zakat_rate = float(nisab_data[0].get('kadar_zakat', 2.5)) / 100
            except (ValueError, AttributeError, TypeError):
                zakat_rate = 0.025
            
            # Calculate zakatable amount
            zakatable_amount = income - expenses
            
            if zakatable_amount <= 0:
                return {
                    'success': True,
                    'zakat_amount': 0.0,
                    'zakatable_amount': 0.0,
                    'reaches_nisab': False,
                    'nisab_value': nisab_value,
                    'message': '❌ Perbelanjaan anda melebihi pendapatan. Tiada zakat perlu dibayar.',
                    'type': 'income',
                    'year': year,
                    'year_type': 'Hijrah' if year_type == 'H' else 'Masihi'
                }
            
            # Check if reaches nisab
            reaches_nisab = zakatable_amount >= nisab_value
            zakat_amount = zakatable_amount * zakat_rate if reaches_nisab else 0.0
            
            # Generate detailed message
            if reaches_nisab:
                message = (
                    f"✅ **Pendapatan bersih anda mencapai nisab**\n\n"
                    f"💰 **Jumlah Zakat: RM{zakat_amount:,.2f}**\n\n"
                    f"📊 **Butiran Pengiraan:**\n"
                    f"• Pendapatan tahunan: RM{income:,.2f}\n"
                    f"• Perbelanjaan asas: RM{expenses:,.2f}\n"
                    f"• Pendapatan bersih: RM{zakatable_amount:,.2f}\n"
                    f"• Nisab ({year} {year_type}): RM{nisab_value:,.2f}\n"
                    f"• Kadar zakat: {zakat_rate * 100}%"
                )
            else:
                shortfall = nisab_value - zakatable_amount
                message = (
                    f"ℹ️ **Pendapatan bersih anda belum mencapai nisab**\n\n"
                    f"Tiada zakat perlu dibayar pada masa ini.\n\n"
                    f"📊 **Butiran:**\n"
                    f"• Pendapatan bersih: RM{zakatable_amount:,.2f}\n"
                    f"• Nisab ({year} {year_type}): RM{nisab_value:,.2f}\n"
                    f"• Kekurangan: RM{shortfall:,.2f}"
                )
            
            return {
                'success': True,
                'zakat_amount': round(zakat_amount, 2),
                'zakatable_amount': round(zakatable_amount, 2),
                'reaches_nisab': reaches_nisab,
                'nisab_value': nisab_value,
                'message': message,
                'type': 'income',
                'year': year,
                'year_type': 'Hijrah' if year_type == 'H' else 'Masihi',
                'details': {
                    'income': round(income, 2),
                    'expenses': round(expenses, 2),
                    'rate': zakat_rate,
                    'shortfall': round(nisab_value - zakatable_amount, 2) if not reaches_nisab else 0
                }
            }
        
        except ValueError:
            return {
                'success': False,
                'error': 'Sila masukkan nilai yang sah (nombor sahaja)',
                'type': 'income'
            }
        except Exception as e:
            print(f"Error in calculate_income_zakat: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': f'Ralat pengiraan: Sila cuba lagi',
                'type': 'income'
            }
    
    def calculate_savings_zakat(self, savings_amount: float, year: str, 
                               year_type: str = 'H') -> Dict:
        """
        Calculate zakat on savings
        
        Args:
            savings_amount: Total savings in RM
            year: Year for nisab calculation
            year_type: 'H' or 'M'
        
        Returns:
            dict: Calculation results
        """
        try:
            savings = float(savings_amount)
            
            if savings <= 0:
                return {
                    'success': True,
                    'zakat_amount': 0.0,
                    'reaches_nisab': False,
                    'message': '❌ Jumlah simpanan tidak sah. Sila masukkan nilai yang betul.',
                    'type': 'savings'
                }
            
            # Fetch nisab data
            nisab_result = self.fetch_nisab_data(year, year_type)
            
            if not nisab_result['success']:
                return nisab_result
            
            nisab_data = nisab_result['data']
            nisab_value = float(nisab_data.get('nisab_simpanan', 0))
            zakat_rate = float(nisab_data.get('kadar_zakat', 2.5)) / 100
            
            # Check if reaches nisab
            reaches_nisab = savings >= nisab_value
            zakat_amount = savings * zakat_rate if reaches_nisab else 0.0
            
            # Generate detailed message
            if reaches_nisab:
                message = (
                    f"✅ **Simpanan anda mencapai nisab**\n\n"
                    f"💰 **Jumlah Zakat: RM{zakat_amount:,.2f}**\n\n"
                    f"📊 **Butiran Pengiraan:**\n"
                    f"• Jumlah simpanan: RM{savings:,.2f}\n"
                    f"• Nisab ({year} {year_type}): RM{nisab_value:,.2f}\n"
                    f"• Kadar zakat: {zakat_rate * 100}%"
                )
            else:
                shortfall = nisab_value - savings
                message = (
                    f"ℹ️ **Simpanan anda belum mencapai nisab**\n\n"
                    f"Tiada zakat perlu dibayar pada masa ini.\n\n"
                    f"📊 **Butiran:**\n"
                    f"• Jumlah simpanan: RM{savings:,.2f}\n"
                    f"• Nisab ({year} {year_type}): RM{nisab_value:,.2f}\n"
                    f"• Kekurangan: RM{shortfall:,.2f}"
                )
            
            return {
                'success': True,
                'zakat_amount': round(zakat_amount, 2),
                'zakatable_amount': round(savings, 2),
                'reaches_nisab': reaches_nisab,
                'nisab_value': nisab_value,
                'message': message,
                'type': 'savings',
                'year': year,
                'year_type': 'Hijrah' if year_type == 'H' else 'Masihi',
                'details': {
                    'savings': round(savings, 2),
                    'rate': zakat_rate,
                    'shortfall': round(nisab_value - savings, 2) if not reaches_nisab else 0
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
    
    def get_nisab_info(self, year: str, year_type: str = 'H') -> Dict:
        """Get current nisab values"""
        try:
            nisab_result = self.fetch_nisab_data(year, year_type)
            
            if not nisab_result['success']:
                return nisab_result
            
            nisab_data = nisab_result['data']
            
            message = (
                f"📊 **Maklumat Nisab Tahun {year} ({year_type})**\n\n"
                f"**Nisab Pendapatan/Simpanan:**\n"
                f"• RM{float(nisab_data.get('nisab_pendapatan', 0)):,.2f} setahun\n\n"
                f"**Kadar Zakat:**\n"
                f"• {float(nisab_data.get('kadar_zakat', 2.5))}% (2.5%)\n\n"
                f"**Jenis Tahun:** {nisab_result['year_type']}\n"
                f"**Tahun:** {year}"
            )
            
            return {
                'success': True,
                'reply': message,
                'data': nisab_data,
                'year': year,
                'year_type': nisab_result['year_type']
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Ralat sistem: {str(e)}'
            }
    
    def check_amount_against_years(self, amount: float, years: List[str],
                                   year_type: str = 'H', amount_kind: str = 'net') -> Dict:
        """
        Check a given amount against nisab for multiple years using kalkulator.php.

        Args:
            amount: numeric amount to check (treated as net zakatable amount or savings)
            years: list of year strings (e.g., ['1447','1448'])
            year_type: 'H' or 'M'
            amount_kind: 'net' (net income / zakatable amount) or 'savings'

        Returns:
            dict: per-year results { year: { nisab, kadar, reaches, zakat, raw_data, fallback? } }
        """
        results = {}
        for y in years:
            try:
                res = self.fetch_nisab_data(y, year_type)
                if not res.get('success'):
                    results[y] = {'error': res.get('error', 'unknown'), 'fallback': res.get('fallback', False)}
                    continue
                data = res['data'] or {}
                # read nisab depending on kind
                nisab_income = None
                nisab_savings = None
                try:
                    nisab_income = float(data.get('nisab_pendapatan', data.get('nisab', 22000)))
                except Exception:
                    nisab_income = 22000.0
                try:
                    nisab_savings = float(data.get('nisab_simpanan', nisab_income))
                except Exception:
                    nisab_savings = nisab_income
                try:
                    kadar = float(data.get('kadar_zakat', 2.5)) / 100.0
                except Exception:
                    kadar = 0.025
                nisab_value = nisab_savings if amount_kind == 'savings' else nisab_income
                reaches = float(amount) >= nisab_value
                zakat = round((float(amount) * kadar) if reaches else 0.0, 2)
                results[y] = {
                    'nisab': nisab_value,
                    'kadar': kadar,
                    'reaches': reaches,
                    'zakat': zakat,
                    'raw_data': data,
                    'fallback': res.get('fallback', False)
                }
            except Exception as e:
                results[y] = {'error': str(e)}
        return {'success': True, 'checked_amount': amount, 'kind': amount_kind, 'results': results}