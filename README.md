# MYS-YOLLUK-OTOMASYON

MYS "Yolluk Süreç Hazırlama" formunu Excel'den otomatik dolduran yerel otomasyon
(Aşama 1). Canlı gönderim varsayılan olarak kilitlidir.

## ÖNCE OKU

**[PROJECT_KNOWLEDGE_TREE.md](PROJECT_KNOWLEDGE_TREE.md)** — Projenin hafızası:
kodlama kuralları, dosya haritası, ana akış, güvenlik ilkeleri ve değişiklik günlüğü.
Kod değiştirmeden önce bu dosyayı oku.

Ek kaynaklar:
- `README-STAGE1.txt` — Aşama 1 akışı ve güvenli çalışma kuralları.
- `PROJECT_HANDOFF_AI.md` — Detaylı devir/tanı dokümanı (MYS alanları, Excel yapısı).
- `PROJECT_KNOWLEDGE_TREE.md` — Güncel durum + kodlama kuralı + changelog.

## Hızlı başlangıç

```powershell
python scripts\yolluk-controller.py     # Panel -> http://127.0.0.1:8765
python scripts\stage1-live-run.py --stop-before-submit   # Güvenli dry-run
python tests\test-assignment.py         # Birim testler
```

