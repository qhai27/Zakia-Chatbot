"""
Zakat Calculator Module for ZAKIA Chatbot
Integrates with LZNK API for real-time nisab values
"""

import requests
import re
import json
from typing import Dict, List

class ZakatCalculator:
    BASE_API_URL = "https://jom.zakatkedah.com.my"

    def __init__(self, debug: bool = False):
        self.current_nisab_data = {}
        self.available_years = {}
        self.DEBUG = debug

    def _parse_kadar(self, raw) -> float:
        """Return rate as fraction (e.g. 0.0257 for 2.57%)"""
        if raw is None:
            return 0.0257
        s = str(raw).strip()
        try:
            if s.endswith('%'):
                return float(s.rstrip('%')) / 100.0
            v = float(s)
            if v > 1:
                return v / 100.0
            return v
        except Exception:
            return 0.0257

    def _parse_amount(self, s: str) -> float:
        """Parse monetary string like 'RM 22,000.00' or '22,000' -> float"""
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
        """Extract nisab pendapatan / simpanan and kadar from raw HTML/text responses."""
        out = {'nisab_pendapatan': None, 'nisab_simpanan': None, 'kadar_zakat': None}

        lowered = text.lower()
        
        # nisab pendapatan
        m = re.search(r'(nisab pendapatan)[\s\:\-]*RM\.?\s*([\d,]+(?:\.\d+)?)', lowered, flags=re.I)
        if m:
            out['nisab_pendapatan'] = self._parse_amount(m.group(2))
        
        # nisab simpanan
        m = re.search(r'(nisab simpanan)[\s\:\-]*RM\.?\s*([\d,]+(?:\.\d+)?)', lowered, flags=re.I)
        if m:
            out['nisab_simpanan'] = self._parse_amount(m.group(2))

        # kadar
        m = re.search(r'kadar(?:\s*zakat)?[^\d]*(\d+(?:\.\d+)?)\s*%?', lowered, flags=re.I)
        if m:
            out['kadar_zakat'] = self._parse_kadar(m.group(1))

        # fallback extraction
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

        if out['nisab_pendapatan'] is None:
            out['nisab_pendapatan'] = 22000.0
        if out['nisab_simpanan'] is None:
            out['nisab_simpanan'] = out['nisab_pendapatan']
        if out['kadar_zakat'] is None:
            m = re.search(r'(\d+(?:\.\d+)?)\s*%', text)
            if m:
                out['kadar_zakat'] = self._parse_kadar(m.group(1))
            else:
                out['kadar_zakat'] = 0.0257

        return out

    def fetch_nisab_data(self, year: str, year_type: str = 'H') -> Dict:
        """Fetch nisab/kadar info for a given year"""
        url = f"{self.BASE_API_URL}/koding/kalkulator.php"
        params = {'mode': 'semakHaul', 'haul': year}
        headers = {'User-Agent': 'ZAKIA/1.0'}
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=12)
            resp.raise_for_status()
            text = resp.text or ''
            
            parsed = None
            try:
                parsed = resp.json()
            except ValueError:
                parsed = None

            data = {}
            if isinstance(parsed, dict):
                data = parsed
            elif isinstance(parsed, list) and parsed:
                if isinstance(parsed[0], dict):
                    data = parsed[0]
                else:
                    data = {}
            else:
                data = {}

            def pick(d, keys):
                for k in keys:
                    if k in d and d[k] not in (None, ''):
                        return d[k]
                return None

            nisab_pendapatan = pick(data, ['nisab_pendapatan','nisabPendapatan','nisab','nisab_pendapatan_rm','nilai_nisab'])
            nisab_simpanan = pick(data, ['nisab_simpanan','nisabSimpanan','nisab_simpanan_rm'])
            kadar_raw = pick(data, ['kadar_zakat','kadar','kadar_zakat_persen','kadar_zakat_percent','percent'])

            if nisab_pendapatan is not None:
                nisab_pendapatan = self._parse_amount(str(nisab_pendapatan))
            if nisab_simpanan is not None:
                nisab_simpanan = self._parse_amount(str(nisab_simpanan))
            kadar = None
            if kadar_raw is not None:
                kadar = self._parse_kadar(kadar_raw)

            if nisab_pendapatan in (None, 0.0) or nisab_simpanan in (None, 0.0) or kadar is None:
                parsed_from_text = self._extract_nisab_from_text(text)
                nisab_pendapatan = nisab_pendapatan or parsed_from_text.get('nisab_pendapatan')
                nisab_simpanan = nisab_simpanan or parsed_from_text.get('nisab_simpanan')
                kadar = kadar or parsed_from_text.get('kadar_zakat')

            if not nisab_pendapatan:
                nisab_pendapatan = 22000.0
            if not nisab_simpanan:
                nisab_simpanan = nisab_pendapatan
            if not kadar:
                kadar = 0.0257

            normalized = {
                'nisab_pendapatan': float(nisab_pendapatan),
                'nisab_simpanan': float(nisab_simpanan),
                'kadar_zakat': float(kadar)
            }

            self.current_nisab_data = normalized
            return {'success': True, 'data': normalized, 'raw': parsed if parsed is not None else text}
        except requests.RequestException as e:
            return {'success': False, 'error': str(e)}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def fetch_available_years(self, year_type: str = 'H') -> Dict:
        """Fetch available years from LZNK endpoint"""
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
                        if key in data and isinstance(data[key], (list,tuple)):
                            years = [str(x) for x in data[key]]
                            break
                    if years is None:
                        cand = []
                        for v in data.values():
                            if isinstance(v, (list,tuple)):
                                cand.extend(v)
                        if cand:
                            years = [str(x) for x in cand]
            except ValueError:
                years = None

            if years is None:
                found = re.findall(r'\d{3,4}', text)
                if found:
                    years = sorted(list(set(found)), reverse=True)
                else:
                    years = []

            self.available_years[year_type] = years
            return {'success': True, 'years': years, 'raw': text}
        except requests.RequestException as e:
            return {'success': False, 'error': str(e), 'years': []}
        except Exception as e:
            return {'success': False, 'error': str(e), 'years': []}

    def calculate_income_zakat_kaedah_a(self, gross_income: float, year: str, 
                                        year_type: str = 'H') -> Dict:
        """
        Calculate zakat on income using Kaedah A (Tanpa Tolakan)
        Zakat is calculated on gross income without any deductions
        """
        try:
            income = float(gross_income)
            
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
            
            nisab_value = 22000
            try:
                if isinstance(nisab_data, dict):
                    nisab_value = float(nisab_data.get('nisab_pendapatan', 22000))
                elif isinstance(nisab_data, list) and len(nisab_data) > 0:
                    nisab_value = float(nisab_data[0].get('nisab_pendapatan', 22000))
            except (ValueError, AttributeError, TypeError):
                nisab_value = 22000
            
            # Get zakat rate
            zakat_rate = 0.0257
            try:
                raw_kadar = None
                if isinstance(nisab_data, dict):
                    raw_kadar = nisab_data.get('kadar_zakat', nisab_data.get('kadar', None))
                elif isinstance(nisab_data, list) and len(nisab_data) > 0:
                    raw_kadar = nisab_data[0].get('kadar_zakat', nisab_data[0].get('kadar', None))
                if raw_kadar is not None:
                    kv = float(raw_kadar)
                    zakat_rate = kv/100.0 if kv > 1 else kv
            except Exception:
                zakat_rate = 0.0257
            
            # Calculate zakat directly on gross income (no deductions)
            zakatable_amount = income
            
            # Check if reaches nisab
            reaches_nisab = zakatable_amount >= nisab_value
            zakat_amount = zakatable_amount * zakat_rate if reaches_nisab else 0.0
            
            # Generate detailed message
            if reaches_nisab:
                message = (
                    f"✅ **Pendapatan anda mencapai nisab (Kaedah A - Tanpa Tolakan)**\n\n"
                    f"💰 **Jumlah Zakat: RM{zakat_amount:,.2f}**\n\n"
                    f"📊 **Butiran Pengiraan:**\n"
                    f"• Pendapatan kasar: RM{income:,.2f}\n"
                    f"• Nisab ({year} {year_type}): RM{nisab_value:,.2f}\n"
                    f"• Kadar zakat: {zakat_rate * 100:.2f}%\n\n"
                    f"ℹ️ Kaedah A: Zakat dikira berdasarkan pendapatan kasar tanpa tolakan"
                )
            else:
                shortfall = nisab_value - zakatable_amount
                message = (
                    f"ℹ️ **Pendapatan anda belum mencapai nisab (Kaedah A - Tanpa Tolakan)**\n\n"
                    f"Tiada zakat perlu dibayar pada masa ini.\n\n"
                    f"📊 **Butiran:**\n"
                    f"• Pendapatan kasar: RM{zakatable_amount:,.2f}\n"
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
                'type': 'income_kaedah_a',
                'year': year,
                'year_type': 'Hijrah' if year_type == 'H' else 'Masihi',
                'details': {
                    'gross_income': round(income, 2),
                    'rate': zakat_rate,
                    'shortfall': round(nisab_value - zakatable_amount, 2) if not reaches_nisab else 0
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
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': f'Ralat pengiraan: Sila cuba lagi',
                'type': 'income_kaedah_a'
            }

    def calculate_income_zakat_kaedah_b(self, annual_income: float, annual_expenses: float, 
                                        year: str, year_type: str = 'H') -> Dict:
        """
        Calculate zakat on income using Kaedah B (Dengan Tolakan)
        This is the original method with expense deductions
        """
        try:
            income = float(annual_income)
            expenses = float(annual_expenses)
            
            # Fetch nisab data
            nisab_result = self.fetch_nisab_data(year, year_type)
            
            if not nisab_result['success']:
                return nisab_result
            
            nisab_data = nisab_result['data']
            
            nisab_value = 22000
            try:
                if isinstance(nisab_data, dict):
                    nisab_value = float(nisab_data.get('nisab_pendapatan', 22000))
                elif isinstance(nisab_data, list) and len(nisab_data) > 0:
                    nisab_value = float(nisab_data[0].get('nisab_pendapatan', 22000))
            except (ValueError, AttributeError, TypeError):
                nisab_value = 22000
            
            # Get zakat rate
            zakat_rate = 0.0257
            try:
                raw_kadar = None
                if isinstance(nisab_data, dict):
                    raw_kadar = nisab_data.get('kadar_zakat', nisab_data.get('kadar', None))
                elif isinstance(nisab_data, list) and len(nisab_data) > 0:
                    raw_kadar = nisab_data[0].get('kadar_zakat', nisab_data[0].get('kadar', None))
                if raw_kadar is not None:
                    kv = float(raw_kadar)
                    zakat_rate = kv/100.0 if kv > 1 else kv
            except Exception:
                zakat_rate = 0.0257
            
            # Calculate zakatable amount with deductions
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
            
            # Check if reaches nisab
            reaches_nisab = zakatable_amount >= nisab_value
            zakat_amount = zakatable_amount * zakat_rate if reaches_nisab else 0.0
            
            # Generate detailed message
            if reaches_nisab:
                message = (
                    f"✅ **Pendapatan bersih anda mencapai nisab (Kaedah B - Dengan Tolakan)**\n\n"
                    f"💰 **Jumlah Zakat: RM{zakat_amount:,.2f}**\n\n"
                    f"📊 **Butiran Pengiraan:**\n"
                    f"• Pendapatan tahunan: RM{income:,.2f}\n"
                    f"• Perbelanjaan asas: RM{expenses:,.2f}\n"
                    f"• Pendapatan bersih: RM{zakatable_amount:,.2f}\n"
                    f"• Nisab ({year} {year_type}): RM{nisab_value:,.2f}\n"
                    f"• Kadar zakat: {zakat_rate * 100:.2f}%\n\n"
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
                    'rate': zakat_rate,
                    'shortfall': round(nisab_value - zakatable_amount, 2) if not reaches_nisab else 0
                }
            }
        
        except ValueError:
            return {
                'success': False,
                'error': 'Sila masukkan nilai yang sah (nombor sahaja)',
                'type': 'income_kaedah_b'
            }
        except Exception as e:
            print(f"Error in calculate_income_zakat_kaedah_b: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': f'Ralat pengiraan: Sila cuba lagi',
                'type': 'income_kaedah_b'
            }
    
    def calculate_savings_zakat(self, savings_amount: float, year: str, 
                               year_type: str = 'H') -> Dict:
        """Calculate zakat on savings"""
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
            
            # Get zakat rate
            zakat_rate = 0.0257
            try:
                raw_kadar = nisab_data.get('kadar_zakat', nisab_data.get('kadar', None)) if isinstance(nisab_data, dict) else None
                if raw_kadar is not None:
                    kv = float(raw_kadar)
                    zakat_rate = kv/100.0 if kv > 1 else kv
            except Exception:
                zakat_rate = 0.0257
            
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
                    f"• Kadar zakat: {zakat_rate * 100:.2f}%"
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
            res = self.fetch_nisab_data(year, year_type)
            if not res.get('success', False):
                return {'success': False, 'error': res.get('error', 'Gagal mendapatkan data nisab')}

            data = res.get('data', {}) or {}

            def to_float(v, default=0.0):
                try:
                    return float(v)
                except Exception:
                    return default

            nisab_pendapatan = to_float(data.get('nisab_pendapatan', data.get('nisab', 0)), 22000.0)
            nisab_simpanan = to_float(data.get('nisab_simpanan', nisab_pendapatan), nisab_pendapatan)

            raw_kadar = data.get('kadar_zakat', data.get('kadar', None))
            kadar_frac = None
            try:
                if raw_kadar is None:
                    kadar_frac = 0.0257
                else:
                    k = float(raw_kadar)
                    kadar_frac = (k / 100.0) if k > 1 else k
            except Exception:
                kadar_frac = 0.0257

            kadar_percent = round(kadar_frac * 100.0, 2)

            reply = (
                f"📊 Maklumat Nisab Tahun {year} ({'Hijrah' if year_type=='H' else 'Masihi'})\n\n"
                f"• Nisab Pendapatan: RM{nisab_pendapatan:,.2f} setahun\n"
                f"• Nisab Simpanan: RM{nisab_simpanan:,.2f}\n"
                f"• Kadar Zakat: {kadar_percent:.2f}%\n"
            )

            return {
                'success': True,
                'reply': reply,
                'data': {
                    'nisab_pendapatan': nisab_pendapatan,
                    'nisab_simpanan': nisab_simpanan,
                    'kadar_zakat_fraction': kadar_frac,
                    'kadar_zakat_percent': kadar_percent
                },
                'raw': res.get('raw', None),
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
                    results[y] = {'error': res.get('error', 'unknown'), 'fallback': res.get('fallback', False)}
                    continue
                data = res['data'] or {}
                
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
                    raw_kadar = data.get('kadar_zakat', data.get('kadar', 0.0257))
                    kv = float(raw_kadar)
                    kadar = kv/100.0 if kv > 1 else kv
                except Exception:
                    kadar = 0.0257
                
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

        # Add these methods to the existing ZakatCalculator class in zakat_calculator.py

    def fetch_nisab_extended(self, zakat_type: str, year: str, year_type: str = 'H') -> Dict:
        """
        Fetch nisab for extended zakat types (padi, saham, perak, kwsp)
        Uses JomZakat API with fallback defaults
        """
        url = f"{self.BASE_API_URL}/public/nisab"
        params = {'type': zakat_type, 'haul': year}
        headers = {'User-Agent': 'ZAKIA/1.0'}
        
        # Default nisab values
        defaults = {
            'padi': 1300.0,  # kg
            'saham': 85.0,   # gram emas
            'perak': 595.0,  # gram perak
            'kwsp': 85.0     # gram emas
        }
        
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=12)
            resp.raise_for_status()
            
            try:
                data = resp.json()
                if isinstance(data, dict):
                    # Extract nisab based on type
                    if zakat_type == 'padi':
                        nisab = data.get('nisab_padi', defaults['padi'])
                    elif zakat_type in ['saham', 'kwsp']:
                        nisab = data.get('nisab_emas', defaults[zakat_type])
                    elif zakat_type == 'perak':
                        nisab = data.get('nisab_perak', defaults['perak'])
                    else:
                        nisab = defaults.get(zakat_type, 0)
                    
                    return {
                        'success': True,
                        'nisab': float(nisab),
                        'raw': data
                    }
            except ValueError:
                pass
            
            # Fallback to default
            return {
                'success': True,
                'nisab': defaults.get(zakat_type, 0),
                'fallback': True
            }
            
        except requests.RequestException as e:
            print(f"API error for {zakat_type}: {e}")
            return {
                'success': True,
                'nisab': defaults.get(zakat_type, 0),
                'fallback': True,
                'error': str(e)
            }


    def calculate_padi_zakat(self, hasil_padi_kg: float, harga_beras_kg: float,
                            year: str, year_type: str = 'H') -> Dict:
        """
        Calculate zakat for padi (rice)
        Formula: zakat = hasil_padi_kg × harga_beras_kg × 0.10
        """
        try:
            hasil = float(hasil_padi_kg)
            harga = float(harga_beras_kg)
            
            if hasil <= 0 or harga <= 0:
                return {
                    'success': True,
                    'zakat_amount': 0.0,
                    'zakatable_amount': 0.0,
                    'reaches_nisab': False,
                    'message': '❌ Nilai tidak sah. Sila masukkan nilai yang betul.',
                    'type': 'padi'
                }
            
            # Fetch nisab
            nisab_result = self.fetch_nisab_extended('padi', year, year_type)
            nisab_kg = nisab_result.get('nisab', 1300.0)
            
            # Calculate total value
            total_value = hasil * harga
            
            # Check nisab
            reaches_nisab = hasil >= nisab_kg
            zakat_amount = total_value * 0.10 if reaches_nisab else 0.0
            
            # Generate message
            if reaches_nisab:
                message = (
                    f"✅ **Hasil padi anda mencapai nisab**\n\n"
                    f"💰 **Jumlah Zakat: RM{zakat_amount:,.2f}**\n\n"
                    f"📊 **Butiran Pengiraan:**\n"
                    f"• Hasil padi: {hasil:,.2f} kg\n"
                    f"• Harga beras: RM{harga:,.2f}/kg\n"
                    f"• Nilai hasil: RM{total_value:,.2f}\n"
                    f"• Nisab ({year} {year_type}): {nisab_kg:,.2f} kg\n"
                    f"• Kadar zakat: 10%\n\n"
                    f"ℹ️ Zakat padi dikira berdasarkan hasil selepas kos pengeluaran"
                )
            else:
                shortfall = nisab_kg - hasil
                message = (
                    f"ℹ️ **Hasil padi anda belum mencapai nisab**\n\n"
                    f"Tiada zakat perlu dibayar pada masa ini.\n\n"
                    f"📊 **Butiran:**\n"
                    f"• Hasil padi: {hasil:,.2f} kg\n"
                    f"• Nisab ({year} {year_type}): {nisab_kg:,.2f} kg\n"
                    f"• Kekurangan: {shortfall:,.2f} kg"
                )
            
            return {
                'success': True,
                'zakat_amount': round(zakat_amount, 2),
                'zakatable_amount': round(total_value, 2),
                'reaches_nisab': reaches_nisab,
                'nisab_value': nisab_kg,
                'message': message,
                'type': 'padi',
                'year': year,
                'year_type': 'Hijrah' if year_type == 'H' else 'Masihi',
                'details': {
                    'hasil_padi_kg': round(hasil, 2),
                    'harga_beras_kg': round(harga, 2),
                    'total_value': round(total_value, 2),
                    'rate': 0.10,
                    'shortfall': round(nisab_kg - hasil, 2) if not reaches_nisab else 0
                }
            }
            
        except Exception as e:
            print(f"Error in calculate_padi_zakat: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': 'Ralat pengiraan',
                'type': 'padi'
            }


    def calculate_saham_zakat(self, nilai_portfolio: float, hutang_saham: float,
                             year: str, year_type: str = 'H') -> Dict:
        """
        Calculate zakat for saham (shares/stocks)
        Formula: zakat = (nilai_portfolio - hutang_saham) × 0.025
        """
        try:
            portfolio = float(nilai_portfolio)
            hutang = float(hutang_saham)
            
            if portfolio <= 0:
                return {
                    'success': True,
                    'zakat_amount': 0.0,
                    'zakatable_amount': 0.0,
                    'reaches_nisab': False,
                    'message': '❌ Nilai portfolio tidak sah.',
                    'type': 'saham'
                }
            
            # Fetch nisab (85g emas)
            nisab_result = self.fetch_nisab_extended('saham', year, year_type)
            nisab_emas_g = nisab_result.get('nisab', 85.0)
            
            # Get gold price (from existing nisab data or default)
            nisab_data_result = self.fetch_nisab_data(year, year_type)
            if nisab_data_result.get('success'):
                nisab_data = nisab_data_result.get('data', {})
                # Estimate gold price from nisab_simpanan / 85g
                nisab_rm = nisab_data.get('nisab_simpanan', 22000)
                gold_price_per_gram = nisab_rm / 85.0
            else:
                gold_price_per_gram = 259.0  # fallback
            
            nisab_value = nisab_emas_g * gold_price_per_gram
            
            # Calculate zakatable amount
            zakatable = portfolio - hutang
            
            if zakatable <= 0:
                return {
                    'success': True,
                    'zakat_amount': 0.0,
                    'zakatable_amount': 0.0,
                    'reaches_nisab': False,
                    'nisab_value': nisab_value,
                    'message': '❌ Hutang melebihi nilai portfolio. Tiada zakat perlu dibayar.',
                    'type': 'saham',
                    'year': year,
                    'year_type': 'Hijrah' if year_type == 'H' else 'Masihi'
                }
            
            # Check nisab
            reaches_nisab = zakatable >= nisab_value
            zakat_amount = zakatable * 0.025 if reaches_nisab else 0.0
            
            # Generate message
            if reaches_nisab:
                message = (
                    f"✅ **Portfolio saham anda mencapai nisab**\n\n"
                    f"💰 **Jumlah Zakat: RM{zakat_amount:,.2f}**\n\n"
                    f"📊 **Butiran Pengiraan:**\n"
                    f"• Nilai portfolio: RM{portfolio:,.2f}\n"
                    f"• Hutang saham: RM{hutang:,.2f}\n"
                    f"• Nilai bersih: RM{zakatable:,.2f}\n"
                    f"• Nisab ({year} {year_type}): RM{nisab_value:,.2f} (85g emas)\n"
                    f"• Kadar zakat: 2.5%\n\n"
                    f"ℹ️ Zakat saham dikira berdasarkan nilai bersih portfolio"
                )
            else:
                shortfall = nisab_value - zakatable
                message = (
                    f"ℹ️ **Portfolio saham belum mencapai nisab**\n\n"
                    f"Tiada zakat perlu dibayar pada masa ini.\n\n"
                    f"📊 **Butiran:**\n"
                    f"• Nilai bersih: RM{zakatable:,.2f}\n"
                    f"• Nisab ({year} {year_type}): RM{nisab_value:,.2f}\n"
                    f"• Kekurangan: RM{shortfall:,.2f}"
                )
            
            return {
                'success': True,
                'zakat_amount': round(zakat_amount, 2),
                'zakatable_amount': round(zakatable, 2),
                'reaches_nisab': reaches_nisab,
                'nisab_value': round(nisab_value, 2),
                'message': message,
                'type': 'saham',
                'year': year,
                'year_type': 'Hijrah' if year_type == 'H' else 'Masihi',
                'details': {
                    'portfolio': round(portfolio, 2),
                    'hutang': round(hutang, 2),
                    'zakatable': round(zakatable, 2),
                    'rate': 0.025,
                    'shortfall': round(nisab_value - zakatable, 2) if not reaches_nisab else 0
                }
            }
            
        except Exception as e:
            print(f"Error in calculate_saham_zakat: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': 'Ralat pengiraan',
                'type': 'saham'
            }


    def calculate_perak_zakat(self, berat_perak_g: float, harga_per_gram: float,
                             year: str, year_type: str = 'H') -> Dict:
        """
        Calculate zakat for perak (silver)
        Formula: zakat = (berat_perak_g × harga_per_gram) × 0.025
        """
        try:
            berat = float(berat_perak_g)
            harga = float(harga_per_gram)
            
            if berat <= 0 or harga <= 0:
                return {
                    'success': True,
                    'zakat_amount': 0.0,
                    'zakatable_amount': 0.0,
                    'reaches_nisab': False,
                    'message': '❌ Nilai tidak sah.',
                    'type': 'perak'
                }
            
            # Fetch nisab (595g perak)
            nisab_result = self.fetch_nisab_extended('perak', year, year_type)
            nisab_g = nisab_result.get('nisab', 595.0)
            
            # Calculate value
            total_value = berat * harga
            
            # Check nisab
            reaches_nisab = berat >= nisab_g
            zakat_amount = total_value * 0.025 if reaches_nisab else 0.0
            
            # Generate message
            if reaches_nisab:
                message = (
                    f"✅ **Perak anda mencapai nisab**\n\n"
                    f"💰 **Jumlah Zakat: RM{zakat_amount:,.2f}**\n\n"
                    f"📊 **Butiran Pengiraan:**\n"
                    f"• Berat perak: {berat:,.2f} gram\n"
                    f"• Harga per gram: RM{harga:,.2f}\n"
                    f"• Nilai perak: RM{total_value:,.2f}\n"
                    f"• Nisab ({year} {year_type}): {nisab_g:,.2f} gram\n"
                    f"• Kadar zakat: 2.5%"
                )
            else:
                shortfall = nisab_g - berat
                message = (
                    f"ℹ️ **Perak anda belum mencapai nisab**\n\n"
                    f"Tiada zakat perlu dibayar pada masa ini.\n\n"
                    f"📊 **Butiran:**\n"
                    f"• Berat perak: {berat:,.2f} gram\n"
                    f"• Nisab ({year} {year_type}): {nisab_g:,.2f} gram\n"
                    f"• Kekurangan: {shortfall:,.2f} gram"
                )
            
            return {
                'success': True,
                'zakat_amount': round(zakat_amount, 2),
                'zakatable_amount': round(total_value, 2),
                'reaches_nisab': reaches_nisab,
                'nisab_value': nisab_g,
                'message': message,
                'type': 'perak',
                'year': year,
                'year_type': 'Hijrah' if year_type == 'H' else 'Masihi',
                'details': {
                    'berat_perak_g': round(berat, 2),
                    'harga_per_gram': round(harga, 2),
                    'total_value': round(total_value, 2),
                    'rate': 0.025,
                    'shortfall': round(nisab_g - berat, 2) if not reaches_nisab else 0
                }
            }
            
        except Exception as e:
            print(f"Error in calculate_perak_zakat: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': 'Ralat pengiraan',
                'type': 'perak'
            }


    def calculate_kwsp_zakat(self, jumlah_akaun_1: float, jumlah_akaun_2: float,
                            jumlah_pengeluaran: float, year: str, year_type: str = 'H') -> Dict:
        """
        Calculate zakat for KWSP (EPF)
        Logic:
        - If jumlah_pengeluaran > 0: zakat = jumlah_pengeluaran × 0.025
        - Else: zakat = (jumlah_akaun_1 + jumlah_akaun_2) × 0.025
        """
        try:
            akaun_1 = float(jumlah_akaun_1)
            akaun_2 = float(jumlah_akaun_2)
            pengeluaran = float(jumlah_pengeluaran)
            
            if akaun_1 < 0 or akaun_2 < 0 or pengeluaran < 0:
                return {
                    'success': True,
                    'zakat_amount': 0.0,
                    'zakatable_amount': 0.0,
                    'reaches_nisab': False,
                    'message': '❌ Nilai tidak sah.',
                    'type': 'kwsp'
                }
            
            # Fetch nisab (85g emas)
            nisab_result = self.fetch_nisab_extended('kwsp', year, year_type)
            nisab_emas_g = nisab_result.get('nisab', 85.0)
            
            # Get nisab value in RM
            nisab_data_result = self.fetch_nisab_data(year, year_type)
            if nisab_data_result.get('success'):
                nisab_data = nisab_data_result.get('data', {})
                nisab_value = nisab_data.get('nisab_simpanan', 22000)
            else:
                nisab_value = 22000.0
            
            # Calculate simpanan sedia ada
            simpanan_sedia_ada = akaun_1 + akaun_2
            
            # Determine zakatable amount based on KWSP logic
            if pengeluaran > 0:
                zakatable = pengeluaran
                calculation_basis = "pengeluaran"
            else:
                zakatable = simpanan_sedia_ada
                calculation_basis = "simpanan sedia ada"
            
            # Check nisab
            reaches_nisab = zakatable >= nisab_value
            zakat_amount = zakatable * 0.025 if reaches_nisab else 0.0
            
            # Generate message
            if reaches_nisab:
                message = (
                    f"✅ **KWSP anda mencapai nisab**\n\n"
                    f"💰 **Jumlah Zakat: RM{zakat_amount:,.2f}**\n\n"
                    f"📊 **Butiran Pengiraan:**\n"
                    f"• Akaun 1: RM{akaun_1:,.2f}\n"
                    f"• Akaun 2: RM{akaun_2:,.2f}\n"
                    f"• Simpanan sedia ada: RM{simpanan_sedia_ada:,.2f}\n"
                )
                
                if pengeluaran > 0:
                    message += f"• Pengeluaran: RM{pengeluaran:,.2f}\n"
                    message += f"• Asas pengiraan: Pengeluaran\n"
                else:
                    message += f"• Asas pengiraan: Simpanan sedia ada\n"
                
                message += (
                    f"• Nisab ({year} {year_type}): RM{nisab_value:,.2f} (85g emas)\n"
                    f"• Kadar zakat: 2.5%\n\n"
                    f"ℹ️ Zakat KWSP dikira berdasarkan {calculation_basis}"
                )
            else:
                shortfall = nisab_value - zakatable
                message = (
                    f"ℹ️ **KWSP anda belum mencapai nisab**\n\n"
                    f"Tiada zakat perlu dibayar pada masa ini.\n\n"
                    f"📊 **Butiran:**\n"
                    f"• Simpanan sedia ada: RM{simpanan_sedia_ada:,.2f}\n"
                )
                
                if pengeluaran > 0:
                    message += f"• Pengeluaran: RM{pengeluaran:,.2f}\n"
                
                message += (
                    f"• Nisab ({year} {year_type}): RM{nisab_value:,.2f}\n"
                    f"• Kekurangan: RM{shortfall:,.2f}"
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
                    'calculation_basis': calculation_basis,
                    'rate': 0.025,
                    'shortfall': round(nisab_value - zakatable, 2) if not reaches_nisab else 0
                }
            }
            
        except Exception as e:
            print(f"Error in calculate_kwsp_zakat: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': 'Ralat pengiraan',
                'type': 'kwsp'
            }


    def get_nisab_extended(self, zakat_type: str, year: str, year_type: str = 'H') -> Dict:
        """Get nisab info for extended zakat types"""
        try:
            nisab_result = self.fetch_nisab_extended(zakat_type, year, year_type)
            
            if not nisab_result.get('success'):
                return {
                    'success': False,
                    'error': 'Gagal mendapatkan data nisab'
                }
            
            nisab_value = nisab_result.get('nisab', 0)
            
            # Generate appropriate message based on type
            type_names = {
                'padi': 'Padi',
                'saham': 'Saham',
                'perak': 'Perak',
                'kwsp': 'KWSP'
            }
            
            type_units = {
                'padi': 'kg',
                'saham': 'gram emas',
                'perak': 'gram',
                'kwsp': 'gram emas'
            }
            
            type_name = type_names.get(zakat_type, zakat_type.capitalize())
            unit = type_units.get(zakat_type, '')
            
            reply = (
                f"📊 Maklumat Nisab {type_name} - Tahun {year} "
                f"({'Hijrah' if year_type=='H' else 'Masihi'})\n\n"
                f"• Nisab: {nisab_value:,.2f} {unit}\n"
                f"• Kadar Zakat: 2.5%" if zakat_type != 'padi' else f"• Kadar Zakat: 10%"
            )
            
            return {
                'success': True,
                'reply': reply,
                'data': {
                    'nisab': nisab_value,
                    'unit': unit,
                    'rate': 0.10 if zakat_type == 'padi' else 0.025,
                    'type': zakat_type
                },
                'raw': nisab_result.get('raw'),
                'source': 'jom.zakatkedah.com.my'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }