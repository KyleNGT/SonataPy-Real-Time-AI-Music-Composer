import { GoogleGenAI } from 'https://esm.run/@google/genai';

// Initialize Google GenAI client
// The API key is never committed; it is asked for once and kept in sessionStorage
let apiKey = sessionStorage.getItem('GEMINI_API_KEY');
if (!apiKey) {
    apiKey = window.prompt('Enter your Google AI (Gemini) API key:') || '';
    if (apiKey) sessionStorage.setItem('GEMINI_API_KEY', apiKey);
}
const client = new GoogleGenAI({
    apiKey,
    apiVersion: "v1alpha",
});

// Constants
const SAMPLE_RATE = 44100;
const MODEL_NAME = "models/lyria-realtime-exp";

// Application State
const state = {
    activeConfig: {},
    activePrompts: [],
    isPlaying: false,
}

// Audio and Session State
let session = null;
let audioContext = null;
let audioGainNode = null;
let audioQueueTime = 0;
let pendingVolume = 0.8;
let isConnecting = false;

// UI Elements
const slidersList = document.getElementById('sliders-list');
const promptInputField = document.getElementById('promptInput');
const addSliderBtn = document.getElementById('addSliderBtn');
const clearBtn = document.getElementById('clearBtn');
const playBtn = document.getElementById('playBtn');
const stopBtn = document.getElementById('stopBtn');
const bpmRange = document.getElementById('bpmRange');
const bpmValue = document.getElementById('bpmValue');
const autoBpmCheckbox = document.getElementById('autoBpmCheckbox');
const scaleSelect = document.getElementById('scaleSelect');
const muteBass = document.getElementById('bassCheckbox');
const muteDrums = document.getElementById('drumsCheckbox');
const logEl = document.getElementById('log');
const logEntries = [];
const sidebar = document.getElementById('sidebar');
const toggleSidebarBtn = document.getElementById('toggleSidebar');
const generatedCodeEl = document.getElementById('generatedCode');


// Sidebar toggle logic
if (sidebar && toggleSidebarBtn) {
    const syncSidebarIcon = () => {
        const icon = toggleSidebarBtn.querySelector('i');
        if (icon) {
            icon.className = sidebar.classList.contains('collapsed') ? 'fa fa-chevron-right' : 'fa fa-chevron-left';
        }
    };
    if (localStorage.getItem('sidebarCollapsed') === 'true') {
        sidebar.classList.add('collapsed');
    }
    toggleSidebarBtn.addEventListener('click', () => {
        sidebar.classList.toggle('collapsed');
        syncSidebarIcon();
        localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
    });
    syncSidebarIcon();
}
function debounce(func, delay) {
    let timeoutId;
    return function(...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => {
            func(...args);
        }, delay);
    };
}

function buildCodeString() {
    let code = "";

    // Get BPM
    if (autoBpmCheckbox.checked) {
        code += `bpm 120;\n`; // Send a default, but API will ignore if 'auto' is set
    } else {
        code += `bpm ${bpmRange.value};\n`;
    }

    // Get Density
    const density = document.querySelector('input[name="densityRadio"]:checked').value;
    code += `density ${density};\n`; 

    // Get Brightness
    const brightness = document.querySelector('input[name="brightnessRadio"]:checked').value;
    code += `brightness ${brightness};\n`; 

    // Get Mute flags
    code += `mute_drums ${muteDrums.checked};\n`; 
    code += `mute_bass ${muteBass.checked};\n`;  

    // Get Scale
    const scale = scaleSelect.value;
    if (scale === "SCALE_UNSPECIFIED") {
        code += `scale "auto";\n`;
    } else {
        code += `scale "${scale}";\n`; // e.g., scale "C_MAJOR_A_MINOR";
    }

    // Get Prompts from sliders
    const promptParts = [];
    const sliderRows = slidersList.querySelectorAll('.slider-row');
    sliderRows.forEach(row => {
        const labelEl = row.querySelector('label.form-label');
        const rangeEl = row.querySelector('input[type="range"]');
        if (labelEl && rangeEl) {
            const text = labelEl.textContent.trim();
            const weight = rangeEl.value;
            promptParts.push(`${text}:${weight}`);
        }
    });

    if (promptParts.length > 0) {
        code += `compose "${promptParts.join(',')}";\n`; // compose "Piano:1.5,Drums:1.0";
    } else {
        code += `compose "";\n`; 
    }
    code += "play;\n";

    if (generatedCodeEl) {
        generatedCodeEl.textContent = code;
    }

    return code;
}
async function runInterpreter(code) {
    try {
        const response = await fetch('http://localhost:8000/interpret', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ code: code }),
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Interpreter request failed');
        }

        const result = await response.json();
        return result; 
    
    } catch (error) {
        console.error('Interpreter Error:', error);
        appendLog(`Interpreter Error: ${error.message}`, 'error');
        return null;
    }
}

async function applySettingsToSession() {
    if (!session || !state.isPlaying) {
        return;
    }
    const code = buildCodeString();
    appendLog(`Sending to interpreter...`);
    console.log("Sending code:\n", code);

    // Run the interpreter
    const result = await runInterpreter(code);
    if (!result) {
        appendLog('Failed to get settings from interpreter.', 'error');
        return;
    }

    const { config, prompts } = result;

    const configChanged = JSON.stringify(config) !== JSON.stringify(state.activeConfig);
    const promptsChanged = JSON.stringify(prompts) !== JSON.stringify(state.activePrompts);

    if (!configChanged && !promptsChanged) {
        return;
    }
    
    state.activeConfig = config;
    state.activePrompts = prompts;

    console.log("Received Config:", config);
    console.log("Received Prompts:", prompts);

    try {
        if (promptsChanged) {
            if (prompts.length > 0) {
                await session.setWeightedPrompts({ weightedPrompts: prompts });
                appendLog(`Sent ${prompts.length} prompt(s) to session.`);
            } else {
                appendLog(`No prompts to send.`);
            }
        }
        
        if (configChanged) {
            await session.setMusicGenerationConfig({ musicGenerationConfig: config });
            appendLog('Generation config updated from interpreter.');
        }

    } catch (error) {
        appendLog(`Failed to apply settings: ${error.message}`, 'error');
    }
}

// Create a debounced version for live updates
const debouncedApplySettings = debounce(applySettingsToSession, 500);

// Play/Pause button logic
playBtn.addEventListener('click', () => {
    if (playBtn.disabled) return;
    
    if (state.isPlaying === false) {
        btnToPauseState();
        void handlePlay(); // Call the async play handler
    }

    if (state.isPlaying === true) {
        playBtn.disabled = true;
        btnToPlayState();
        void handlePause().finally(() => {
            playBtn.disabled = false;
        });
    }
});

function btnToPlayState() {
  playBtn.innerHTML = '<i class="fa fa-play"></i>';
  playBtn.classList.remove('btn-danger');
  playBtn.classList.add('btn-success');
}

function btnToPauseState() {
    playBtn.innerHTML = '<i class="fa fa-pause"></i>';
    playBtn.classList.remove('btn-success');
    playBtn.classList.add('btn-danger');
}

// Stop button logic
stopBtn.addEventListener('click', () => {
    void handleStop();
});

// Listen for config changes
document.querySelectorAll('input[name="densityRadio"]').forEach(radio => {
    radio.addEventListener('change', debouncedApplySettings);
});
document.querySelectorAll('input[name="brightnessRadio"]').forEach(radio => {
    radio.addEventListener('change', debouncedApplySettings);
});
muteBass.addEventListener('change', debouncedApplySettings);
muteDrums.addEventListener('change', debouncedApplySettings);
scaleSelect.addEventListener('change', debouncedApplySettings);
autoBpmCheckbox.addEventListener('change', () => {
    bpmRange.disabled = autoBpmCheckbox.checked;
    debouncedApplySettings();
});
bpmRange.addEventListener('input', () => {
    bpmValue.textContent = bpmRange.value;
    debouncedApplySettings();
});


// Play button handler
async function handlePlay() {
    if (isConnecting) return;
    await ensureAudioReady();

    // Create session if not exists
    if (!session) {
        console.log('Connecting to generation session...');
        isConnecting = true;
        
        if (slidersList.children.length === 0) {
            appendLog('No prompts defined. Please add at least one prompt slider before playing.', 'warn');
            isConnecting = false;
            btnToPlayState();
            return;
        }

        try {
            session = await client.live.music.connect({
                model: MODEL_NAME,
                callbacks: {
                    onmessage: handleServerMessage,
                    onerror: handleServerError,
                    onclose: handleServerClose,
                },
            });
            isConnecting = false;
            appendLog('Connected to generation session.');
            
            // Set state to playing *before* applying settings
            state.isPlaying = true;
            buildCodeString();
            await applySettingsToSession(); 

        } catch (error) {
            isConnecting = false;
            appendLog(`Connection failed: ${error.message}`, 'error');
            // Reset play button
            btnToPlayState();
            return;
        }
    }

    // Start playback
    await session.play();
    state.isPlaying = true; // Set state here again in case session already existed
    console.log('Streaming audio...');
    appendLog('Playback started.');
    buildCodeString();
}

// Pause button handle
async function handlePause() {
    if (!session) return;
    if (audioGainNode) audioGainNode.gain.value = 0;
    try {
        await session.pause();
        state.isPlaying = false;
        console.log('Playback paused.');
        appendLog('Playback paused.');
    } catch (error) {
        console.error(`Failed to pause: ${error.message}`, error);
        if (audioGainNode) audioGainNode.gain.value = pendingVolume;
    } 
}

// Stop button handler
async function handleStop() {
    if (!session) return;
    await session.stop();
    state.isPlaying = false;
    console.log('Playback stopped.');
    appendLog('Playback stopped.');
    
    btnToPlayState();

    await closeSession();
}
function createSlider(promptText) {
        const sliderId = `slider${Date.now()}`; // Use timestamp for unique ID
        const sliderRow = document.createElement('div');
        sliderRow.className = 'slider-row d-flex flex-wrap align-items-center justify-content-between gap-3';
        sliderRow.innerHTML = `
            <div class="d-flex align-items-center gap-2">
                <button class="btn btn-danger btn-sm remove-slider-btn" type="button">✖</button>
                <label for="${sliderId}" class="form-label mb-0">${promptText}</label>
            </div>
            <div class="flex-grow-1">
                <input type="range" class="form-range custom-slider" id="${sliderId}" min="0.1" max="3" step="0.1" value="1.0">
            </div>
        `;
        slidersList.appendChild(sliderRow);
}

// Send slider values to the console when changed
slidersList.addEventListener('input', (event) => {
    const target = event.target;
    if (target.type === 'range') {
        debouncedApplySettings();
    }
});

// Remove slider row when remove button is clicked
slidersList.addEventListener('click', (event) => {
    const btn = event.target.closest('.remove-slider-btn');
    if (!btn) return;

    const row = btn.closest('.slider-row');
    if (row) {
        row.remove();
        debouncedApplySettings(); 
    }

    if (slidersList.children.length === 0 && state.isPlaying) {
        closeSession();
        appendLog('All sliders removed. Closing session.');
        btnToPlayState();
        state.isPlaying = false;
    }
});

// Add new slider when add button is clicked
addSliderBtn.addEventListener('click', () => {
    const rawValue = promptInputField.value;
    if (!rawValue.trim()) {
        alert('Please enter a prompt.');
        return;
    }
    
    if (rawValue.includes(':')) {
        alert('Please enter only the prompt text (e.g., "Piano"). The weight is set by the slider.');
        return;
    }

    createSlider(rawValue.trim());
    promptInputField.value = '';
    debouncedApplySettings();
});

// Clear all sliders when clear button is clicked
clearBtn.addEventListener('click', async () => {
    slidersList.innerHTML = '';
    
    if (state.isPlaying) {
        await closeSession();
        appendLog('All sliders cleared. Closing session.');
        btnToPlayState();
        state.isPlaying = false;
    }
});

async function ensureAudioReady() {
    if (!audioContext) {
        const AudioContextCtor = window.AudioContext || window.webkitAudioContext;
        if (!AudioContextCtor) {
            appendLog('This browser does not support the Web Audio API.', 'error');
            throw new Error('Web Audio API unavailable');
        }
        try {
            audioContext = new AudioContextCtor({ sampleRate: SAMPLE_RATE });
        } catch (error) {
            console.warn('Falling back to default AudioContext sample rate:', error);
            audioContext = new AudioContextCtor();
        }
        audioGainNode = audioContext.createGain();
        audioGainNode.gain.value = pendingVolume;
        audioGainNode.connect(audioContext.destination);
        audioQueueTime = audioContext.currentTime;
    }
    if (audioContext.state === 'suspended') {
        await audioContext.resume();
    }
    updateVolume();
}
function updateVolume() {
    if (audioGainNode && audioContext && typeof pendingVolume === 'number') {
        audioGainNode.gain.setTargetAtTime(pendingVolume, audioContext.currentTime, 0.02);
    }
}

autoBpmCheckbox.addEventListener('change', async () => {
    await closeSession();
    appendLog('Auto BPM toggled, session reset.');
    btnToPlayState();
    state.isPlaying = false;
});

// Close session if BPM value changed
bpmRange.addEventListener('change', async () => {
    await closeSession();
    appendLog('BPM changed, session reset.');
    btnToPlayState();
    state.isPlaying = false;
});

// Close session if Scale changed
scaleSelect.addEventListener('change', async () => {
    await closeSession();
    appendLog('Scale changed, session reset.');
    btnToPlayState();
    state.isPlaying = false;
});


async function closeSession() {
    const activeSession = session;
    session = null;
    state.isPlaying = false;
    if (activeSession) {
        try {
            if (typeof activeSession.close === 'function') {
                await activeSession.close();
            } else if (typeof activeSession.disconnect === 'function') {
                await activeSession.disconnect();
            }
        } catch (error) {
            appendLog(`Session close warning: ${error.message}`, 'warn');
        }
    }
    state.activeConfig = {};
    state.activePrompts = [];
    if (audioContext) {
        try {
            await audioContext.close();
        } catch (error) {
            console.warn('Audio context close failed:', error);
        }
        audioContext = null;
        audioGainNode = null;
    }
}
function handleServerMessage(message) {
    const chunks = message?.serverContent?.audioChunks || [];
    if (chunks.length) {
        for (const chunk of chunks) {
            scheduleChunk(chunk);
        }
    }
    if (message?.serverContent?.sessionStatus) {
        const status = message.serverContent.sessionStatus;
        const summary = JSON.stringify(status);
        appendLog(`Session status: ${summary}`);
    }
    if (message?.serverContent?.error) {
        appendLog(`Server reported error: ${JSON.stringify(message.serverContent.error)}`, 'error');
    }
    if (message?.serverContent?.filteredPrompt) {
        appendLog(`Prompt filtered: ${message.serverContent.filteredPrompt}`.trim(), 'warn');
    }
}
function scheduleChunk(chunk) {
    if (!audioContext || !audioGainNode || !chunk?.data) return;
    if (chunk.format && chunk.format !== 'pcm16') {
        appendLog(`Unsupported audio format: ${chunk.format}`, 'warn');
        return;
    }
    const buffer = decodeBase64ToArrayBuffer(chunk.data)
    const pcm = new Int16Array(buffer);
    if (!pcm.length) return;
    const channelCount = 2;
    const frameCount = pcm.length / channelCount;
    const audioBuffer = audioContext.createBuffer(channelCount, frameCount, audioContext.sampleRate);
    for (let channel = 0; channel < channelCount; channel += 1) {
        const channelData = audioBuffer.getChannelData(channel);
        for (let i = 0; i < frameCount; i += 1) {
            const sample = pcm[i * channelCount + channel] / 32768;
            channelData[i] = Math.max(-1, Math.min(1, sample));
        }
    }
    const source = audioContext.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(audioGainNode);
    const startAt = Math.max(audioQueueTime, audioContext.currentTime + 0.05);
    source.start(startAt);
    audioQueueTime = startAt + audioBuffer.duration;
}
function decodeBase64ToArrayBuffer(data) {
    const binary = atob(data)
    const len = binary.length
    const bytes = new Uint8Array(len)
    for (let i = 0; i < len; i += 1) {
        bytes[i] = binary.charCodeAt(i)
    }
    return bytes.buffer
}
function handleServerError(error) {
    const details = serializeError(error)
    appendLog(`Session error: ${details}`, 'error');
}
function handleServerClose(event) {
    const description = describeCloseEvent(event);
    appendLog(`Session closed by server. ${description}`, 'warn');
    console.log('Session Closed.');
    session = null;
    state.isPlaying = false;
}
function appendLog(message, level = 'info') {
    const entry = document.createElement('div');
    entry.className = `log-entry log-${level}`;
    const timestamp = new Date().toLocaleTimeString()
    entry.textContent = `[${timestamp}] ${message}`;
    logEl.prepend(entry);
    logEntries.push(entry);
    if (logEntries.length > 100) {
        const old = logEntries.shift();
        old?.remove();
    }
}
function serializeError(error) {
    if (!error) return 'unknown error.';
    if (error instanceof Error) {
        const base = error.message;
        const extra = {};
        Object.getOwnPropertyNames(error).forEach((key) => {
            if (key === 'message' || key === 'stack') return;
            extra[key] = error[key];
        })
        return Object.keys(extra).length ? `${base} ${JSON.stringify(extra)}` : base;
    }
    if (typeof error === 'object') {
        try {
            return JSON.stringify(error);
        } catch (jsonError) {
            console.warn('Failed to stringify error payload', jsonError);
        }
    }
    return String(error);
}
function describeCloseEvent(event) {
    if (!event) return '';
    const parts = [];
    if (typeof event.code === 'number') {
        parts.push(`code=${event.code}`)
    }
    if (event.reason) {
        parts.push(`reason="${event.reason}"`);
    }
    if (event.wasClean !== undefined) {
        parts.push(`clean=${event.wasClean}`);
    }
    return parts.length ? `Details: ${parts.join(', ')}` : ''
}