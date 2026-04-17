# OpenStudio Prompt Gallery

Tested prompts for use with Claude Code, Cursor, Copilot, or any supported AI assistant.

---

## 🆓 Zero API Keys Required

### Animated Explainer (free)
```
"Make a 45-second animated explainer about how blockchain works, 
 using stock images and offline narration"
```
- Pipeline: animated_explainer
- Assets: Pexels stock + Piper TTS
- Cost: $0.00

---

## 🔑 With Muapi Key (~$0.50–$2)

### Product Ad
```
"Create a 30-second product launch video for a fictional AI writing tool 
 called 'Quill'. Generate a logo, hero shots, and compose with upbeat music."
```
- Pipeline: animated_explainer + bridge generate_image
- Assets: FLUX images + Piper TTS + stock music
- Estimated cost: ~$0.30

### Talking Head (OpenStudio Exclusive)
```
"Take portrait.jpg and this script: [paste script].
 Generate a professional talking head video with lip sync."
```
- Pipeline: lipsync_presenter ✨ (OpenStudio original)
- Assets: LTX 2.3 Lipsync + Remotion composition
- Estimated cost: ~$0.10–$0.20 per minute

### Social Media Clip
```
"Take this 3-minute explainer script about solar panels and turn it 
 into 3 TikTok-ready vertical clips with AI visuals and subtitles"
```
- Pipeline: clip_factory
- Assets: FLUX images + Piper TTS + Remotion captions
- Estimated cost: ~$0.50

---

## 💎 Full Setup (~$1–$5)

### Cinematic Brand Trailer
```
"Create a 30-second cinematic trailer for an architecture firm called 
 'Form & Light Studio'. Use AI-generated building renders, dramatic orchestral 
 music, and a professional voiceover. Export for LinkedIn."
```
- Pipeline: cinematic
- Assets: Kling v3 video + ElevenLabs TTS + Suno music
- Estimated cost: ~$2–$3

### Multi-Language Product Video
```
"Create a 60-second product explainer in English, then dub it into 
 Spanish and French with matching subtitles."
```
- Pipeline: animated_explainer → localization_dub
- Assets: FLUX images + Google TTS (700+ voices)
- Estimated cost: ~$1–$2

### AI Influencer Presenter (OpenStudio Exclusive)
```
"Generate a consistent AI presenter character using this reference photo, 
 write a 90-second script about AI trends, and produce a talking head video 
 with lip sync ready for YouTube."
```
- Pipeline: lipsync_presenter ✨
- Assets: Nano Banana 2 Edit (multi-image) + LTX lipsync + Remotion
- Estimated cost: ~$0.50–$1.00

### Podcast Repurpose
```
"Take this podcast transcript [paste text] and create 5 short social clips 
 with audiogram-style visuals, captions, and the speaker's portrait animated 
 with lip sync."
```
- Pipeline: podcast_repurpose + lipsync_presenter
- Assets: Infinite Talk lipsync + Remotion captions
- Estimated cost: ~$0.50

---

## 💡 Tips

- Always start with `model="auto"` — the router picks the best available model
- Use `style="budget"` in your prompt if cost matters more than quality
- The lipsync pipeline works best with a clean, well-lit portrait photo
- For consistent AI characters across scenes, provide reference images via multi-image models (Nano Banana 2 Edit supports up to 14)
