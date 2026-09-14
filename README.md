# SOFA — Safe One For All

Local AI chatbox for everything, you need to create image, create music, chat or do anything safely when talking to AI? You don't need to search thousands of websites to find the best AI versions, SOFA has you covered; you can do everything with this AI and it's fully local so no cloud saving will happen.

## Nedir?

SOFA, tamamen yerel-öncelikli (local-first) ve gizlilik odaklı bir çok işlevli AI yardımcı uygulamasıdır. Sohbet, görsel üretimi ve filigran temizleme gibi araçları tek bir arayüzde birleştirir; içerikleriniz varsayılan olarak diske veya bulutta hiçbir yere loglanmaz.

## Kullanılan LLM Altyapısı

SOFA, ücretsiz API'ler için tek tek sağlayıcı hesabı açmanızı gerektirmez. Bunun yerine, yerelde çalışan **OpenAI-uyumlu ağ geçitlerini (gateway)** kullanır:

- **[OmniRoute](https://github.com/diegosouzapw/OmniRoute)** — zero-config, kurulum sonrası anahtar gerekmeden 290+ sağlayıcıya erişim sağlar. Varsayılan uç: `http://localhost:20128/v1`
- **[FreeLLMAPI](https://github.com/tashfeenahmed/freellmapi)** — 34+ ücretsiz LLM sağlayıcısını tek bir `/v1` ucunda birleştirir. Varsayılan uç: `http://localhost:3001/v1`

Hangisinin kullanılacağı `.env` dosyasındaki `CHAT_PROVIDER` (`omniroute` veya `freellmapi`) ile seçilir; her iki servis de OpenAI'nin `/chat/completions` ve `/images/generations` formatını kullandığı için SOFA'nın backend'i tek bir generic istemci ile her ikisiyle de konuşabilir.

## Klasör Yapısı

```
SOFA-Safe-One-For-All-/
├── README.md
├── .env.example
├── .gitignore
├── requirements.txt
├── app/
│   ├── main.py                  # FastAPI giriş noktası
│   ├── config.py                # .env tabanlı merkezi ayarlar
│   ├── utils/
│   │   └── logger.py            # gizlilik-öncelikli logger
│   └── modules/
│       ├── chat/                # Sohbet & Asistan modülü
│       │   ├── schemas.py
│       │   ├── service.py       # OmniRoute / FreeLLMAPI istemcisi
│       │   └── router.py
│       ├── media/                # Medya üretimi & işleme modülü
│       │   ├── schemas.py
│       │   ├── service.py       # görsel üretimi + filigran temizleme taslağı
│       │   └── router.py
│       └── privacy/              # Güvenli yerel araçlar modülü
│           ├── schemas.py
│           ├── service.py       # geçici dosya temizleme, durum raporu
│           └── router.py
├── static/
│   ├── css/style.css
│   ├── js/splash.js              # giriş animasyonu kontrolcüsü
│   └── js/app.js                 # sekme + API entegrasyonu
└── templates/
    └── index.html                 # giriş ekranı + uygulama kabuğu
```

## Kurulum

1. **Bir LLM ağ geçidi kurun** (en az birini):
   ```bash
   # OmniRoute (önerilen, zero-config)
   npm install -g omniroute
   omniroute

   # veya FreeLLMAPI
   curl -fsSL https://freellmapi.co/install.sh | bash
   ```

2. **Python bağımlılıklarını kurun:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Ortam değişkenlerini ayarlayın:**
   ```bash
   cp .env.example .env
   # Gerekirse CHAT_PROVIDER, base URL ve anahtarları düzenleyin.
   ```

4. **Uygulamayı çalıştırın:**
   ```bash
   uvicorn app.main:app --reload
   ```
   Tarayıcıdan `http://127.0.0.1:8000` adresini açın.

## Gizlilik

- `SOFA_NO_LOG=true` (varsayılan) iken hiçbir sohbet/medya içeriği diske veya konsola yazılmaz.
- "Gizlilik" sekmesinden tek tıkla tüm yerel geçici dosyalar silinebilir.
- Hiçbir veri, kullanıcının açıkça yapılandırdığı yerel ağ geçidi dışında bir yere gönderilmez.
