# 🗣️ TUM Voice Application Assistant (Frontend)

This is the frontend of the **TUM Application Voice Assistant**, a Progressive Web App (PWA) that helps prospective students explore TUM study programs using voice interaction. The app is mobile-first and designed to be accessible, including for visually impaired users.

🌐 **Live site**:  
👉 [https://voice-assistant-gilt.vercel.app/](https://voice-assistant-gilt.vercel.app/)

---

## 🚀 Features

- ✅ **Voice Input** (via Web Speech API, with animated overlay and volume visualization)
- ✅ **Voice Output** (Text-to-Speech for assistant replies)
- ✅ **LLM-powered** dynamic responses (mocked for now)
- ✅ **Mobile-first** interface
- ✅ **PWA support** (installable on phones)
- ✅ **Accessibility friendly**
- ✅ **Multi-language support** (i18n with JSON backend, FAQ auto-switches language)
- ✅ **FAQ Suggestions** (shows clickable FAQ when chat is empty, supports multi-language)
- ✅ **Chat Interface** (user/assistant bubbles, typewriter effect for assistant, scroll-to-bottom button)
- ✅ **File/Image Upload** (with preview)
- ✅ **Sidebar with other information**

---

## 🛠️ Getting Started (Local Development)

### 1. Clone the repository

```bash
git clone https://github.com/tsaichen1o/voiceAssistant.git
cd frontend
```

### 2. Install dependencies

```bash
yarn install
```

### 3. Start the development server

```bash
yarn dev
```

Visit `http://localhost:3000` in your browser.

---

## 🧱 Built With

* [Next.js 15](https://nextjs.org/)
* [Tailwind CSS](https://tailwindcss.com/)
* [react-i18next](https://react.i18next.com/) + [i18next-http-backend](https://github.com/i18next/i18next-http-backend)
* [next-pwa](https://github.com/shadowwalker/next-pwa)
* [Web Speech API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API)
* [uuid](https://www.npmjs.com/package/uuid)

---

## 📁 Project Structure

```
frontend
├── app
│   ├── layout.tsx
│   ├── page.tsx     # Landing page
│   ├── login
│   │    └── page.tsx
│   └── chat
│       ├── layout.tsx
│       └── [userId]
│           └── [chatSessionId]
│               └── page.tsx
├── components
│   ├── LandingPage.tsx
│   ├── ChatSidebar.tsx
│   ├── ChatInterface.tsx
│   ├── ChatInput.tsx
│   ├── ChatMessagesList.tsx
│   ├── ChatMessage.tsx
│   ├── TypewriterText.tsx
│   ├── VoiceAssistantOverlay.tsx
├── locales
│   └── en/translation.json
│   └── zh/translation.json
├── hooks
│   └── useMicrophoneVolume.ts
├── types
│   └── chat.ts
├── i18n.ts
├── public
│   ├── logo.png
│   └── icons/
└── styles
    └── globals.css
```

---

## 📦 Deployment

The project is deployed on **Vercel**. You can easily deploy it by connecting your GitHub repo to Vercel and setting the **root directory** to `frontend/`.

---

## 🌍 Multi-language (i18n)
- All FAQ and UI strings are managed via JSON files in `public/locales/{lang}/translation.json`.
- Language switching is supported via i18next.

---

## 💡 Notable UI/UX Features
- **FAQ Suggestions**: When chat is empty, clickable FAQ suggestions are shown (auto-translated).
- **Voice Overlay**: Animated, volume-reactive overlay for voice input, with pause/close controls.
- **Typewriter Effect**: Assistant replies are animated character-by-character.
- **Scroll to Bottom**: Button appears when chat is not at the bottom.
- **Responsive Design**: Works great on mobile and desktop.

---

## 📝 License
MIT
