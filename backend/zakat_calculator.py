"""
Enhanced Zakat Calculator Module for ZAKIA Chatbot
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
            # if >1 treat as percent (2.5 => 2.5%)
            if v > 1:
                return v / 100.0
            return v
        except Exception:
            return 0.0257

    def _parse_amount(self, s: str) -> float:
        """Parse monetary string like 'RM 22,000.00' or '22,000' -> float"""
        if not s:
            return 0.0
        # remove non-digit except dot and comma, keep minus
        s = str(s)
        # common patterns: "RM 22,000", "22,000.00", "22000"
        m = re.search(r'([\d\.,]+)', s)
        if not m:
            return 0.0
        num = m.group(1).replace(',', '')
        try:
            return float(num)
        except Exception:
            return 0.0

    def _extract_nisab_from_text(self, text: str) -> Dict:
        """
        Try to extract nisab pendapatan / simpanan and kadar from raw HTML/text responses.
        Returns dict with keys nisab_pendapatan, nisab_simpanan, kadar_zakat (fraction).
        """
        out = {'nisab_pendapatan': None, 'nisab_simpanan': None, 'kadar_zakat': None}

        # Try patterns like "Nisab Simpanan: RM 22,000" or "Nisab Pendapatan RM22,000"
        patterns = [
            r'nisab\s*(?:pendapatan)?[^\dRRM]*RM\.?\s*([\d,]+(?:\.\d+)?)',  # nisab ... RM 22,000
            r'nisab\s*(?:simpanan)?[^\dRRM]*RM\.?\s*([\d,]+(?:\.\d+)?)',
            r'Nisab\s*[:\-]?\s*([\d,]+(?:\.\d+)?)',  # simple nisab number
            r'RM\s*([\d,]+(?:\.\d+)?)\s*(?:\(nisab\))?',  # RM 22000 (with nisab note)
        ]

        # search nearby text for keywords to decide pendapatan/simpanan
        lowered = text.lower()
        # try to find explicit labels
        # nisab pendapatan
        m = re.search(r'(nisab pendapatan)[\s\:\-]*RM\.?\s*([\d,]+(?:\.\d+)?)', lowered, flags=re.I)
        if m:
            out['nisab_pendapatan'] = self._parse_amount(m.group(2))
        # nisab simpanan
        m = re.search(r'(nisab simpanan)[\s\:\-]*RM\.?\s*([\d,]+(?:\.\d+)?)', lowered, flags=re.I)
        if m:
            out['nisab_simpanan'] = self._parse_amount(m.group(2))

        # try to find kadar (rate) like "Kadar Zakat 2.5%" or "kadar: 2.5"
        m = re.search(r'kadar(?:\s*zakat)?[^\d]*(\d+(?:\.\d+)?)\s*%?', lowered, flags=re.I)
        if m:
            out['kadar_zakat'] = self._parse_kadar(m.group(1))

        # if still missing, extract all numbers and heuristically pick
        if out['nisab_pendapatan'] is None or out['nisab_simpanan'] is None:
            nums = re.findall(r'RM\.?\s*([\d,]+(?:\.\d+)?)', text, flags=re.I)
            if not nums:
                nums = re.findall(r'([\d,]{4,}(?:\.\d+)?)', text)  # numbers with >=4 digits
            nums_clean = [self._parse_amount(n) for n in nums if self._parse_amount(n) > 0]
            nums_clean = sorted(set(nums_clean), reverse=True)
            if nums_clean:
                # assume largest is nisab (RM value)
                if out['nisab_pendapatan'] is None:
                    out['nisab_pendapatan'] = nums_clean[0]
                if out['nisab_simpanan'] is None:
                    out['nisab_simpanan'] = nums_clean[0]

        # final fallbacks
        if out['nisab_pendapatan'] is None:
            out['nisab_pendapatan'] = 22000.0
        if out['nisab_simpanan'] is None:
            out['nisab_simpanan'] = out['nisab_pendapatan']
        if out['kadar_zakat'] is None:
            # try to find percent anywhere
            m = re.search(r'(\d+(?:\.\d+)?)\s*%', text)
            if m:
                out['kadar_zakat'] = self._parse_kadar(m.group(1))
            else:
                out['kadar_zakat'] = 0.0257

        return out

    def fetch_nisab_data(self, year: str, year_type: str = 'H') -> Dict:
        """
        Fetch nisab/kadar info for a given year (haul).
        Calls: /koding/kalkulator.php?mode=semakHaul&haul=YEAR
        Returns standardized dict containing nisab_pendapatan, nisab_simpanan, kadar_zakat (fraction)
        """
        url = f"{self.BASE_API_URL}/koding/kalkulator.php"
        params = {'mode': 'semakHaul', 'haul': year}
        headers = {'User-Agent': 'ZAKIA/1.0'}
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=12)
            resp.raise_for_status()
            text = resp.text or ''
            # try JSON first
            parsed = None
            try:
                parsed = resp.json()
            except ValueError:
                parsed = None

            data = {}
            if isinstance(parsed, dict):
                data = parsed
            elif isinstance(parsed, list) and parsed:
                # if list of dicts, take first
                if isinstance(parsed[0], dict):
                    data = parsed[0]
                else:
                    data = {}
            else:
                # fallback to text parsing
                data = {}

            # attempt to locate nisab/kadar keys in parsed dict
            def pick(d, keys):
                for k in keys:
                    if k in d and d[k] not in (None, ''):
                        return d[k]
                return None

            nisab_pendapatan = pick(data, ['nisab_pendapatan','nisabPendapatan','nisab','nisab_pendapatan_rm','nilai_nisab'])
            nisab_simpanan = pick(data, ['nisab_simpanan','nisabSimpanan','nisab_simpanan_rm'])
            kadar_raw = pick(data, ['kadar_zakat','kadar','kadar_zakat_persen','kadar_zakat_percent','percent'])

            # normalize extracted values
            if nisab_pendapatan is not None:
                nisab_pendapatan = self._parse_amount(str(nisab_pendapatan))
            if nisab_simpanan is not None:
                nisab_simpanan = self._parse_amount(str(nisab_simpanan))
            kadar = None
            if kadar_raw is not None:
                kadar = self._parse_kadar(kadar_raw)

            # if any missing, run text extractor on full response body
            if nisab_pendapatan in (None, 0.0) or nisab_simpanan in (None, 0.0) or kadar is None:
                parsed_from_text = self._extract_nisab_from_text(text)
                nisab_pendapatan = nisab_pendapatan or parsed_from_text.get('nisab_pendapatan')
                nisab_simpanan = nisab_simpanan or parsed_from_text.get('nisab_simpanan')
                kadar = kadar or parsed_from_text.get('kadar_zakat')

            # final fallbacks to safe defaults
            if not nisab_pendapatan:
                nisab_pendapatan = 22000.0
            if not nisab_simpanan:
                nisab_simpanan = nisab_pendapatan
            if not kadar:
                kadar = 0.0257

            normalized = {
                'nisab_pendapatan': float(nisab_pendapatan),
                'nisab_simpanan': float(nisab_simpanan),
                # keep fraction (0.0257) internally
                'kadar_zakat': float(kadar)
            }

            self.current_nisab_data = normalized
            return {'success': True, 'data': normalized, 'raw': parsed if parsed is not None else text}
        except requests.RequestException as e:
            return {'success': False, 'error': str(e)}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def fetch_available_years(self, year_type: str = 'H') -> Dict:
        """
        Fetch available years from LZNK endpoint.
        year_type: 'H' (Hijrah) or 'M' (Masihi)
        Returns standardized dict: { success:bool, years: [str], raw: any, error: str? }
        """
        url = f"{self.BASE_API_URL}/kirazakat/listjenistahun.php"
        params = {'jenistahun': year_type, 'options': 'listjenistahun'}
        headers = {'User-Agent': 'ZAKIA/1.0'}

        try:
            resp = requests.get(url, params=params, headers=headers, timeout=10)
            resp.raise_for_status()
            text = resp.text.strip()

            # Try parse JSON first
            years = None
            try:
                data = resp.json()
                # Accept lists or dicts containing list under a key
                if isinstance(data, list):
                    years = [str(x) for x in data]
                elif isinstance(data, dict):
                    # try common keys
                    for key in ('years', 'list', 'data', 'jenistahun'):
                        if key in data and isinstance(data[key], (list,tuple)):
                            years = [str(x) for x in data[key]]
                            break
                    # else try to flatten dict values
                    if years is None:
                        # collect numeric-like values
                        cand = []
                        for v in data.values():
                            if isinstance(v, (list,tuple)):
                                cand.extend(v)
                        if cand:
                            years = [str(x) for x in cand]
            except ValueError:
                years = None

            # Fallback: extract year-like numbers from HTML/text
            if years is None:
                found = re.findall(r'\d{3,4}', text)
                # unique and sorted descending (prefer latest first)
                if found:
                    years = sorted(list(set(found)), reverse=True)
                else:
                    years = []

            # store
            self.available_years[year_type] = years
            return {'success': True, 'years': years, 'raw': text}
        except requests.RequestException as e:
            return {'success': False, 'error': str(e), 'years': []}
        except Exception as e:
            return {'success': False, 'error': str(e), 'years': []}

    def calculate_income_zakat(self, annual_income: float, annual_expenses: float, 
                              year: str, year_type: str = 'H') -> Dict:
        """
        Calculate zakat on income
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
            
            # Ensure zakat_rate is a fraction (e.g. 0.0257 for 2.57%)
            zakat_rate = 0.0257
            try:
                # read raw rate from nisab_data (it may be fraction or percent)
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
                    f"• Kadar zakat: {zakat_rate * 100:.2f}%"
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
            
            # Ensure zakat_rate is a fraction (0.0257)
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
            
            # Generate detailed message.
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
        """Get current nisab values (fetches from LZNK kalkulator.php)"""
        try:
            # fetch live nisab data for provided year
            res = self.fetch_nisab_data(year, year_type)
            if not res.get('success', False):
                return {'success': False, 'error': res.get('error', 'Gagal mendapatkan data nisab')}

            data = res.get('data', {}) or {}

            # normalize nisab numeric values
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
        """
        Check a given amount against nisab for multiple years using kalkulator.php.
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
                # robust kadar parsing: data may store fraction or percent
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