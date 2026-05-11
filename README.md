# Konut Fiyat Analizi Otomasyonu

Bu proje, secilen 3 sehir icin konut verisini toplar/dogrular, istatistiksel analizleri calistirir ve rapor ciktilarini otomatik uretir.
Arayuz `Streamlit` uzerinden calisir; rapor ciktilari Excel ve Word formatinda uretilir.

## Ozellikler

- 3 farkli sehir secimi ve dogrulama
- Excel ile toplu veri yukleme (`data/templates/input_template.xlsx`)
- Form uzerinden manuel satir girisi
- Otomatik veri dogrulama (zorunlu alanlar + min 30 kayit/sehir)
- Istatistik analizleri ve grafik uretimi
- Excel paket cikti ve Word rapor olusturma

## Gereksinimler

- Python 3.10+ (onerilen)
- Windows (exe/setup paketleme adimlari icin)

Kurulum:

```bash
python -m pip install -r requirements.txt
```

## Uygulamayi Calistirma

Gelistirme modunda:

```bash
python -m streamlit run app.py
```

Alternatif:

```bash
python launcher.py
```

Uygulama varsayilan olarak `http://localhost:8501` adresinde acilir.

## Kullanim Akisi

1. 3 farkli sehri secip onaylayin.
2. Veriyi Excel ile yukleyin veya manuel satir ekleyin.
3. Veri onizleme ve kayit sayilarini kontrol edin.
4. Analizi calistirin.
5. Excel/Word ciktilarini indirin.

## Hizli Test (Smoke Test)

```bash
python smoke_test.py
```

Bu komut sahte veri ile tum analiz ve rapor hattini uctan uca test eder.

## Paketleme (Windows)

### EXE olusturma

```powershell
.\build_exe.ps1
```

Uretilen dosya:

```text
dist/StatisticApp.exe
```

### Setup olusturma

```powershell
.\build_setup.ps1
```

Uretilen dosya:

```text
installer-dist/StatisticApp-Setup.exe
```

## Proje Yapisi

```text
Statistic/
|-- app.py
|-- launcher.py
|-- smoke_test.py
|-- requirements.txt
|-- data/
|   |-- city_assignments.csv
|   `-- templates/
|       `-- input_template.xlsx
`-- src/
    |-- analysis/
    |-- reporting/
    |-- validation.py
    `-- data_ingestion.py
```

## GitHub icin Not

Depoya sadece kaynak kodu ve gerekli temel dosyalar eklenmelidir. Uretilen ciktilar ve yerel dokumanlar `.gitignore` ile dislanmistir.
