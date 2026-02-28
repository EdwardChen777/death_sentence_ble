/**
 * Subtle chromatic emphasis on CTA hover
 */
document.querySelector('.cta-button')?.addEventListener('mouseenter', function () {
  this.style.setProperty('--chroma', '1');
});
document.querySelector('.cta-button')?.addEventListener('mouseleave', function () {
  this.style.setProperty('--chroma', '0.9');
});

/**
 * Frequency section: record / stop button, then transcribe via OpenAI and show below circle
 */
(function () {
  var recordBtn = document.getElementById('frequencyRecordBtn');
  var transcriptionEl = document.getElementById('frequencyTranscriptionText');
  var statusEl = document.getElementById('frequencyTranscriptionStatus');
  if (!recordBtn) return;

  var micIcon = recordBtn.querySelector('.record-mic-icon');
  var stopIcon = recordBtn.querySelector('.record-stop-icon');
  var recordLabel = recordBtn.querySelector('.record-label');
  var mediaRecorder = null;
  var stream = null;
  var chunks = [];

  // AI backend (e.g. uvicorn agents.app:app --port 8000)
  var API_BASE = window.FREQUENCY_API_BASE || 'http://localhost:8000';

  function setRecording(recording) {
    recordBtn.classList.toggle('recording', recording);
    recordBtn.setAttribute('aria-label', recording ? 'Stop recording' : 'Record audio');
    if (recordLabel) recordLabel.textContent = recording ? 'Stop' : 'Record';
  }

  function setStatus(text, isError) {
    if (!statusEl) return;
    statusEl.textContent = text;
    statusEl.style.color = isError ? 'rgba(255, 120, 120, 0.9)' : 'rgba(255, 255, 255, 0.5)';
  }

  function setTranscription(text) {
    if (transcriptionEl) transcriptionEl.textContent = text || '';
  }

  function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.stop();
    }
    if (stream) {
      stream.getTracks().forEach(function (t) { t.stop(); });
      stream = null;
    }
    setRecording(false);
  }

  function sendForTranscription(blob, mimeType) {
    setStatus('Transcribing…');
    setTranscription('');
    var form = new FormData();
    var ext = (mimeType || '').indexOf('webm') !== -1 ? 'webm' : 'ogg';
    form.append('audio', blob, 'recording.' + ext);

    fetch(API_BASE + '/transcribe', {
      method: 'POST',
      body: form
    })
      .then(function (res) {
        if (!res.ok) return res.json().then(function (body) { throw new Error(body.detail || res.statusText); });
        return res.json();
      })
      .then(function (data) {
        setTranscription(data.text || '');
        setStatus('');
      })
      .catch(function (err) {
        setStatus('Transcription failed: ' + (err.message || err));
        setTranscription('');
      });
  }

  recordBtn.addEventListener('click', function (e) {
    e.preventDefault();
    e.stopPropagation();
    if (recordBtn.classList.contains('recording')) {
      stopRecording();
      return;
    }

    chunks = [];
    setRecording(true);

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setRecording(false);
      if (window.alert) window.alert('Your browser does not support recording. Try Chrome or Firefox.');
      return;
    }

    navigator.mediaDevices.getUserMedia({ audio: true })
      .then(function (s) {
        stream = s;
        var options = { mimeType: 'audio/webm;codecs=opus' };
        if (!MediaRecorder.isTypeSupported(options.mimeType)) {
          options = {};
        }
        mediaRecorder = new MediaRecorder(stream, options);
        mediaRecorder.ondataavailable = function (ev) {
          if (ev.data.size > 0) chunks.push(ev.data);
        };
        mediaRecorder.onstop = function () {
          if (stream) {
            stream.getTracks().forEach(function (t) { t.stop(); });
            stream = null;
          }
          if (chunks.length) {
            var blob = new Blob(chunks, { type: mediaRecorder.mimeType || 'audio/webm' });
            sendForTranscription(blob, mediaRecorder.mimeType);
          }
        };
        mediaRecorder.start();
      })
      .catch(function (err) {
        console.warn('Recording not available:', err);
        setRecording(false);
        if (window.alert) {
          window.alert('Microphone access is needed to record. Please allow the site to use your microphone and try again.');
        }
      });
  });
})();
