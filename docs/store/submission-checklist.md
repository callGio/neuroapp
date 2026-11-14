# Microsoft Store submission checklist (Gyrafold)

Gyrafold goes into the Microsoft Store as a Progressive Web App (PWA) wrapped in a Windows package by PWABuilder. Everything stays free: an individual developer account costs nothing, and PWABuilder is free.

Steps marked **[Owner only]** need your identity, your accounts or your decisions. Nobody else (including Claude) can do them for you.

## Before you start

- [ ] The PWA changes (manifest, service worker, icons, privacy page) are deployed to https://gyrafold.com.
- [ ] https://gyrafold.com/privacy.html opens.
- [ ] https://gyrafold.com/manifest.webmanifest opens and shows the Gyrafold name and icons.
- [ ] In Edge or Chrome on a computer, https://gyrafold.com shows an install icon in the address bar, and "Install app" appears on the welcome page.

## 1. Create a developer account **[Owner only]**

1. Go to Partner Center (https://partner.microsoft.com/dashboard) and sign up for the Windows and Xbox developer program as an **individual**. Individual accounts are free.
2. Sign in with your personal Microsoft account.
3. Complete identity verification (Microsoft asks for a government-issued ID). This can take a few days.

## 2. Reserve the name **[Owner only]**

1. In Partner Center: Apps and games > New product > MSIX or PWA app.
2. Reserve the name **Gyrafold**.

## 3. Copy the three identity values **[Owner only]**

In Partner Center, open the app > Product management > Product identity. Copy these three values exactly:

- **Package/Identity/Name**
- **Package/Identity/Publisher** (starts with `CN=`)
- **Package/Properties/PublisherDisplayName**

## 4. Make the Windows package with PWABuilder **[Owner only]**

1. Go to https://www.pwabuilder.com and enter `https://gyrafold.com`.
2. Review the report. The manifest, service worker and icons should pass. Fix anything marked as required before continuing.
3. Choose Package for stores > Windows.
4. Paste the three identity values from step 3. Keep the app name **Gyrafold**. Set the version (for example `1.0.0`).
5. Download the package and follow the upload instructions included in it (it contains the bundle files to upload to Partner Center).

## 5. Upload and fill in the submission **[Owner only]**

In Partner Center, start a submission for Gyrafold:

1. **Pricing and availability:** Free. Choose markets (all is fine).
2. **Properties:** Category **Education**. Answer the product declarations honestly (no ads, no purchases).
3. **Age ratings:** complete the IARC questionnaire using the notes in `listing.md` (no user-generated content, no purchases, no ads, anatomical and medical education content).
4. **Packages:** upload the files from PWABuilder.
5. **Store listings (English):** copy the name, short description, description, features, keywords and "what's new" from `listing.md`. Upload the six 1920x1080 screenshots from `docs/store/screenshots/` in the order listed there. Add the line "Educational use only; not medical advice." if it is not already in the description.
6. **Privacy policy URL:** `https://gyrafold.com/privacy.html`
7. **Website:** `https://gyrafold.com`
8. **Support contact:** use the contact page, `https://giovannicallahan.github.io/contact.html` (do not paste a personal email address into the public listing unless you want it public).

## 6. Submit **[Owner only]**

1. Submit for certification. Review usually takes a few business days.
2. If it is rejected, read the report, fix, and resubmit.

## After it is live

- The Store app loads https://gyrafold.com, so normal deploys update it. You only need a new package when the manifest identity, name or icons change.
- When you deploy changes to the pages, content JSON, icons, fonts or three.js, bump `VERSION` at the top of `viewer/public/sw.js` so installed copies pick up the new files. Bump `MODELS_CACHE` (in both `sw.js` and `atlas-viewer.html`) only if the `.glb` model files change.
