"""
Zakat Calculator Module for ZAKIA Chatbot
Integrates with JomZakat API for real-time nisab values

"""

import requests
import re
import json
from typing import Dict, List
from decimal import Decimal, ROUND_HALF_UP


class ZakatCalculator:
    """Main zakat calculation engine with API integration"""
    
    BASE_API_URL = "https://jom.zakatkedah.com.my"

    def __init__(self, debug: bool = False):
        self.current_nisab_data = {}
        self.available_years = {}
        self.DEBUG = debug


    # ========================================================================
    # HELPER & PARSING FUNCTIONS
    # ========================================================================

    def _parse_kadar(self, raw) -> float:
        """Convert rate to fraction (e.g. 2.57% -> 0.0257)"""
        if raw is None:
            return 0.0257
        s = str(raw).strip()
        try:
            if s.endswith('%'):
                return float(s.rstrip('%')) / 100.0
            v = float(s)
            return v / 100.0 if v > 1 else v
        except Exception:
            return 0.0257

    def _parse_amount(self, s: str) -> float:
        """Parse monetary string like 'RM 22,000.00' -> float"""
        if not s:
            return 0.0
        s = str(s)
        m = re.search(r'([\d\.,]+)', s)
        if not m:
            return 0.0
        num = m.group(1).replace(',', '')
        try:
            return float(num)
        except Exception:
            return 0.0

    def _extract_nisab_from_text(self, text: str) -> Dict:
        """Extract nisab & kadar from raw HTML/text response"""
        out = {'nisab_pendapatan': None, 'nisab_simpanan': None, 'kadar_zakat': None}
        lowered = text.lower()
        
        # Extract nisab pendapatan
        m = re.search(r'(nisab pendapatan)[\s\:\-]*RM\.?\s*([\d,]+(?:\.\d+)?)', lowered, flags=re.I)
        if m:
            out['nisab_pendapatan'] = self._parse_amount(m.group(2))
        
        # Extract nisab simpanan
        m = re.search(r'(nisab simpanan)[\s\:\-]*RM\.?\s*([\d,]+(?:\.\d+)?)', lowered, flags=re.I)
        if m:
            out['nisab_simpanan'] = self._parse_amount(m.group(2))

        # Extract kadar
        m = re.search(r'kadar(?:\s*zakat)?[^\d]*(\d+(?:\.\d+)?)\s*%?', lowered, flags=re.I)
        if m:
            out['kadar_zakat'] = self._parse_kadar(m.group(1))

        # Fallback: extract all RM amounts
        if out['nisab_pendapatan'] is None or out['nisab_simpanan'] is None:
            nums = re.findall(r'RM\.?\s*([\d,]+(?:\.\d+)?)', text, flags=re.I)
            if not nums:
                nums = re.findall(r'([\d,]{4,}(?:\.\d+)?)', text)
            nums_clean = [self._parse_amount(n) for n in nums if self._parse_amount(n) > 0]
            nums_clean = sorted(set(nums_clean), reverse=True)
            if nums_clean:
                if out['nisab_pendapatan'] is None:
                    out['nisab_pendapatan'] = nums_clean[0]
                if out['nisab_simpanan'] is None:
                    out['nisab_simpanan'] = nums_clean[0]

        # Apply defaults
        if out['nisab_pendapatan'] is None:
            out['nisab_pendapatan'] = 22000.0
        if out['nisab_simpanan'] is None:
            out['nisab_simpanan'] = out['nisab_pendapatan']
        if out['kadar_zakat'] is None:
            m = re.search(r'(\d+(?:\.\d+)?)\s*%', text)
            out['kadar_zakat'] = self._parse_kadar(m.group(1)) if m else 0.0257

        return out

    def _safe_float(self, value, default=0.0) -> float:
        """Safely convert value to float with fallback"""
        try:
            return float(value) if value is not None else default
        except (ValueError, TypeError):
            return default
        
    from decimal import Decimal, ROUND_HALF_UP

    # Add this helper method to the ZakatCalculator class
    def _round_currency(self, amount: float) -> float:
        """
        Round currency to 2 decimal places using ROUND_HALF_UP
        """
        if amount == 0:
            return 0.0
        
        decimal_amount = Decimal(str(amount))
        rounded = decimal_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return float(rounded)

    def _build_nisab_message(self, nisab_data: Dict, year: str, year_type: str, zakat_type: str = None) -> str:
        """Build formatted nisab info message"""
        year_label = 'Hijrah' if year_type == 'H' else 'Masihi'

        # Helper to format based on unit (RM vs other units)
        def fmt_nisab(n, unit, is_money=False):
            if unit and unit.upper() == 'RM':
                return f"RM{float(n):,.2f}"
            return f"{float(n):,.2f} {unit or ('kg' if zakat_type=='padi' else 'gram emas')}"
        
        if zakat_type == 'padi':
            nisab = nisab_data.get('nisab', 1300.0)
            return (
                f"📊 Maklumat Nisab Padi - Tahun {year} ({year_label})\n"
                f"• Nisab: {fmt_nisab(nisab, nisab_data.get('unit','kg'))}\n"
                f"• Kadar Zakat: 10%"
            )
        elif zakat_type == 'saham':
            nisab = nisab_data.get('nisab', 85.0)
            unit = nisab_data.get('unit', 'RM')  # prefer RM for saham when available
            return (
                f"📊 Maklumat Nisab Saham - Tahun {year} ({year_label})\n"
                f"• Nisab: {fmt_nisab(nisab, unit)}\n"
                f"• Kadar Zakat: 2.577%"
            )
        elif zakat_type == 'perak':
            nisab = nisab_data.get('nisab', 595.0)
            return (
                f"📊 Maklumat Nisab Perak - Tahun {year} ({year_label})\n"
                f"• Nisab: {fmt_nisab(nisab, nisab_data.get('unit','gram'))}\n"
                f"• Kadar Zakat: 2.577%"
            )
        elif zakat_type == 'kwsp':
            nisab = nisab_data.get('nisab', nisab_data.get('nisab_simpanan', 22000.0))
            unit = nisab_data.get('unit', 'RM')
            return (
                f"📊 Maklumat Nisab KWSP - Tahun {year} ({year_label})\n"
                f"• Nisab: {fmt_nisab(nisab, unit)}\n"
                f"• Kadar Zakat: 2.577%"
            )
        else:
            # Default: pendapatan & simpanan
            nisab_pd = nisab_data.get('nisab_pendapatan', 22000.0)
            nisab_sp = nisab_data.get('nisab_simpanan', nisab_pd)
            kadar = nisab_data.get('kadar_zakat', 0.0257)
            return (
                f"📊 Maklumat Nisab - Tahun {year} ({year_label})\n"
                f"• Nisab Pendapatan: RM{nisab_pd:,.2f}\n"
                f"• Nisab Simpanan: RM{nisab_sp:,.2f}\n"
                f"• Kadar Zakat: {kadar*100:.2f}%"
            )


    # ========================================================================
    # API FETCHING FUNCTIONS
    # ========================================================================

    def fetch_nisab_data(self, year: str, year_type: str = 'H') -> Dict:
        """
        Fetch nisab/kadar info for given year from JomZakat API
        GET /koding/kalkulator.php?mode=semakHaul&haul=<year>
        """
        url = f"{self.BASE_API_URL}/koding/kalkulator.php"
        params = {'mode': 'semakHaul', 'haul': year}
        headers = {'User-Agent': 'ZAKIA/1.0'}
        
        try:
            if self.DEBUG:
                print(f"[DEBUG] Fetching main nisab from: {url} with params {params}")
            
            resp = requests.get(url, params=params, headers=headers, timeout=12)
            resp.raise_for_status()
            text = resp.text or ''
            
            if self.DEBUG:
                print(f"[DEBUG] API Response received (text length: {len(text)})")
            
            # Try JSON first
            parsed = None
            try:
                parsed = resp.json()
                if self.DEBUG:
                    print(f"[DEBUG] Successfully parsed JSON response (type: {type(parsed).__name__})")
            except ValueError:
                if self.DEBUG:
                    print(f"[DEBUG] Response not valid JSON, will try text parsing")
                parsed = None

            # Normalize JSON response - handle both list and dict
            data = {}
            if isinstance(parsed, dict):
                data = parsed
            elif isinstance(parsed, list) and parsed and isinstance(parsed[0], dict):
                data = parsed[0]
                if self.DEBUG:
                    print(f"[DEBUG] Extracted dict from list (list length: {len(parsed)})")
            
            if self.DEBUG and data:
                print(f"[DEBUG] Normalized data keys: {list(data.keys())}")

            # Extract key values with fallback
            def pick(d, keys):
                for k in keys:
                    if k in d and d[k] not in (None, ''):
                        if self.DEBUG:
                            print(f"[DEBUG] Found '{k}' = {d[k]}")
                        return d[k]
                return None

            nisab_pendapatan = pick(data, ['nisab_pendapatan','nisabPendapatan','nisab','nisab_pendapatan_rm','nilai_nisab'])
            nisab_simpanan = pick(data, ['nisab_simpanan','nisabSimpanan','nisab_simpanan_rm'])
            kadar_raw = pick(data, ['kadar_zakat','kadar','kadar_zakat_persen','kadar_zakat_percent','percent'])

            # Parse to numeric
            nisab_pendapatan = self._parse_amount(str(nisab_pendapatan)) if nisab_pendapatan else None
            nisab_simpanan = self._parse_amount(str(nisab_simpanan)) if nisab_simpanan else None
            kadar = self._parse_kadar(kadar_raw) if kadar_raw else None

            # Fallback to text extraction
            if not nisab_pendapatan or not nisab_simpanan or kadar is None:
                parsed_text = self._extract_nisab_from_text(text)
                nisab_pendapatan = nisab_pendapatan or parsed_text.get('nisab_pendapatan')
                nisab_simpanan = nisab_simpanan or parsed_text.get('nisab_simpanan')
                kadar = kadar or parsed_text.get('kadar_zakat')

            # Apply final defaults
            nisab_pendapatan = nisab_pendapatan or 22000.0
            nisab_simpanan = nisab_simpanan or nisab_pendapatan
            kadar = kadar or 0.0257

            normalized = {
                'nisab_pendapatan': float(nisab_pendapatan),
                'nisab_simpanan': float(nisab_simpanan),
                'kadar_zakat': float(kadar)
            }

            if self.DEBUG:
                print(f"[DEBUG] Final nisab data: {normalized}")

            self.current_nisab_data = normalized
            return {'success': True, 'data': normalized, 'raw': parsed if parsed else text}

        except requests.RequestException as e:
            return {'success': False, 'error': str(e)}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def fetch_available_years(self, year_type: str = 'H') -> Dict:
        """Fetch available years from JomZakat API"""
        url = f"{self.BASE_API_URL}/kirazakat/listjenistahun.php"
        params = {'jenistahun': year_type, 'options': 'listjenistahun'}
        headers = {'User-Agent': 'ZAKIA/1.0'}

        try:
            resp = requests.get(url, params=params, headers=headers, timeout=10)
            resp.raise_for_status()
            text = resp.text.strip()

            years = None
            try:
                data = resp.json()
                if isinstance(data, list):
                    years = [str(x) for x in data]
                elif isinstance(data, dict):
                    for key in ('years', 'list', 'data', 'jenistahun'):
                        if key in data and isinstance(data[key], (list, tuple)):
                            years = [str(x) for x in data[key]]
                            break
                    if years is None:
                        cand = [v for v in data.values() if isinstance(v, (list, tuple))]
                        if cand:
                            years = [str(x) for sublist in cand for x in sublist]
            except ValueError:
                years = None

            if years is None:
                found = re.findall(r'\d{3,4}', text)
                years = sorted(list(set(found)), reverse=True) if found else []

            self.available_years[year_type] = years
            return {'success': True, 'years': years, 'raw': text}

        except requests.RequestException as e:
            return {'success': False, 'error': str(e), 'years': []}
        except Exception as e:
            return {'success': False, 'error': str(e), 'years': []}

    def fetch_nisab_extended(self, zakat_type: str, year: str, year_type: str = 'H') -> Dict:
        """
        Fetch nisab for extended zakat types (padi, saham, perak, kwsp)
        Uses JomZakat main API endpoint: /koding/kalkulator.php?mode=semakHaul&haul=<year>
        This endpoint returns all nisab values in one response
        Falls back to defaults if API fails
        """
        # Use the main API endpoint which contains all nisab data
        url = f"{self.BASE_API_URL}/koding/kalkulator.php"
        params = {'mode': 'semakHaul', 'haul': year}
        headers = {'User-Agent': 'ZAKIA/1.0'}
        
        # Map zakat types to API response field names
        field_map = {
            'padi': 'NISABPADI',
            'saham': 'NISABEMAS',      # Using gold (emas) as equiv for saham
            'perak': 'NISABPERAK',
            'kwsp': 'NISABEMAS'         # Using gold (emas) as equiv for kwsp
        }
        
        defaults = {
            'padi': 1300.49,      # Rm/kg
            'saham': 38618.66,       # (equivalent RM value)
            'perak': 595.0,      # gram perak
            'kwsp': 38618.66         # (equivalent RM value)
        }
        
        try:
            if self.DEBUG:
                print(f"[DEBUG] Fetching {zakat_type} nisab from: {url} with params {params}")
            
            resp = requests.get(url, params=params, headers=headers, timeout=12)
            resp.raise_for_status()
            text = resp.text or ''
            
            # Try to parse JSON
            try:
                data = resp.json()
                if self.DEBUG:
                    print(f"[DEBUG] API Response type: {type(data).__name__}")
                
                # Handle both list and dict responses
                if isinstance(data, list) and data and isinstance(data[0], dict):
                    data = data[0]
                    if self.DEBUG:
                        print(f"[DEBUG] Extracted dict from list")
                
                if isinstance(data, dict):
                    # Get the field for this zakat type
                    field_name = field_map.get(zakat_type)
                    nisab_value = data.get(field_name) if field_name else None
                    
                    if self.DEBUG:
                        print(f"[DEBUG] Looking for field '{field_name}' in keys: {list(data.keys())}")
                    
                    if nisab_value:
                        nisab_float = self._parse_amount(str(nisab_value))
                        if nisab_float > 0:
                            if self.DEBUG:
                                print(f"[DEBUG] Found {zakat_type} nisab: {nisab_float} (from {field_name})")
                            return {
                                'success': True,
                                'nisab': nisab_float,
                                'raw': data,
                                'source': 'jomzakat_api',
                                'api_field': field_name
                            }
            except (ValueError, json.JSONDecodeError):
                # Not JSON, try text parsing as fallback
                if self.DEBUG:
                    print(f"[DEBUG] Response not valid JSON, trying text parsing: {text[:200]}...")
                nisab_value = self._parse_amount(text)
                if nisab_value > 0:
                    return {
                        'success': True,
                        'nisab': nisab_value,
                        'source': 'jomzakat_api_text'
                    }
            
            # Fallback to default
            if self.DEBUG:
                print(f"[DEBUG] Using default nisab for {zakat_type}: {defaults.get(zakat_type, 0)}")
            
            return {
                'success': True,
                'nisab': defaults.get(zakat_type, 0),
                'fallback': True,
                'reason': 'API did not return valid nisab value for field: ' + field_map.get(zakat_type, 'unknown')
            }
            
        except requests.RequestException as e:
            if self.DEBUG:
                print(f"[DEBUG] API request failed: {str(e)}")
            
            return {
                'success': True,
                'nisab': defaults.get(zakat_type, 0),
                'fallback': True,
                'error': str(e),
                'reason': 'API request failed'
            }


    # ========================================================================
    # INCOME & SAVINGS CALCULATIONS
    # ========================================================================

    def calculate_income_zakat_kaedah_a(self, gross_income: float, year: str, 
                                        year_type: str = 'H') -> Dict:
        """Calculate zakat on income using Kaedah A (Tanpa Tolakan)"""
        try:
            income = self._safe_float(gross_income)
            
            if income <= 0:
                return {
                    'success': True,
                    'zakat_amount': 0.0,
                    'zakatable_amount': 0.0,
                    'reaches_nisab': False,
                    'message': '❌ Jumlah pendapatan tidak sah. Sila masukkan nilai yang betul.',
                    'type': 'income_kaedah_a'
                }
            
            # Fetch nisab data
            nisab_result = self.fetch_nisab_data(year, year_type)
            if not nisab_result['success']:
                return nisab_result
            
            nisab_data = nisab_result['data']
            nisab_value = self._safe_float(
                nisab_data.get('nisab_pendapatan') if isinstance(nisab_data, dict) else nisab_data[0].get('nisab_pendapatan'),
                22000.0
            )
            kadar = self._safe_float(
                nisab_data.get('kadar_zakat') if isinstance(nisab_data, dict) else nisab_data[0].get('kadar_zakat'),
                0.0257
            )
            
            # Calculate zakat on gross income (no deductions)
            reaches_nisab = income >= nisab_value
            zakat_amount = income * kadar if reaches_nisab else 0.0
            
            # Build message
            if reaches_nisab:
                message = (
                    f"✅ **Pendapatan anda mencapai nisab (Kaedah A - Tanpa Tolakan)**\n\n"
                    f"💰 **Jumlah Zakat: RM{zakat_amount:,.2f}**\n\n"
                    f"📊 **Butiran Pengiraan:**\n"
                    f"• Pendapatan kasar: RM{income:,.2f}\n"
                    f"• Nisab ({year} {year_type}): RM{nisab_value:,.2f}\n"
                    f"• Kadar zakat: {kadar * 100:.2f}%\n\n"
                    f"ℹ️ Kaedah A: Zakat dikira berdasarkan pendapatan kasar tanpa tolakan"
                )
            else:
                shortfall = nisab_value - income
                message = (
                    f"ℹ️ **Pendapatan anda belum mencapai nisab (Kaedah A - Tanpa Tolakan)**\n\n"
                    f"Tiada zakat perlu dibayar pada masa ini.\n\n"
                    f"📊 **Butiran:**\n"
                    f"• Pendapatan kasar: RM{income:,.2f}\n"
                    f"• Nisab ({year} {year_type}): RM{nisab_value:,.2f}\n"
                    f"• Kekurangan: RM{shortfall:,.2f}"
                )
            
            return {
                'success': True,
                'zakat_amount': round(zakat_amount, 2),
                'zakatable_amount': round(income, 2),
                'reaches_nisab': reaches_nisab,
                'nisab_value': nisab_value,
                'message': message,
                'type': 'income_kaedah_a',
                'year': year,
                'year_type': 'Hijrah' if year_type == 'H' else 'Masihi',
                'details': {
                    'gross_income': round(income, 2),
                    'rate': kadar,
                    'shortfall': round(nisab_value - income, 2) if not reaches_nisab else 0
                }
            }
        
        except ValueError:
            return {
                'success': False,
                'error': 'Sila masukkan nilai yang sah (nombor sahaja)',
                'type': 'income_kaedah_a'
            }
        except Exception as e:
            print(f"Error in calculate_income_zakat_kaedah_a: {e}")
            return {'success': False, 'error': 'Ralat pengiraan', 'type': 'income_kaedah_a'}

    def calculate_income_zakat_kaedah_b(self, annual_income: float, annual_expenses: float, 
                                        year: str, year_type: str = 'H') -> Dict:
        """Calculate zakat on income using Kaedah B (Dengan Tolakan)"""
        try:
            income = self._safe_float(annual_income)
            expenses = self._safe_float(annual_expenses)
            
            # Fetch nisab data
            nisab_result = self.fetch_nisab_data(year, year_type)
            if not nisab_result['success']:
                return nisab_result
            
            nisab_data = nisab_result['data']
            nisab_value = self._safe_float(
                nisab_data.get('nisab_pendapatan') if isinstance(nisab_data, dict) else nisab_data[0].get('nisab_pendapatan'),
                22000.0
            )
            kadar = self._safe_float(
                nisab_data.get('kadar_zakat') if isinstance(nisab_data, dict) else nisab_data[0].get('kadar_zakat'),
                0.0257
            )
            
            # Calculate net income
            zakatable_amount = income - expenses
            
            if zakatable_amount <= 0:
                return {
                    'success': True,
                    'zakat_amount': 0.0,
                    'zakatable_amount': 0.0,
                    'reaches_nisab': False,
                    'nisab_value': nisab_value,
                    'message': '❌ Perbelanjaan anda melebihi pendapatan. Tiada zakat perlu dibayar.',
                    'type': 'income_kaedah_b',
                    'year': year,
                    'year_type': 'Hijrah' if year_type == 'H' else 'Masihi'
                }
            
            # Check nisab & calculate zakat
            reaches_nisab = zakatable_amount >= nisab_value
            zakat_amount = zakatable_amount * kadar if reaches_nisab else 0.0
            
            # Build message
            if reaches_nisab:
                message = (
                    f"✅ **Pendapatan bersih anda mencapai nisab (Kaedah B - Dengan Tolakan)**\n\n"
                    f"💰 **Jumlah Zakat: RM{zakat_amount:,.2f}**\n\n"
                    f"📊 **Butiran Pengiraan:**\n"
                    f"• Pendapatan tahunan: RM{income:,.2f}\n"
                    f"• Perbelanjaan asas: RM{expenses:,.2f}\n"
                    f"• Pendapatan bersih: RM{zakatable_amount:,.2f}\n"
                    f"• Nisab ({year} {year_type}): RM{nisab_value:,.2f}\n"
                    f"• Kadar zakat: {kadar * 100:.2f}%\n\n"
                    f"ℹ️ Kaedah B: Zakat dikira selepas tolakan perbelanjaan asas"
                )
            else:
                shortfall = nisab_value - zakatable_amount
                message = (
                    f"ℹ️ **Pendapatan bersih anda belum mencapai nisab (Kaedah B - Dengan Tolakan)**\n\n"
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
                'type': 'income_kaedah_b',
                'year': year,
                'year_type': 'Hijrah' if year_type == 'H' else 'Masihi',
                'details': {
                    'income': round(income, 2),
                    'expenses': round(expenses, 2),
                    'rate': kadar,
                    'shortfall': round(nisab_value - zakatable_amount, 2) if not reaches_nisab else 0
                }
            }
        
        except ValueError:
            return {'success': False, 'error': 'Sila masukkan nilai yang sah', 'type': 'income_kaedah_b'}
        except Exception as e:
            print(f"Error in calculate_income_zakat_kaedah_b: {e}")
            return {'success': False, 'error': 'Ralat pengiraan', 'type': 'income_kaedah_b'}
    
    def calculate_savings_zakat(self, savings_amount: float, year: str, 
                               year_type: str = 'H') -> Dict:
        """Calculate zakat on savings"""
        try:
            savings = self._safe_float(savings_amount)
            
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
            nisab_value = self._safe_float(
                nisab_data.get('nisab_simpanan') if isinstance(nisab_data, dict) else nisab_data[0].get('nisab_simpanan'),
                22000.0
            )
            kadar = self._safe_float(
                nisab_data.get('kadar_zakat') if isinstance(nisab_data, dict) else nisab_data[0].get('kadar_zakat'),
                0.0257
            )
            
            # Check nisab & calculate zakat
            reaches_nisab = savings >= nisab_value
            zakat_amount = savings * kadar if reaches_nisab else 0.0
            
            # Build message
            if reaches_nisab:
                message = (
                    f"✅ **Simpanan anda mencapai nisab**\n\n"
                    f"💰 **Jumlah Zakat: RM{zakat_amount:,.2f}**\n\n"
                    f"📊 **Butiran Pengiraan:**\n"
                    f"• Jumlah simpanan: RM{savings:,.2f}\n"
                    f"• Nisab ({year} {year_type}): RM{nisab_value:,.2f}\n"
                    f"• Kadar zakat: {kadar * 100:.2f}%"
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
                    'rate': kadar,
                    'shortfall': round(nisab_value - savings, 2) if not reaches_nisab else 0
                }
            }
            
        except ValueError:
            return {'success': False, 'error': 'Sila masukkan nilai yang sah', 'type': 'savings'}
        except Exception as e:
            print(f"Error in calculate_savings_zakat: {e}")
            return {'success': False, 'error': 'Ralat pengiraan', 'type': 'savings'}
        

    def calculate_padi_zakat(self, jumlah_rm: float, year: str, year_type: str = 'H') -> Dict:
        """Calculate zakat for padi (rice) - input total value in RM
        """
        try:
            total_value = self._safe_float(jumlah_rm)
            
            if total_value <= 0:
                return {
                    'success': True,
                    'zakat_amount': 0.0,
                    'zakatable_amount': 0.0,
                    'reaches_nisab': False,
                    'message': '❌ Nilai tidak sah. Sila masukkan nilai yang betul.',
                    'type': 'padi'
                }
            
            # FIXED: Get padi nisab from JomZakat API (NISABPADI field)
            print(f"[PADI] Fetching nisab for year {year} ({year_type})")
            nisab_result = self.fetch_nisab_extended('padi', year, year_type)
            
            # Extract nisab value (default to 1300.49 RM if API fails)
            nisab_rm = self._safe_float(nisab_result.get('nisab', 1300.49))
            
            if self.DEBUG:
                print(f"[DEBUG] Padi nisab for year {year}: RM{nisab_rm}")
                print(f"[DEBUG] Nisab source: {nisab_result.get('source', 'unknown')}")
            
            # Check nisab & calculate zakat (10%)
            reaches_nisab = total_value >= nisab_rm
            zakat_amount = total_value * 0.10 if reaches_nisab else 0.0
            
            # Build message
            year_label = 'Hijrah' if year_type == 'H' else 'Masihi'
            
            if reaches_nisab:
                message = (
                    f"✅ **Hasil padi anda mencapai nisab**\n\n"
                    f"💰 **Jumlah Zakat: RM{zakat_amount:,.2f}**\n\n"
                    f"📊 **Butiran Pengiraan:**\n"
                    f"• Jumlah hasil: RM{total_value:,.2f}\n"
                    f"• Nisab ({year} {year_label}): RM{nisab_rm:,.2f}\n"
                    f"• Kadar zakat: 10%\n\n"
                    f"ℹ️ Zakat padi dikira sebanyak 10% daripada jumlah hasil."
                )
            else:
                shortfall = nisab_rm - total_value
                message = (
                    f"ℹ️ **Hasil padi anda belum mencapai nisab**\n\n"
                    f"Tiada zakat perlu dibayar pada masa ini.\n\n"
                    f"📊 **Butiran:**\n"
                    f"• Jumlah hasil: RM{total_value:,.2f}\n"
                    f"• Nisab ({year} {year_label}): RM{nisab_rm:,.2f}\n"
                    f"• Kekurangan: RM{shortfall:,.2f}"
                )

            return {
                'success': True,
                'zakat_amount': round(zakat_amount, 2),
                'zakatable_amount': round(total_value, 2),
                'reaches_nisab': reaches_nisab,
                'nisab_value': round(nisab_rm, 2),
                'message': message,
                'type': 'padi',
                'year': year,
                'year_type': year_label,
                'details': {
                    'total_value_rm': round(total_value, 2),
                    'nisab_rm': round(nisab_rm, 2),
                    'rate': 0.10,
                    'rate_percent': 10.0,
                    'shortfall': round(nisab_rm - total_value, 2) if not reaches_nisab else 0,
                    'nisab_source': nisab_result.get('source', 'fallback'),
                    'api_fallback': nisab_result.get('fallback', False)
                }
            }

        except Exception as e:
            print(f"❌ Error in calculate_padi_zakat: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': f'Ralat pengiraan zakat padi: {str(e)}',
                'type': 'padi'
            }
        
    def calculate_saham_zakat(self, nama_saham: str, bilangan_unit: float, 
                            harga_seunit: float, year: str, year_type: str = 'H') -> Dict:
        """Calculate zakat for saham (shares/stocks)
        
        Based on JomZakat calculation:
        - Input: Nama Saham, Bilangan Unit, Harga Seunit
        - Formula: Jumlah Saham = Bilangan Unit × Harga Seunit
        - Check: Jumlah Saham ≥ Kadar Nisab (RM38,618.66)
        - If YES: Zakat = Jumlah Saham × 2.577%
        - If NO: Zakat = 0
        """
        try:
            bilangan = self._safe_float(bilangan_unit)
            harga = self._safe_float(harga_seunit)
            nama = str(nama_saham).strip() if nama_saham else ""
            
            # Validation
            if bilangan <= 0:
                return {
                    'success': True,
                    'zakat_amount': 0.0,
                    'zakatable_amount': 0.0,
                    'reaches_nisab': False,
                    'message': '❌ Bilangan unit tidak sah.',
                    'type': 'saham'
                }
            
            if harga <= 0:
                return {
                    'success': True,
                    'zakat_amount': 0.0,
                    'zakatable_amount': 0.0,
                    'reaches_nisab': False,
                    'message': '❌ Harga seunit tidak sah.',
                    'type': 'saham'
                }
            
            # Fetch nisab for saham from JomZakat API
            nisab_result = self.fetch_nisab_extended('saham', year, year_type)
            
            if nisab_result.get('success') and nisab_result.get('nisab'):
                kadar_nisab_rm = self._safe_float(nisab_result.get('nisab'))
            else:
                # Fallback: Try main API for NISABSAHAM field
                main_result = self.fetch_nisab_data(year, year_type)
                if main_result.get('success'):
                    api_data = main_result.get('raw', {})
                    if isinstance(api_data, list) and api_data:
                        api_data = api_data[0]
                    # NISABSAHAM field contains saham-based nisab for saham
                    kadar_nisab_rm = self._safe_float(api_data.get('NISABSAHAM', 38618.66))
                else:
                    kadar_nisab_rm = 38618.66  # Final fallback
            
            if self.DEBUG:
                print(f"[DEBUG] Saham calculation:")
                print(f"  Nama: {nama}")
                print(f"  Bilangan unit: {bilangan}")
                print(f"  Harga seunit: RM{harga}")
                print(f"  Kadar nisab: RM{kadar_nisab_rm}")
            
            # STEP 1: Calculate total value (Jumlah Saham)
            jumlah_saham = bilangan * harga
            
            # STEP 2: Check if total value reaches nisab
            reaches_nisab = jumlah_saham >= kadar_nisab_rm
            
            # STEP 3: Calculate zakat if reaches nisab
            # Zakat = Jumlah Saham × 2.577%
            if reaches_nisab:
                zakat_amount = self._round_currency(jumlah_saham * 0.02577)
            else:
                zakat_amount = 0.0
            
            if self.DEBUG:
                print(f"  Jumlah saham: RM{jumlah_saham}")
                print(f"  Reaches nisab: {reaches_nisab}")
                print(f"  Zakat amount: RM{zakat_amount}")
            
            # Build message
            year_label = 'Hijrah' if year_type == 'H' else 'Masihi'
            nama_display = f" ({nama})" if nama else ""
            
            if reaches_nisab:
                message = (
                    f"✅ **Saham anda mencapai nisab{nama_display}**\n\n"
                    f"💰 **Jumlah Zakat: RM{zakat_amount:,.2f}**\n\n"
                    f"📊 **Butiran Pengiraan:**\n"
                    f"• Bilangan unit: {bilangan:,.0f}\n"
                    f"• Harga seunit: RM{harga:,.2f}\n"
                    f"• Jumlah saham: RM{jumlah_saham:}\n"
                    f"• Kadar nisab ({year} {year_label}): RM{kadar_nisab_rm:,.2f}\n"
                    f"ℹ️ Zakat saham dikira sebanyak 2.577% daripada jumlah saham."
                )
            else:
                shortfall = kadar_nisab_rm - jumlah_saham
                message = (
                    f"ℹ️ **Saham anda belum mencapai nisab{nama_display}**\n\n"
                    f"Tiada zakat perlu dibayar pada masa ini.\n\n"
                    f"📊 **Butiran:**\n"
                    f"• Bilangan unit: {bilangan:,.0f}\n"
                    f"• Harga seunit: RM{harga:,.2f}\n"
                    f"• Jumlah saham: RM{jumlah_saham:,.2f}\n"
                    f"• Kadar nisab ({year} {year_label}): RM{kadar_nisab_rm:,.2f}\n"
                    f"• Kekurangan: RM{shortfall:,.2f}"
                )
            
            return {
                'success': True,
                'zakat_amount': round(zakat_amount, 2),
                'zakatable_amount': round(jumlah_saham, 2),
                'reaches_nisab': reaches_nisab,
                'nisab_value': round(kadar_nisab_rm, 2),
                'message': message,
                'type': 'saham',
                'year': year,
                'year_type': year_label,
                'details': {
                    'nama_saham': nama,
                    'bilangan_unit': bilangan,
                    'harga_seunit': round(harga, 2),
                    'jumlah_saham': round(jumlah_saham, 2),
                    'kadar_nisab_rm': round(kadar_nisab_rm, 2),
                    'rate': 0.02577,
                    'rate_percent': 2.577,
                    'shortfall': round(kadar_nisab_rm - jumlah_saham, 2) if not reaches_nisab else 0
                }
            }
            
        except Exception as e:
            print(f"Error in calculate_saham_zakat: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': 'Ralat pengiraan', 'type': 'saham'}

        
    def calculate_perak_zakat(self, berat_perak_g: float, year: str, year_type: str = 'H') -> Dict:
        """Calculate zakat for perak (silver)
        
        Fetches perak price (RM per gram) from JomZakat API
        User only needs to input: berat_perak_g (weight in grams)
        
        Two types of nisab:
        - NILAI nisab: 595 gram (fixed weight threshold)
        - KADAR nisab: RM value from API (for display/reference only)
        
        Calculation Flow:
        1. Get weight from user
        2. Check if weight >= NILAI nisab (595g)
        3. If YES:
        - Calculate value = weight × price_per_gram
        - Calculate zakat = value × 2.577%
        4. If NO: zakat = 0
        """
        try:
            berat = self._safe_float(berat_perak_g)
            
            if berat <= 0:
                return {
                    'success': True,
                    'zakat_amount': 0.0,
                    'zakatable_amount': 0.0,
                    'reaches_nisab': False,
                    'message': '❌ Nilai berat tidak sah. Sila masukkan nilai yang betul.',
                    'type': 'perak'
                }
            
            # Fetch data from JomZakat API
            nisab_result = self.fetch_nisab_data(year, year_type)
            if not nisab_result.get('success'):
                return {'success': False, 'error': 'Gagal mendapatkan data nisab dari API', 'type': 'perak'}
            
            # Extract data from API response
            api_data = nisab_result.get('raw', {})
            if isinstance(api_data, list) and api_data:
                api_data = api_data[0]
            
            # NILAI NISAB (weight threshold) - FIXED at 595 gram
            nilai_nisab_gram = 595.0
            
            # KADAR NISAB (RM value from API for display) - NISABPERAK field
            kadar_nisab_rm = self._safe_float(api_data.get('NISABPERAK', 1378.44))
            
            # Get perak price per gram (RM) from API - NILAIPERAK field
            harga_per_gram = self._safe_float(api_data.get('NILAIPERAK', 2.32))
            
            if self.DEBUG:
                print(f"[DEBUG] Perak calculation:")
                print(f"  User weight: {berat}g")
                print(f"  NILAI nisab (threshold): {nilai_nisab_gram}g")
                print(f"  KADAR nisab (RM value): RM{kadar_nisab_rm}")
                print(f"  Price per gram: RM{harga_per_gram}")
            
            # STEP 1: Check if weight reaches NILAI nisab (595g)
            reaches_nisab = berat >= nilai_nisab_gram
            
            # STEP 2: Calculate value and zakat ONLY if reaches nisab
            if reaches_nisab:
                total_value = berat * harga_per_gram
                zakat_amount = total_value * 0.02577
            else:
                total_value = 0.0
                zakat_amount = 0.0
            
            if self.DEBUG:
                print(f"  Reaches nisab: {reaches_nisab}")
                print(f"  Total value: RM{total_value}")
                print(f"  Zakat amount: RM{zakat_amount}")
            
            # Build message
            year_label = 'Hijrah' if year_type == 'H' else 'Masihi'
            
            if reaches_nisab:
                message = (
                    f"✅ **Perak anda mencapai nisab**\n\n"
                    f"💰 **Jumlah Zakat: RM{zakat_amount:,.2f}**\n\n"
                    f"📊 **Butiran Pengiraan:**\n"
                    f"• Berat perak: {berat:,.2f} gram\n"
                    f"• Nilai nisab: {nilai_nisab_gram:,.0f} gram\n"
                    f"• Kadar nisab: RM{kadar_nisab_rm:,.2f}\n"
                    f"• Harga per gram: RM{harga_per_gram:,.2f}\n"
                    f"• Nilai perak: RM{total_value:,.2f}\n"
                    f"ℹ️ Zakat perak dikira sebanyak 2.577% daripada nilai perak anda."
                )
            else:
                shortfall = nilai_nisab_gram - berat
                message = (
                    f"ℹ️ **Perak anda belum mencapai nisab**\n\n"
                    f"Tiada zakat perlu dibayar pada masa ini.\n\n"
                    f"📊 **Butiran:**\n"
                    f"• Berat perak: {berat:,.2f} gram\n"
                    f"• Nilai nisab: {nilai_nisab_gram:,.0f} gram\n"
                    f"• Kadar nisab: RM{kadar_nisab_rm:,.2f}\n"
                    f"• Kekurangan: {shortfall:,.2f} gram\n\n"
                    f"ℹ️ Anda memerlukan {shortfall:,.2f} gram lagi untuk mencapai nisab."
                )
            
            return {
                'success': True,
                'zakat_amount': round(zakat_amount, 2),
                'zakatable_amount': round(total_value, 2),
                'reaches_nisab': reaches_nisab,
                'nisab_value': nilai_nisab_gram,  # Weight threshold
                'nisab_value_rm': kadar_nisab_rm,  # RM value for reference
                'message': message,
                'type': 'perak',
                'year': year,
                'year_type': year_label,
                'details': {
                    'berat_perak_g': round(berat, 2),
                    'nilai_nisab_gram': nilai_nisab_gram,
                    'kadar_nisab_rm': round(kadar_nisab_rm, 2),
                    'harga_per_gram': round(harga_per_gram, 2),
                    'total_value': round(total_value, 2),
                    'rate': 0.02577,
                    'rate_percent': 2.577,
                    'harga_source': 'jomzakat_api',
                    'shortfall_g': round(nilai_nisab_gram - berat, 2) if not reaches_nisab else 0
                }
            }

        except Exception as e:
            print(f"❌ Error in calculate_perak_zakat: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': f'Ralat pengiraan zakat perak: {str(e)}',
                'type': 'perak'
            }
            
    def calculate_kwsp_zakat(self, jumlah_akaun_1: float, jumlah_akaun_2: float,
                            jumlah_pengeluaran: float, year: str, year_type: str = 'H') -> Dict:
        """Calculate zakat for KWSP (EPF)"""
        try:
            akaun_1 = self._safe_float(jumlah_akaun_1)
            akaun_2 = self._safe_float(jumlah_akaun_2)
            pengeluaran = self._safe_float(jumlah_pengeluaran)

            if akaun_1 < 0 or akaun_2 < 0 or pengeluaran < 0:
                return {
                    'success': True,
                    'zakat_amount': 0.0,
                    'zakatable_amount': 0.0,
                    'reaches_nisab': False,
                    'message': '❌ Nilai tidak sah.',
                    'type': 'kwsp'
                }

            # Get nisab value in RM
            nisab_result = self.fetch_nisab_data(year, year_type)
            if nisab_result.get('success'):
                nisab_value = self._safe_float(
                    nisab_result['data'].get('nisab_simpanan', 22000),
                    22000.0
                )
            else:
                nisab_value = 22000.0

            # Total savings
            simpanan_sedia_ada = akaun_1 + akaun_2

            # Check nisab using TOTAL savings (not withdrawal)
            reaches_nisab = simpanan_sedia_ada >= nisab_value

            # Zakat only on withdrawn amount
            if reaches_nisab and pengeluaran > 0:
                zakatable = pengeluaran
                zakat_amount = pengeluaran * 0.02577
            else:
                zakatable = 0
                zakat_amount = 0.0

            # Build message
            if reaches_nisab:
                if pengeluaran > 0:
                    message = (
                        f"✅ **KWSP anda mencapai nisab**\n\n"
                        f"💰 **Jumlah Zakat: RM{zakat_amount:,.2f}**\n\n"
                        f"📊 **Butiran Pengiraan:**\n"
                        f"• Akaun 1: RM{akaun_1:,.2f}\n"
                        f"• Akaun 2: RM{akaun_2:,.2f}\n"
                        f"• Jumlah Simpanan: RM{simpanan_sedia_ada:,.2f}\n"
                        f"• Pengeluaran: RM{pengeluaran:,.2f}\n"
                        f"• Kadar zakat: 2.577%"
                    )
                else:
                    message = (
                        f"ℹ️ **KWSP anda mencapai nisab tetapi tiada pengeluaran dibuat.**\n\n"
                        f"Tiada zakat dikenakan sehingga pengeluaran dilakukan.\n\n"
                        f"📊 **Maklumat:**\n"
                        f"• Simpanan: RM{simpanan_sedia_ada:,.2f}\n"
                        f"• Nisab: RM{nisab_value:,.2f}"
                    )
            else:
                message = (
                    f"ℹ️ **KWSP anda belum mencapai nisab**\n\n"
                    f"Tiada zakat dikenakan.\n\n"
                    f"📊 **Maklumat:**\n"
                    f"• Simpanan: RM{simpanan_sedia_ada:,.2f}\n"
                    f"• Nisab: RM{nisab_value:,.2f}"
                )

            return {
                'success': True,
                'zakat_amount': round(zakat_amount, 2),
                'zakatable_amount': round(zakatable, 2),
                'reaches_nisab': reaches_nisab,
                'nisab_value': round(nisab_value, 2),
                'message': message,
                'type': 'kwsp',
                'year': year,
                'year_type': 'Hijrah' if year_type == 'H' else 'Masihi',
                'details': {
                    'akaun_1': round(akaun_1, 2),
                    'akaun_2': round(akaun_2, 2),
                    'simpanan_sedia_ada': round(simpanan_sedia_ada, 2),
                    'pengeluaran': round(pengeluaran, 2),
                    'rate': 0.02577
                }
            }

        except Exception as e:
            print(f"Error in calculate_kwsp_zakat: {e}")
            return {'success': False, 'error': 'Ralat pengiraan', 'type': 'kwsp'}


    # ========================================================================
    # UTILITY & INFO FUNCTIONS
    # ========================================================================

    def get_nisab_info(self, year: str, year_type: str = 'H') -> Dict:
        """Get current nisab values summary"""
        try:
            res = self.fetch_nisab_data(year, year_type)
            if not res.get('success'):
                return {'success': False, 'error': res.get('error')}

            data = res.get('data', {})
            nisab_pd = self._safe_float(data.get('nisab_pendapatan'), 22000.0)
            nisab_sp = self._safe_float(data.get('nisab_simpanan'), nisab_pd)
            kadar = self._safe_float(data.get('kadar_zakat'), 0.0257)

            reply = (
                f"📊 Maklumat Nisab Tahun {year} ({'Hijrah' if year_type=='H' else 'Masihi'})\n\n"
                f"• Nisab Pendapatan: RM{nisab_pd:,.2f} setahun\n"
                f"• Nisab Simpanan: RM{nisab_sp:,.2f}\n"
                f"• Kadar Zakat: {kadar*100:.2f}%"
            )

            return {
                'success': True,
                'reply': reply,
                'data': {
                    'nisab_pendapatan': nisab_pd,
                    'nisab_simpanan': nisab_sp,
                    'kadar_zakat_fraction': kadar,
                    'kadar_zakat_percent': round(kadar * 100, 2)
                },
                'source': 'jom.zakatkedah.com.my'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_nisab_extended(self, zakat_type: str, year: str, year_type: str = 'H') -> Dict:
        """Get nisab info for extended zakat types"""
        try:
            nisab_result = self.fetch_nisab_extended(zakat_type, year, year_type)
            
            if not nisab_result.get('success'):
                return {'success': False, 'error': 'Gagal mendapatkan data nisab'}
            
            nisab_value = nisab_result.get('nisab', 0)
            unit = nisab_result.get('unit', '')
            type_info = {
                'padi': {'unit': 'kg', 'rate': '10%'},
                'saham': {'unit': unit or 'RM', 'rate': '2.577%'},
                'perak': {'unit': 'gram', 'rate': '2.577%'},
                'kwsp': {'unit': unit or 'RM', 'rate': '2.577%'}
            }
            
            info = type_info.get(zakat_type, {'unit': '', 'rate': '2.5%'})
            reply = (
                f"📊 Maklumat Nisab {zakat_type.capitalize()} - Tahun {year} "
                f"({'Hijrah' if year_type=='H' else 'Masihi'})\n\n"
                f"• Nisab: {nisab_value:,.2f} {info['unit']}\n"
                f"• Kadar Zakat: {info['rate']}"
            )
            
            return {
                'success': True,
                'reply': reply,
                'data': {
                    'nisab': nisab_value,
                    'unit': info['unit'],
                    'rate': info['rate'],
                    'type': zakat_type
                },
                'source': 'jom.zakatkedah.com.my'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def check_amount_against_years(self, amount: float, years: List[str],
                                   year_type: str = 'H', amount_kind: str = 'net') -> Dict:
        """Check a given amount against nisab for multiple years"""
        results = {}
        for y in years:
            try:
                res = self.fetch_nisab_data(y, year_type)
                if not res.get('success'):
                    results[y] = {'error': res.get('error', 'unknown')}
                    continue
                
                data = res['data'] or {}
                nisab_value = self._safe_float(
                    data.get('nisab_simpanan' if amount_kind == 'savings' else 'nisab_pendapatan'),
                    22000.0
                )
                kadar = self._safe_float(data.get('kadar_zakat'), 0.0257)
                
                reaches = amount >= nisab_value
                zakat = round((amount * kadar) if reaches else 0.0, 2)
                
                results[y] = {
                    'nisab': nisab_value,
                    'kadar': kadar,
                    'reaches': reaches,
                    'zakat': zakat
                }
            except Exception as e:
                results[y] = {'error': str(e)}
        
        return {
            'success': True,
            'checked_amount': amount,
            'kind': amount_kind,
            'results': results
        }