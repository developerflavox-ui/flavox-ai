# FLAVOX AI Video Enhancer — Website + AI backend starter

এটি ওয়েবসাইট এবং Android অ্যাপ বানানোর জন্য starter project। Backend FFmpeg দিয়ে resize, denoise, sharpen এবং frame-rate conversion করে।

## সতর্কতা
এখনো প্রকৃত AI super-resolution model bundled নয়। Real-ESRGAN/অন্য video super-resolution model যুক্ত করতে আলাদা model weights, inference pipeline এবং GPU/CPU capacity লাগবে। 4× resize মানেই আসল 4K detail পুনরুদ্ধার নয়।

## দরকার
- Python 3.10+
- FFmpeg এবং ffprobe PATH-এ
- Node.js 20+, npm
- Android APK বানাতে Android Studio + Android SDK

## Backend চালানো
```bash
cd backend
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS:
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000
```

## Website চালানো
অন্য terminal:
```bash
cd web
npm install
cp .env.example .env
npm run dev -- --host 0.0.0.0
```

## Android project/APK
```bash
cd web
npm install
npm run build
npx cap add android
npx cap sync android
npx cap open android
```
Android Studio-তে Build > Build Bundle(s) / APK(s) > Build APK(s)।

`android/` folder প্রথম `npx cap add android` চালালে তৈরি হবে। ZIP-এ prebuilt APK নেই।

## অনলাইনে প্রকাশ
Backend-টি HTTPS-সহ GPU-capable hosting-এ deploy করে `web/.env`-এর `VITE_API_BASE`-এ public API URL দিতে হবে। তারপর `npm run build` করে `dist/` folder static hosting-এ deploy করুন। HTTPS ব্যবহার করুন; localhost production URL নয়।

## API
- `GET /health`
- `POST /api/enhance` multipart: `file`, `scale` (1/2/4), `sharpen`, `denoise`, `fps` (0/30/60)
