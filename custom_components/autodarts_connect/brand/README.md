# Brand Images (Logos & Icons)

## 🇩🇪 Deutsch
Dieser Ordner enthält die lokalen Logos und Icons für die Darstellung der **Autodarts Connect Online** Integration in der Home Assistant Benutzeroberfläche.

**Warum existiert dieser Ordner?**
Seit dem Home Assistant Update **2026.3** können Custom Integrations ihre eigenen Markenbilder direkt im Integrationsverzeichnis mitliefern. Zuvor war es notwendig, diese Bilder mühsam in einem separaten, zentralen Home Assistant GitHub-Repository einzureichen. Home Assistant erkennt diesen Ordner nun automatisch, lädt die Bilder über die lokale API und speichert sie zwischen (Cache), sodass sie auch bei Internetausfällen im Dashboard sichtbar bleiben.

**Unterstützte Dateinamen in diesem Ordner:**
- `icon.png` / `dark_icon.png` (Quadratisches Icon für Listen und Geräte)
- `logo.png` / `dark_logo.png` (Breites Banner für die Integrations-Detailseite)
- `icon@2x.png` / `dark_icon@2x.png` (Hochauflösende Varianten)
- `logo@2x.png` / `dark_logo@2x.png`

---

## 🇺🇸 English
This folder contains the local logos and icons used to display the **Autodarts Connect Online** integration within the Home Assistant UI.

**Why does this folder exist?**
Starting with Home Assistant **2026.3**, custom integrations can ship their own brand images directly inside the integration directory. Previously, developers had to submit these images via PR to a separate, central Home Assistant GitHub repository. Home Assistant now automatically detects this folder, proxies the images through its local API, and caches them so they remain available even during internet outages.

**Supported filenames in this folder:**
- `icon.png` / `dark_icon.png` (Square icon for lists and devices)
- `logo.png` / `dark_logo.png` (Wide banner for the integration detail page)
- `icon@2x.png` / `dark_icon@2x.png` (High-resolution variants)
- `logo@2x.png` / `dark_logo@2x.png`
