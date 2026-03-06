<img width="512" height="256" alt="logo" src="https://github.com/user-attachments/assets/7f0a3a43-a6d9-47ad-bb7e-52f7d3c2f3d9" />

# Autodarts Connect Online

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)
[![Beta](https://img.shields.io/badge/Status-BETA-orange.svg?style=for-the-badge)](#)

[English version below]

---

## 🇩🇪 Deutsch

**Autodarts Connect Online** ist eine Home Assistant Integration, die eine Echtzeit-Verbindung zu deinem Autodarts-Board über die offizielle WebSocket-Cloud herstellt. Im Gegensatz zu lokalen Lösungen erlaubt diese Integration das Mitverfolgen von Online-Matches und Bot-Spielen in Echtzeit.

⚠️ **Wichtiger Hinweis:** Diese Integration befindet sich aktuell im **Beta-Stadium**. Sie funktioniert bereits sehr gut, aber es können bei speziellen Spielmodi noch unvorhergesehene Fehler auftreten.

### 🤖 Transparenzhinweis
Dieses Projekt wurde in der Basis mithilfe von **Künstlicher Intelligenz (Google Gemini)** entwickelt. Ziel war es, eine hochperformante, granulare und moderne Integration zu schaffen. Die Weiterentwicklung erfolgt gemeinschaftlich durch die Community.

### 🚀 Status & Kompatibilität
Die Integration verfügt über einen Failsafe-Mechanismus: Sollte ein ungetesteter Spielmodus gestartet werden, stürzt die Integration nicht ab, sondern liefert weiterhin die Basisdaten.

| Spielmodus | Status | Details |
| :--- | :--- | :--- |
| **X01** | ✅ Voll unterstützt | Restpunkte, Checkout-Guide, Turn-Stats. |
| **Cricket** | ✅ Voll unterstützt | Punkte und Marks (20-15 & Bull) pro Spieler als eigene Sensoren. |
| **Bull-off** | ✅ Voll unterstützt | Abstandsmessung zum Bull in mm. |
| **Bermuda** | ⚠️ Ungetestet | Basisdaten (Punkte) vorhanden. |
| **Shanghai** | ⚠️ Ungetestet | Basisdaten vorhanden. |
| **Gotcha** | ⚠️ Ungetestet | Basisdaten vorhanden. |

### ✨ Features
- **Echtzeit-Events:** Schickt `autodarts_throw` Events sofort beim Einschlag (perfekt für verzögerungsfreie Lichteffekte via Node-RED).
- **Maximale Granularität:** Jeder Dart (1, 2, 3) eines Turns und jeder Checkout-Vorschlag ist eine eigene Entität.
- **Multiplayer:** Feste Entitäten für bis zu 4 Spieler (Name, Score, Average, Cricket-Marks).
- **Geräte-Integration:** Vollständige Unterstützung von HA-Geräten und Bereichen (Areas).

### 🛠 Installation

Die Installation erfolgt am einfachsten über den [Home Assistant Community Store (HACS)](https://hacs.xyz/). Wenn du HACS eingerichtet hast, klicke einfach auf den folgenden Button (erfordert ein konfiguriertes My Home Assistant) oder füge das Repository manuell hinzu.

[![Öffne deine Home Assistant Instanz und zeige ein Repository im Home Assistant Community Store an.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=casef007&repository=HA-autodarts-connect-online&category=integration)

**Manuelle HACS Installation:**
1. HACS -> Integrationen -> Drei Punkte oben rechts -> **Benutzerdefinierte Repositories**.
2. URL `https://github.com/casef007/HA-autodarts-connect-online` hinzufügen, Kategorie: **Integration**.
3. Herunterladen und Home Assistant neu starten.

### ⚙️ Konfiguration

Nach der Installation und dem Neustart kannst du das Board ganz einfach über die Home Assistant Benutzeroberfläche einrichten. Klicke auf den folgenden Button oder navigiere manuell dorthin.

[![Füge die Integration zu deiner Home Assistant Instanz hinzu.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=autodarts_connect)

**Manuelle Konfiguration:**
Gehe zu **Einstellungen -> Geräte & Dienste -> Integration hinzufügen** und suche nach "Autodarts Connect Online".

### 🗺 Roadmap
- [ ] Kontakt zu Autodarts aufnehmen für eine eigene offizielle Client-ID/Credentials-Kombination (bis dahin nutzen wir als Brücke die öffentlich verfügbaren Zugangsdaten von [darts-caller](https://github.com/lbormann/darts-caller)).
- [ ] Spezifische Sensoren/UI-Werte für Bermuda & Shanghai.
- [ ] Erweiterte Statistiken (Doppelquote, First-9 Average).
- [ ] Binäre Sensoren für "Match Point" Erkennung.
- [ ] Langfristig: Steuerung des Darts-Callers (Volume/Mute).

### 🤝 Mitwirken & Maintenance
Hast du Lust, das Projekt aktiv mitzugestalten oder zu warten? Pull Requests (PRs) sind herzlich willkommen! Da die Basis KI-gestützt erstellt wurde, freuen wir uns besonders über erfahrene Python-Entwickler, die den Code verfeinern möchten.

### 🏆 Credits
Vielen Dank an **[lbormann/darts-caller](https://github.com/lbormann/darts-caller)** für die Vorarbeit. Als Übergangslösung greifen wir derzeit auf die dort öffentlich verfügbare Credentials-Schnittstelle zurück.

---

## 🇺🇸 English

**Autodarts Connect Online** is a Home Assistant integration that establishes a real-time connection to your Autodarts board via the official WebSocket cloud.

⚠️ **Important Note:** This integration is currently in **Beta**. It works very well, but unforeseen bugs may still occur, especially in untested game modes.

### 🤖 Transparency Note
This project was initially developed using **Artificial Intelligence (Google Gemini)**. The goal was to create a high-performance, granular, and modern integration. Future development is driven by the community.

### 🚀 Status & Compatibility
The integration includes a failsafe mechanism to ensure it remains stable even when encountering unknown or untested game modes.

| Game Mode | Status | Details |
| :--- | :--- | :--- |
| **X01** | ✅ Fully Supported | Remaining points, checkout guide, turn stats. |
| **Cricket** | ✅ Fully Supported | Points and Marks (20-15 & Bull) per player as individual sensors. |
| **Bull-off** | ✅ Fully Supported | Bull distance measurement in mm. |
| **Bermuda** | ⚠️ Untested | Basic points data available. |
| **Shanghai** | ⚠️ Untested | Basic data available. |
| **Gotcha** | ⚠️ Untested | Basic data available. |

### ✨ Features
- **Real-time Events:** Fires `autodarts_throw` events instantly upon impact (perfect for zero-latency lighting effects in Node-RED).
- **Maximum Granularity:** Each dart (1, 2, 3) of a turn and each checkout suggestion is a separate entity.
- **Multiplayer Support:** Dedicated entities for up to 4 players (Name, Score, Average, Marks).
- **Device Integration:** Full support for HA Devices and Areas.

### 🛠 Installation

Installation is easiest via the [Home Assistant Community Store (HACS)](https://hacs.xyz/). Once you have HACS set up, simply click the button below (requires My Home Assistant configured) or add the repository manually.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=casef007&repository=HA-autodarts-connect-online&category=integration)

**Manual HACS Installation:**
1. Go to HACS -> Integrations -> Three dots -> **Custom repositories**.
2. Add the URL `https://github.com/casef007/HA-autodarts-connect-online`, Category: **Integration**.
3. Download and restart Home Assistant.

### ⚙️ Configuration

After installing and restarting, you can easily configure your devices using the Integrations UI. Click the shortcut button below or navigate manually.

[![Add Integration to your Home Assistant instance.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=autodarts_connect)

**Manual Configuration:**
Add via **Settings -> Devices & Services -> Add Integration** and search for "Autodarts Connect Online".

### 🗺 Roadmap
- [ ] Contact Autodarts to acquire our own official Client-ID/Credentials combination (until then, we are bridging the gap using the publicly available credentials from [darts-caller](https://github.com/lbormann/darts-caller)).
- [ ] Add specific sensors for Bermuda/Shanghai modes.
- [ ] Implement more statistics (checkout percentage, first-9).
- [ ] Add binary sensors for "Match Point" detection.
- [ ] Long-term: Direct control for Darts-Caller (Mute/Volume).

### 🤝 Contributing & Maintenance
Interested in maintaining or shaping this project? Since the core is AI-assisted, we especially welcome experienced Python developers to refine the code or add new features. Pull Requests (PRs) are always welcome!

### 🏆 Credits
Special thanks to **[lbormann/darts-caller](https://github.com/lbormann/darts-caller)** for the pioneering work. As a temporary workaround, we are currently utilizing the publicly available credential interface from that project.
