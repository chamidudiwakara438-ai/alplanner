# Firebase එක යොදන හැටි (free)

Netlify = website. Firebase = accounts + progress (හැම phone/PC එකකින්ම එකම login).

Credit card ඕන නැහැ. **Spark (free)** plan එක ඇති.

## 1) Project එක

1. https://console.firebase.google.com → **Add project**
2. Name: `al-planner` → Continue → Google Analytics **off** කරන්න පුළුවන් → Create
3. ඉවර උනාම project එක open කරන්න

## 2) Authentication

1. Left menu **Build → Authentication → Get started**
2. **Sign-in method** → **Email/Password** → Enable → Save

## 3) Firestore

1. **Build → Firestore Database → Create database**
2. **Start in test mode** (පස්සේ rules දානවා) → location: `asia-south1` (Mumbai) හෝ nearest → Enable
3. **Rules** tab එකට `public/firebase/firestore.rules` ගොනුවේ තියෙන හැම එකම paste කරලා **Publish**

## 4) Web app keys

1. Project **Settings** (gear) → **Your apps** → `</>` Web
2. App nickname: `alplanner-web` → Register (Hosting tick කරන්න එපා)
3. පේන `firebaseConfig` object එක copy කරන්න

## 5) Keys site එකට දාන්න

`public/js/firebase-config.js` open කරලා හිස් තැන් fill කරන්න:

```js
window.FIREBASE_CONFIG = {
  apiKey: 'AIza...',
  authDomain: 'al-planner-xxxx.firebaseapp.com',
  projectId: 'al-planner-xxxx',
  storageBucket: 'al-planner-xxxx.appspot.com',
  messagingSenderId: '123456',
  appId: '1:123:web:abc',
  adminEmail: 'oyage@gmail.com',   // මේ email එක admin
};
```

`adminEmail` එකට **ඔයා register වෙන Gmail** එක දාන්න.

## 6) Netlify එකට

`public` folder එක zip කරලා https://app.netlify.com/drop වලට දාන්න.

Footer එකේ green **Firebase** pill එකක් පේන්න ඕන. ඒක **This browser** නම් keys හිස්.

## Authorized domains

Firebase → Authentication → Settings → **Authorized domains**

- `localhost`
- ඔයාගේ `something.netlify.app` domain එකත් Add කරන්න (බොහෝ විට auto එකතු වෙනවා)
