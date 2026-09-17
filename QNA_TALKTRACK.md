# VoxGuard — Judge Q&A Talk Track

This document contains prepared answers for the hardest questions judges will likely ask during the SIH assessment. They are grounded in our actual current architecture. 

**Memorize the "Ideal Answer", avoid the "Do Not Say" traps, and be ready for the "Likely Follow-up".**

---

### 1. "How does this scale to thousands of concurrent calls?"

**Ideal Answer:**
"Right now, this prototype runs on a single FastAPI instance where ML inference uses a thread-lock to prevent race conditions, meaning it processes one chunk at a time globally. To scale to thousands of concurrent calls in production, we would decouple the WebSocket ingestion from the ML engine using a message queue like Kafka or Redis Pub/Sub, and feed the audio chunks into a horizontally auto-scaling Triton Inference cluster. The WebSockets just handle routing while the ML cluster scales independently."

**Do Not Say:** "It already scales infinitely," or "FastAPI handles the scaling automatically."
**Likely Follow-up:** "What happens if the ML cluster is overloaded?" *(Answer: "The rolling risk average is resilient to missing chunks, so we could selectively drop chunks during extreme traffic spikes without completely failing to detect fraud.")*

---

### 2. "How would this actually plug into a real bank's phone system?"

**Ideal Answer:**
"For the demo, we are streaming from a browser microphone via WebSockets. However, banks use SIP trunks and PBX systems like Cisco or Asterisk, not browser mics. In our Phase 2 deployment, VoxGuard would act as a SIP REC (SIP Recording) endpoint, or integrate via Twilio Media Streams to receive G.711 packets directly from the telco network. The core streaming architecture remains exactly the same; we just swap the browser WebSocket client for a Twilio/SIP client."

**Do Not Say:** "We will build a mobile app for the bankers to use," or "We will run this on the banker's laptop."
**Likely Follow-up:** "Can your model handle 8kHz compressed telecom audio?" *(Answer: "Yes, our preprocessing layer resamples and normalizes the audio, but we plan to explicitly fine-tune Spectra-AASIST3 on G.711 compressed data to prevent accuracy degradation.")*

---

### 3. "Why does this need blockchain?"

**Ideal Answer:**
"Voice cloning attacks often target high-value transactions, like a 5 Crore wire transfer. If our system flags a call as high-risk but a banker overrides it, or if there's an RBI audit later, we need absolute non-repudiation. By anchoring a cryptographic hash of the JSON audit log to a Sepolia Ethereum smart contract, the bank can mathematically prove exactly when the fraud was detected and what the risk score was, completely preventing any internal log tampering."

**Do Not Say:** "Because the theme said Blockchain," or "We store the audio on the blockchain." (We never store audio on-chain for privacy reasons).
**Likely Follow-up:** "Isn't Ethereum too slow for real-time?" *(Answer: "Yes, which is why the blockchain anchoring happens asynchronously in the background. The actual transaction block and alerting happen instantly via WebSockets; the blockchain just acts as the permanent immutable ledger afterward.")*

---

### 4. "What if the attacker adds static or background noise?"

**Ideal Answer:**
"SOTA spectral models can struggle if adversarial noise is added. This is why we use a multi-modal approach. Even if the noise fools the spectral artifact detector, the attacker still has to spoof the prosody (pitch and jitter) perfectly, AND they have to match the original speaker's embedding. Our Identity Drift tracker will still trigger a high risk score if the voice signature changes mid-call, regardless of background noise."

**Do Not Say:** "Our AI is too smart to be fooled by noise."
**Likely Follow-up:** "Does the noise suppression layer remove the deepfake artifacts?" *(Answer: "That is a known trade-off. Aggressive denoising can smooth out synthetic artifacts. We process the raw audio for the spectral model first, before applying any noise gates for the prosody analysis.")*

---

### 5. "Does it work on Indian languages and accents?"

**Ideal Answer:**
"Yes. Deepfake detection isn't just about the words spoken, it's about the acoustic artifacts introduced by the vocoder during synthesis. However, to prove this empirically, we've built a Transparency Page in our dashboard that tracks our accuracy against regional accents (like Hindi or Gujarati-accented English). We run automated smoke tests against these datasets to ensure our model doesn't falsely flag genuine regional speakers as anomalous."

**Do Not Say:** "Yes, it works perfectly on all languages."
**Likely Follow-up:** "Can you show me the data for that?" *(Answer: "Yes, we have our `accent_eval_results.md` generated from our custom dataset, which you can see right here...")*

---

### 6. "What if you encounter an unseen cloning model (like a brand new ElevenLabs update)?"

**Ideal Answer:**
"Zero-day TTS models are the hardest challenge in this space because they don't have the exact same artifacts as ASVspoof 2019 data. But again, our defense is layered. Even if a zero-day model passes the Spectra-AASIST3 check, it's incredibly difficult for an attacker to spoof the exact pitch variance (Prosody) AND dynamically clone the exact voice embedding in real-time (Identity Drift). A failure in one layer doesn't compromise the whole system."

**Do Not Say:** "Our model detects everything."
**Likely Follow-up:** "How do you plan to keep the spectral model updated?" *(Answer: "We will adopt a continuous learning pipeline where flagged audio that led to confirmed fraud is periodically added to our fine-tuning dataset.")*
