# 🗣️ TUM Voice Application Assistant (Frontend)

This is the frontend of the **TUM Application Voice Assistant**, a Progressive Web App (PWA) that helps prospective students explore TUM study programs using voice interaction. The app is mobile-first and designed to be accessible, including for visually impaired users.

🌐 **Live site**:  
👉 [https://voice-assistant-gilt.vercel.app/](https://voice-assistant-gilt.vercel.app/)

---

## 🚀 Features

- ✅ **Voice Input** (via Web Speech API)
- ✅ **Voice Output** (via Text-to-Speech)
- ✅ **LLM-powered** dynamic responses
- ✅ **Mobile-first** interface
- ✅ **PWA support** (installable on phones)
- ✅ **Accessibility friendly**

---

## 🛠️ Getting Started (Local Development)

### 1. Clone the repository

```bash
git clone https://github.com/your-username/your-repo-name.git
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
* [next-pwa](https://github.com/shadowwalker/next-pwa)
* [Web Speech API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API)

---

## 📁 Project Structure

```
frontend/
├── app/              # App Router pages & layouts
├── public/           # Static files, icons, manifest
├── styles/           # Global CSS (via Tailwind)
├── next.config.ts    # PWA + Next.js config
├── package.json
└── README.md
```

## 📦 Deployment

The project is deployed on **Vercel**. You can easily deploy it by connecting your GitHub repo to Vercel and setting the **root directory** to `frontend/`.
