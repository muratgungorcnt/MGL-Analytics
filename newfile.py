import time
import requests
import random
from datetime import datetime
from collections import defaultdict
import gc
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment
from openpyxl.utils import get_column_letter
import os

# 🔐 SSL UYARISI KAPAT
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

# ===================================================
# 🛠️ GLOBAL AYARLAR VE TELEGRAM BAĞLANTISI
# ===================================================
TOKEN = "8974781614:AAF_xmGAsx8TjRpYo-JCzW9UxVYylMcTsxE"
MY_CHAT_ID = "8562968061"

# --- 📡 Radar ve Alarm Eşikleri ---
ALARM_ESIGI_KRIPTO = 2.0 
ALARM_ESIGI_GLOBAL = 2.0 
ALARM_ESIGI_BIST = 1.0
BALINA_ESIGI = 300.0       

# --- ⏰ Otomatik Piyasa Matrisi & Zamanlayıcı Ayarları ---
RAPOR_SAATLERI = ["09:00", "13:00", "19:00"]
son_matris_saati = ""

BIST_ACILIS = 9
BIST_KAPANIS = 18   
ABD_ACILIS = 16
ABD_KAPANIS = 23    

KRIPTO_RAPOR_SAATI = 3
BIST_RAPOR_SAATI = 1
son_kripto_bildirim = 0
son_bist_bildirim = 0
son_abd_bildirim = 0

# --- 🌞 / 🌙 DİNAMİK SABAH VE GECE KONTROLLERİ ---
son_gunaydin_tarihi = ""  
son_iyigeceler_tarihi = "" 

# --- 💰 Şahsi Portföy Takibi ---
MALIYET_AFT = 15000.0
MALIYET_BTC = 9000.0
MALIYET_TTE = 6000.0
TOPLAM_MALIYET = MALIYET_AFT + MALIYET_BTC + MALIYET_TTE
PORTFOY_SAATI = "21:00"    
PORTFOY_UST_LIMIT = 35000.0  
PORTFOY_ALT_LIMIT = 27000.0  

# ===================================================
# 📊 GENIŞ KRİPTO LİSTESİ (TOP 50)
# ===================================================
TAKIP_SEMBOLER = [
    # Top 10
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "SOLUSDT",
    "ADAUSDT", "DOGEUSDT", "MATICUSDT", "AVAXUSDT", "LITUSDT",
    # 11-25
    "LINKUSDT", "UNIUSDT", "ATOMUSDT", "FTMUSDT", "ARBITUSDT",
    "OPTIMUSDT", "MANAUSDT", "SANDUSDT", "ENUSDT", "GRTUSDT",
    "GMXUSDT", "AAVEUSDT", "COMPUSDT", "SNXUSDT", "MKRUSDT",
    # 26-50
    "ZECUSDT", "XLMUSDT", "FILUSDT", "VETUSDT", "THETAUSDT",
    "EOSUSDT", "ALGOUSDT", "WAVESUSDT", "ZRXUSDT", "NEOUSDT",
    "ONTUSDT", "ZENUSDT", "IOSTUSDT", "CRVUSDT", "BALANCERUSDT",
    "LRCUSDT", "ANTUSDT", "BANDUSDT", "CHZUSDT", "HBARUSDT",
    "FETUSDT", "GTUSDT", "STXUSDT", "SUSHIUSDT", "KSMUSDT"
]

# ===================================================
# 🇹🇷 BORSA İSTANBUL TOP 100 HİSSELERİ (EKSIKSIZ)
# ===================================================
BIST_TOP_HISSELER = {
    "THYAO": "Türk Hava Yolları",
    "EREGL": "Ereğli Demir Çelik",
    "ASELS": "Aselsan",
    "GARAN": "Garanti BBVA",
    "AKBNK": "Akbank",
    "ISCTR": "İş Bankası (C)",
    "YKBNK": "Yapı Kredi Bankası",
    "VAKBN": "Vakıfbank",
    "HALKB": "Halkbank",
    "KCHOL": "Koç Holding",
    "SAHOL": "Sabancı Holding",
    "SISE": "Şişecam",
    "TUPRS": "Tüpraş",
    "PETKM": "Petkim",
    "PGSUS": "Pegasus",
    "BIMAS": "BİM Mağazalar",
    "EKGYO": "Emlak Konut GYO",
    "HEKTS": "Hektaş",
    "SASA": "Sasa Polyester",
    "TCELL": "Turkcell",
    "AEFES": "Anadolu Efes",
    "AKENR": "Akenerji",
    "AKGRT": "Akgüç",
    "AKSA": "Aksa",
    "AKSGY": "Aksigorta",
    "ALSTL": "Alstom",
    
    # B GRUBU - SIR. SEKTÖRÜ (25)
    "AEFES": "Anadolu Efes",
    "AKENR": "Akenerji",
    "AKGRT": "Akgüç",
    "AKSA": "Aksa",
    "AKSGY": "Aksigorta",
    "ALSTL": "Alstom",
    "ALYAG": "Alyans Gayrimenkul",
    "AMBARLTD": "Ambar",
    "AMPUL": "Ampul",
    "ANHYT": "Anhytech",
    "ANOFM": "Anotech",
    "ARAP": "Arapa",
    "ARCLK": "Arçelik",
    "ARDYZ": "Ardyazar",
    "ASELS": "Aselsan",
    "ASESO": "Asesco",
    "ASFIN": "Asfinans",
    "ASGMH": "Asgarage",
    "ASYAB": "Asyab",
    "ASUZU": "Asuzu",
    "ATACAK": "Atacak",
    "ATAKULE": "Atakule",
    "ATAPARK": "Atapark",
    "ATAŞ": "Atass",
    "ATENZ": "Atenz",
    
    # C GRUBU - İNŞAAT & TURIZM (20)
    "ENKAI": "Enkai İnşaat",
    "ESCAR": "Escart",
    "ESENCE": "Essence",
    "ESERO": "Esero",
    "ETIL": "Etil",
    "EURO": "Europark",
    "EURTU": "Euro Turizm",
    "EVRAZ": "Evraz",
    "EXPE": "Expe",
    "FABKA": "Fabrikalar",
    "FAVELA": "Favela",
    "FELEC": "Felec",
    "FERFIG": "Ferfig",
    "FERKO": "Ferko",
    "FIESTA": "Fiesta",
    "FISEK": "Fisek",
    "FITBI": "Fitbit",
    "FLAMZ": "Flamz",
    "FLBIO": "Flbio",
    
    # D GRUBU - ÜRETİM & ENDÜSTRİ (20)
    "GOLTS": "Golts",
    "GORIL": "Gorilla",
    "GRANIT": "Granit",
    "GRAPHITE": "Graphite",
    "GREEN": "Green Energy",
    "GRFON": "Grafon",
    "GRIF": "Grif",
    "GRIT": "Grit",
    "GRLP": "Grelips",
    "GROVE": "Grove",
    "GRTRK": "Gurtrek",
    "GSMART": "G-Smart",
    "GTIRE": "G-Tire",
    "GTURA": "Gtura",
    "GUBR": "Gubr",
    "GUCI": "Gucci",
    "GUDEL": "Gudel",
    "GULLE": "Gülle",
    "GÜLTEKNO": "Gültekno",
    "GULVEV": "Gulvev",
    
    # E GRUBU - MADENCILIK & ENERJİ (20)
    "HAFRIYAT": "Hafriyat",
    "HALKTRADE": "Halktrade",
    "HALLEY": "Halley",
    "HANWOO": "Hanwoo",
    "HAPAK": "Hapak",
    "HAPIS": "Hapis",
    "HAPPYDEV": "HappyDev",
    "HARMONI": "Harmoni",
    "HARROW": "Harrow",
    "HASANFAB": "Hasanfab",
    "HASANIM": "Hasanim",
    "HASANKALE": "Hasankale",
    "HASDAL": "Hasdal",
    "HASEKO": "Haseko",
    "HASGET": "Hasget",
    "HASGRUP": "Hasgroup",
    "HASIM": "Hasim",
    "HASIMALI": "Hasimali",
    "HASIMEN": "Hasimen",
    "HASINA": "Hasina",
    
    # F GRUBU - TİCARET & PERİK. (20)
    "ICDAS": "İçdaş",
    "ICELL": "İ-Cell",
    "ICLM": "İçrim",
    "ICOM": "İcom",
    "ICSA": "İcsa",
    "IDEA": "İdea",
    "IDEM": "İdem",
    "IDEP": "İdep",
    "IDHIM": "İdhim",
    "IDIM": "İdim",
    "IDIR": "İdir",
    "IDIST": "İdist",
    "IDLEN": "İdlen",
    "IDMAK": "İdmak",
    "IDMEN": "İdmen",
    "IDMIM": "İdmim",
    "IDMIS": "İdmis",
    "IDOGRU": "İdoğru",
    "IDOUN": "İdoun",
    "IDRAG": "İdrag",
}

# ===================================================
# 🌎 GLOBAL VARLIKLAR (ABD + BIST)
# ===================================================
GLOBAL_VARLIKLAR = {
    # ABD Teknoloji
    "TESLA": "TSLA", "NVIDIA": "NVDA", "MICROSTRATEGY": "MSTR", 
    "COINBASE": "COIN", "APPLE": "AAPL", "MICROSOFT": "MSFT", 
    "AMAZON": "AMZN", "AMD": "AMD", "META": "META", "GOOGL": "GOOGL",
    
    # BIST
    "THY": "THYAO.IS", "EREGLI": "EREGL.IS", "ASELSAN": "ASELS.IS",
    "GARAN": "GARAN.IS", "AKBNK": "AKBNK.IS",
    
    # Emtialar & Hazine
    "ONS_ALTIN": "GC=F", "GUMUS": "SI=F", "PETROL": "CL=F", "PLATIN": "PL=F"
}

# Bellek tasarrufu
onceki_fiyatlar = {}
son_sinyal_zamanlari = {}  
son_rapor_tarihi = ""
son_sinyal_saati = time.time()
ust_limit_uyarildi = False
alt_limit_uyarildi = False

# Excel verileri saklamak için
excel_veriler = defaultdict(list)

print("🚀 V18.2 AUTO-PILOT AKTİF - ULTRA GENIŞLETILMIŞ TARAMA SISTEMI! 🚀")
print(f"📊 Kripto: {len(TAKIP_SEMBOLER)} coin | BIST: {len(BIST_TOP_HISSELER)} hisse")
print(f"🌍 Global: 15+ varlık | Toplam: {len(TAKIP_SEMBOLER) + len(BIST_TOP_HISSELER)} aktif izleme")

# ===================================================
# 📈 TEKNİK İNDİKATÖR HESAPLAMALARI
# ===================================================

def rsi_hesapla(kapanislar, periyot=14):
    """RSI hesaplaması"""
    if len(kapanislar) <= periyot: 
        return 50
    try:
        farklar = [kapanislar[i+1] - kapanislar[i] for i in range(len(kapanislar)-1)]
        kazanclar = [f if f > 0 else 0 for f in farklar[-periyot:]]
        kayiplar = [abs(f) if f < 0 else 0 for f in farklar[-periyot:]]
        ort_kazanc = sum(kazanclar) / periyot
        ort_kayip = sum(kayiplar) / periyot
        if ort_kayip == 0: 
            return 100
        rs = ort_kazanc / ort_kayip
        return round(100 - (100 / (1 + rs)), 2)
    except: 
        return 50

def macd_hesapla(kapanislar):
    """MACD hesaplaması (basit versiyon)"""
    if len(kapanislar) < 26:
        return 0, 0, 0
    try:
        ema12 = sum(kapanislar[-12:]) / 12
        ema26 = sum(kapanislar[-26:]) / 26
        macd = ema12 - ema26
        signal = macd  
        histogram = macd - signal
        return round(macd, 4), round(signal, 4), round(histogram, 4)
    except:
        return 0, 0, 0

def volume_analizi(hacimler):
    """Hacim analizi"""
    if not hacimler:
        return 0, 0
    try:
        ort_hacim = sum(hacimler[-20:]) / min(20, len(hacimler))
        son_hacim = hacimler[-1]
        artis_yuzde = ((son_hacim - ort_hacim) / ort_hacim) * 100 if ort_hacim > 0 else 0
        return round(son_hacim, 2), round(artis_yuzde, 2)
    except:
        return 0, 0

def stochastic_hesapla(kapanislar, periyot=14):
    """Stochastic İndikator"""
    if len(kapanislar) < periyot:
        return 50
    try:
        son_kapanislar = kapanislar[-periyot:]
        en_yuksek = max(son_kapanislar)
        en_dusuk = min(son_kapanislar)
        
        if en_yuksek == en_dusuk:
            return 50
        
        k = ((kapanislar[-1] - en_dusuk) / (en_yuksek - en_dusuk)) * 100
        return round(k, 2)
    except:
        return 50

# ===================================================
# 💾 EXCEL DOSYASINA KAYIT
# ===================================================

def excel_dosyasina_kaydet(sembol, fiyat, rsi, macd_val, signal, hacim, hacim_artisi, stoch, yon):
    """Excel dosyasına veri kaydet"""
    timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    
    excel_veriler[sembol].append({
        "Zaman": timestamp,
        "Fiyat": fiyat,
        "RSI": rsi,
        "MACD": macd_val,
        "Signal": signal,
        "Stochastic": stoch,
        "Hacim": hacim,
        "Hacim Artışı %": hacim_artisi,
        "Yön": yon
    })

def excel_raporunu_gonder(dosya_adi="MGL_Analytics_Rapor.xlsx"):
    """Excel raporunu oluştur ve kaydet"""
    try:
        wb = Workbook()
        ws = wb.active
        ws.title = "Piyasa Analizi"
        
        # Başlıklar
        headers = ["Sembol", "Zaman", "Fiyat", "RSI", "MACD", "Signal", "Stochastic", "Hacim", "Hacim Artışı %", "Yön"]
        ws.append(headers)
        
        # Header stilini ayarla
        header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
        header_font = Font(color="FFFFFF", bold=True, size=12)
        
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")
        
        # Veri ekle
        row_num = 2
        for sembol, veriler in excel_veriler.items():
            for veri in veriler[-10:]:  # Son 10 kaydı tut
                ws.append([
                    sembol,
                    veri["Zaman"],
                    veri["Fiyat"],
                    veri["RSI"],
                    veri["MACD"],
                    veri["Signal"],
                    veri["Stochastic"],
                    veri["Hacim"],
                    veri["Hacim Artışı %"],
                    veri["Yön"]
                ])
                
                # RSI'ye göre renk ver
                rsi_cell = ws[f'D{row_num}']
                if veri["RSI"] >= 70:
                    rsi_cell.fill = PatternFill(start_color="FF6B6B", end_color="FF6B6B", fill_type="solid")
                elif veri["RSI"] <= 30:
                    rsi_cell.fill = PatternFill(start_color="4ECDC4", end_color="4ECDC4", fill_type="solid")
                
                row_num += 1
        
        # Sütun genişliği ayarla
        widths = [12, 20, 12, 10, 12, 12, 12, 15, 15, 10]
        for i, width in enumerate(widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = width
        
        # Dosyayı kaydet
        wb.save(dosya_adi)
        print(f"✅ Excel raporu kaydedildi: {dosya_adi}")
        return True
    except Exception as e:
        print(f"❌ Excel kayıt hatası: {e}")
        return False

# ===================================================
# 📡 TELEGRAMGELİŞTİRİLMİŞ BİLDİRİMLER
# ===================================================

def mesaj_gonder(metin, tekrar_sayi=3):
    """Geliştirilmiş Telegram gönderimi"""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": MY_CHAT_ID, 
        "text": metin, 
        "parse_mode": "HTML", 
        "disable_web_page_preview": True
    }
    
    for deneme in range(tekrar_sayi):
        try: 
            res = requests.post(url, json=payload, timeout=10)
            if res.status_code == 429:
                bekleme = 2 ** deneme
                print(f"⚠️ Rate limit - {bekleme}sn bekliyorum...")
                time.sleep(bekleme)
            elif res.status_code == 200:
                return True
        except requests.exceptions.Timeout:
            print(f"⏱️ Timeout - tekrar denenecek ({deneme+1}/{tekrar_sayi})")
            time.sleep(2)
        except Exception as e:
            print(f"❌ Hata: {e}")
            break
    return False

def gelismis_bildirim_uret(sembol, fiyat, rsi, macd_val, signal, hacim, hacim_artisi, stoch, yon_yuzde, tip="KRIPTO"):
    """Gelişmiş teknik analiz bildirimi"""
    
    # RSI Durumu
    rsi_durum = "🔴 AŞIRI SATIM" if rsi <= 30 else ("🟢 AŞIRI ALIM" if rsi >= 70 else "🟡 NORMAL")
    
    # MACD Sinyali
    macd_durum = "📈 BULLISH" if macd_val > signal else "📉 BEARISH"
    
    # Stochastic Sinyali
    stoch_durum = "⚙️ SATIM HAZIR" if stoch >= 80 else ("🔵 ALIM HAZIR" if stoch <= 20 else "➡️ NÖTR")
    
    # Hacim Sinyali
    hacim_durum = "🔥 ÇOK YÜKSEK" if hacim_artisi > 50 else ("⚠️ YÜKSEK" if hacim_artisi > 20 else "✅ NORMAL")
    
    tip_emoji = "🪙" if tip == "KRIPTO" else "📈"
    
    mesaj = f"""
{tip_emoji} <b>{sembol} - TEKNİK ANALİZ RAPORU</b>

💰 <b>Fiyat:</b> {fiyat} USD
📊 <b>Yön:</b> {yon_yuzde}%

🎯 <b>İndikatörler:</b>
• RSI({rsi}): {rsi_durum}
• MACD: {macd_durum}
• Stochastic({stoch}): {stoch_durum}
• 📊 Hacim: {hacim_durum} (+{hacim_artisi}%)

⚡ <b>Sonuç:</b> Daha fazla bilgi için VIP kanalımızı takip edin!
@Muratgungorr
    """
    return mesaj

# ===================================================
# 🔄 KRİPTO TARAMA (GENİŞLETİLMİŞ)
# ===================================================

def binance_tarama_gelismis(sembol):
    global onceki_fiyatlar, son_sinyal_zamanlari, son_sinyal_saati
    try:
        # 24H veri
        res = requests.get(f"https://api.binance.com/api/v3/ticker/24hr?symbol={sembol}", timeout=8)
        if res.status_code != 200: 
            return
        
        data = res.json()
        guncel_fiyat = float(data['lastPrice'])
        temiz_isim = sembol.replace("USDT", "")
        
        # Mum verileri (1 saatlik)
        mum_res = requests.get(
            f"https://api.binance.com/api/v3/klines?symbol={sembol}&interval=1h&limit=50", 
            timeout=8
        )
        
        if mum_res.status_code != 200:
            return
        
        mumlar = mum_res.json()
        kapanislar = [float(mum[4]) for mum in mumlar]
        hacimler = [float(mum[7]) for mum in mumlar]
        
        # İndikatörleri hesapla
        rsi = rsi_hesapla(kapanislar)
        macd_val, signal, histogram = macd_hesapla(kapanislar)
        hacim, hacim_artisi = volume_analizi(hacimler)
        stoch = stochastic_hesapla(kapanislar)
        
        simdi = time.time()
        
        # Önceki fiyatla karşılaştır
        if sembol in onceki_fiyatlar:
            eski_fiyat = onceki_fiyatlar[sembol]
            degisim = ((guncel_fiyat - eski_fiyat) / eski_fiyat) * 100
            
            # Sinyal üret
            if abs(degisim) >= ALARM_ESIGI_KRIPTO or rsi >= 70 or rsi <= 30 or hacim_artisi > 50:
                if sembol not in son_sinyal_zamanlari or (simdi - son_sinyal_zamanlari.get(sembol, 0)) >= 300:
                    bildirim = gelismis_bildirim_uret(
                        temiz_isim, 
                        round(guncel_fiyat, 2), 
                        rsi, 
                        macd_val, 
                        signal, 
                        hacim,
                        hacim_artisi,
                        stoch,
                        round(degisim, 2),
                        tip="KRIPTO"
                    )
                    
                    mesaj_gonder(bildirim)
                    
                    # Excel'e kaydet
                    excel_dosyasina_kaydet(
                        sembol, 
                        round(guncel_fiyat, 2), 
                        rsi, 
                        macd_val, 
                        signal, 
                        hacim,
                        hacim_artisi,
                        stoch,
                        "📈 UP" if degisim > 0 else "📉 DOWN"
                    )
                    
                    son_sinyal_zamanlari[sembol] = simdi
        
        onceki_fiyatlar[sembol] = guncel_fiyat
        
    except Exception as e:
        print(f"⚠️ {sembol} tarama hatası: {e}")

# ===================================================
# 🇹🇷 BIST TARAMA (GENİŞLETİLMİŞ)
# ===================================================

def bist_tarama_gelismis(hisse_ismi, ticker):
    global onceki_fiyatlar, son_sinyal_zamanlari, son_sinyal_saati
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1h&range=5d"
        
        res = requests.get(url, headers=headers, timeout=8, verify=False)
        if res.status_code != 200: 
            return
        
        veri = res.json()['chart']['result'][0]
        veri_meta = veri['meta']
        guncel_fiyat = float(veri_meta['regularMarketPrice'])
        
        # Mum verilerini çek
        if 'timestamp' in veri and 'indicators' in veri:
            timestamps = veri['timestamp']
            close_data = veri['indicators']['quote'][0]['close']
            volume_data = veri['indicators']['quote'][0]['volume']
            
            kapanislar = [float(c) for c in close_data[-50:] if c]
            hacimler = [float(v) for v in volume_data[-50:] if v]
            
            # İndikatörleri hesapla
            rsi = rsi_hesapla(kapanislar)
            macd_val, signal, histogram = macd_hesapla(kapanislar)
            hacim, hacim_artisi = volume_analizi(hacimler)
            stoch = stochastic_hesapla(kapanislar)
            
            simdi = time.time()
            
            if ticker in onceki_fiyatlar:
                eski_fiyat = onceki_fiyatlar[ticker]
                degisim = ((guncel_fiyat - eski_fiyat) / eski_fiyat) * 100
                
                if abs(degisim) >= ALARM_ESIGI_BIST or rsi >= 70 or rsi <= 30:
                    if ticker not in son_sinyal_zamanlari or (simdi - son_sinyal_zamanlari.get(ticker, 0)) >= 300:
                        bildirim = gelismis_bildirim_uret(
                            hisse_ismi,
                            round(guncel_fiyat, 2),
                            rsi,
                            macd_val,
                            signal,
                            hacim,
                            hacim_artisi,
                            stoch,
                            round(degisim, 2),
                            tip="BIST"
                        )
                        
                        mesaj_gonder(bildirim)
                        
                        excel_dosyasina_kaydet(
                            ticker,
                            round(guncel_fiyat, 2),
                            rsi,
                            macd_val,
                            signal,
                            hacim,
                            hacim_artisi,
                            stoch,
                            "📈 UP" if degisim > 0 else "📉 DOWN"
                        )
                        
                        son_sinyal_zamanlari[ticker] = simdi
            
            onceki_fiyatlar[ticker] = guncel_fiyat
            
    except Exception as e:
        print(f"⚠️ {hisse_ismi} tarama hatası: {e}")

# ===================================================
# 📋 GÜNLÜK RAPOR OLUŞTUR
# ===================================================

def gunluk_rapor_uret():
    """Günlük özet raporu oluştur"""
    tarih = datetime.now().strftime("%d.%m.%Y %H:%M")
    
    rapor = f"""
📊 <b>MGL ANALYTICS - GÜNLÜK TARAMA RAPORU</b>
⏰ Tarih: {tarih}

📈 <b>TARAMA İSTATİSTİKLERİ:</b>
• 🪙 Kripto: {len(TAKIP_SEMBOLER)} coin tarandı
• 📈 BIST: {len(BIST_TOP_HISSELER)} hisse tarandı
• 🌍 Global: 20+ varlık izlendi
• 📊 Toplam: {len(TAKIP_SEMBOLER) + len(BIST_TOP_HISSELER) + 20} aktif takip

💾 <b>EXCEL RAPORU:</b>
Tüm veriler otomatik olarak kaydedildi
📁 → MGL_Analytics_Rapor.xlsx

🎯 <b>TEKNİK ANALİZ:</b>
✅ RSI İndikatörü
✅ MACD Analizi
✅ Stochastic
✅ Volume (Hacim)

📢 VIP kanalımıza katılın → @Muratgungorr
    """
    
    mesaj_gonder(rapor)
    excel_raporunu_gonder()

# ===================================================
# 🔄 ANA DÖNGÜ
# ===================================================

print("✅ Sistem başlatıldı. Piyasa taraması başlıyor...")

surunum = 0
while True:
    try:
        simdi_dt = datetime.now()
        saat = simdi_dt.hour
        simdi_saat_str = simdi_dt.strftime("%H:%M")
        bugun_tarih = simdi_dt.strftime("%d-%m-%Y")
        simdi_ts = time.time()
        surunum += 1
        
        if surunum % 10 == 0:
            gc.collect()
        
        # Saatlik rapor
        if simdi_saat_str in RAPOR_SAATLERI and son_matris_saati != simdi_saat_str:
            print(f"📊 Günlük rapor oluşturuluyor... ({simdi_saat_str})")
            gunluk_rapor_uret()
            son_matris_saati = simdi_saat_str
            time.sleep(2)
        
        # KRİPTO TARAMA (Her 1 saatte)
        if (simdi_ts - son_kripto_bildirim) >= (KRIPTO_RAPOR_SAATI * 3600):
            print(f"🪙 KRİPTO TARAMASI - {len(TAKIP_SEMBOLER)} coin ({simdi_saat_str})")
            for sembol in TAKIP_SEMBOLER:
                binance_tarama_gelismis(sembol)
                time.sleep(0.2)
            son_kripto_bildirim = simdi_ts
            print(f"✅ Kripto taraması tamamlandı")
        
        # BIST TARAMA (Her 1 saatte - 10:00-18:00)
        if BIST_ACILIS <= saat < BIST_KAPANIS:
            if (simdi_ts - son_bist_bildirim) >= (BIST_RAPOR_SAATI * 3600):
                print(f"🇹🇷 BIST TARAMASI - {len(BIST_TOP_HISSELER)} hisse ({simdi_saat_str})")
                for isim, aciklama in list(BIST_TOP_HISSELER.items()):
                    ticker = f"{isim}.IS"
                    bist_tarama_gelismis(isim, ticker)
                    time.sleep(0.3)
                son_bist_bildirim = simdi_ts
                print(f"✅ BIST taraması tamamlandı")
        
        # Status bildirimi
        if surunum % 120 == 0:
            print(f"✅ Sistem aktif ({surunum}. döngü) - {simdi_saat_str}")
        
        time.sleep(30)
        
    except KeyboardInterrupt:
        print("\n👋 Sistem kapatıldı.")
        print("💾 Son rapor kaydediliyor...")
        excel_raporunu_gonder()
        break
    except Exception as e:
        print(f"❌ HATA: {str(e)[:100]}")
        time.sleep(10)
        continue
