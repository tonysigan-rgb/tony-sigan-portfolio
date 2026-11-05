# pluffy minis — phone app (iPhone + Android)

One Expo app for both phones. The app is a shell: every screen comes from the website on GitHub Pages
(`app.html` = All Series + series pages, `drama.html` = episode player, `teaser.html` = teaser player,
`pluffy-data.js` = episodes and Monday release dates, all in the tony-sigan-portfolio repo).

**To change the design, edit those files on GitHub.** The app shows the new version the next time it
opens (or pull down to refresh). No app download or store update is needed for design changes.

## Try it on your phone (Windows PowerShell)

```powershell
cd mobile
npm install
npx expo start
```

Install **Expo Go** on your phone, connect it to the same Wi-Fi as your computer, then scan the QR code
(iPhone: Camera app · Android: Expo Go). If your Wi-Fi blocks it, run `npx expo start --tunnel` instead.

## Later: put it on the App Store / Google Play

Use EAS Build (`npx eas-cli build`). You'll need an Apple Developer account (iPhone) and a Google Play
developer account (Android). App IDs are already set to `com.tonysigan.pluffyminis` in `app.json`.
