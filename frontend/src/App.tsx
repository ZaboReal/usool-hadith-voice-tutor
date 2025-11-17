import { useState, useEffect, useRef } from 'react'
import {
  LiveKitRoom,
  RoomAudioRenderer,
  useVoiceAssistant,
  BarVisualizer,
  useRoomContext,
} from '@livekit/components-react'
import { RoomEvent, TranscriptionSegment } from 'livekit-client'
import './App.css'

interface TranscriptMessage {
  speaker: 'user' | 'assistant'
  content: string
  timestamp: Date
  isFinal: boolean
}

function VoiceAssistantUI() {
  const [transcript, setTranscript] = useState<TranscriptMessage[]>([])
  const [currentUtterance, setCurrentUtterance] = useState<string>('')
  const [currentSpeaker, setCurrentSpeaker] = useState<'user' | 'assistant'>('user')
  const transcriptEndRef = useRef<HTMLDivElement>(null)
  const room = useRoomContext()
  const { state, audioTrack } = useVoiceAssistant()

  // Auto-scroll to bottom of transcript
  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [transcript, currentUtterance])

  // Listen for agent transcriptions
  useEffect(() => {
    if (!room) return

    // Handle agent transcriptions (what the agent is saying)
    const handleAgentTranscription = (
      segments: TranscriptionSegment[],
      participant: any
    ) => {
      const isAgent = participant?.identity === 'agent' || participant?.name?.includes('agent')

      segments.forEach((segment) => {
        const text = segment.text.trim()
        if (!text) return

        if (segment.final) {
          // Final transcription - add to transcript
          setTranscript((prev) => [
            ...prev,
            {
              speaker: isAgent ? 'assistant' : 'user',
              content: text,
              timestamp: new Date(),
              isFinal: true,
            },
          ])
          setCurrentUtterance('')
        } else {
          // Interim transcription - show as current utterance
          setCurrentUtterance(text)
          setCurrentSpeaker(isAgent ? 'assistant' : 'user')
        }
      })
    }

    // Listen for transcription events
    room.on(RoomEvent.TranscriptionReceived, handleAgentTranscription)

    // Also listen for local participant (user) transcriptions
    const localParticipant = room.localParticipant
    if (localParticipant) {
      localParticipant.on(RoomEvent.LocalTrackPublished, (publication) => {
        if (publication.track?.kind === 'audio') {
          console.log('Local audio track published')
        }
      })
    }

    return () => {
      room.off(RoomEvent.TranscriptionReceived, handleAgentTranscription)
    }
  }, [room])

  return (
    <div className="voice-ui">
      <div className="status connected">
        <strong>Status:</strong> {state}
      </div>

      {audioTrack && (
        <div style={{ marginBottom: '1.5rem' }}>
          <BarVisualizer
            state={state}
            barCount={5}
            trackRef={audioTrack}
            className="visualizer"
          />
        </div>
      )}

      <div className="transcript-container">
        <h2>Live Transcript</h2>
        <div className="transcript">
          {transcript.length === 0 && !currentUtterance ? (
            <div className="empty-state">
              Conversation will appear here...
            </div>
          ) : (
            <>
              {transcript.map((msg, idx) => (
                <div key={idx} className={`transcript-message ${msg.speaker}`}>
                  <div className="speaker">
                    {msg.speaker === 'user' ? 'You' : 'Usuli'}
                  </div>
                  <div className="content">{msg.content}</div>
                </div>
              ))}
              {currentUtterance && (
                <div className={`transcript-message ${currentSpeaker} interim`}>
                  <div className="speaker">
                    {currentSpeaker === 'user' ? 'You' : 'Usuli'}
                  </div>
                  <div className="content" style={{ opacity: 0.7, fontStyle: 'italic' }}>
                    {currentUtterance}
                  </div>
                </div>
              )}
            </>
          )}
          <div ref={transcriptEndRef} />
        </div>
      </div>
    </div>
  )
}

function App() {
  const [token, setToken] = useState<string>('')
  const [isConnecting, setIsConnecting] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<string>('')

  const livekitUrl = import.meta.env.VITE_LIVEKIT_URL
  const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8080'

  const handleStartCall = async () => {
    setIsConnecting(true)
    setError('')

    try {
      // Get token from backend
      const response = await fetch(`${backendUrl}/token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          identity: `user-${Math.random().toString(36).substring(7)}`,
          roomName: 'hadith-voice-room',
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to get token from backend')
      }

      const data = await response.json()
      setToken(data.token)
      setIsConnected(true)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Failed to connect. Make sure the backend is running.'
      )
      setIsConnecting(false)
    }
  }

  const handleEndCall = () => {
    setToken('')
    setIsConnected(false)
    setIsConnecting(false)
  }

  const handleRoomConnected = () => {
    setIsConnecting(false)
  }

  const handleRoomDisconnected = () => {
    setIsConnected(false)
    setToken('')
  }

  return (
    <div className="app">
      <div className="header">
        <h1>USOOL AL-HADITH</h1>
        <p>Voice Tutor • Usuli • AI-Powered Learning</p>
      </div>

      <div className="container">
        {!isConnected && !isConnecting && (
          <>
            <div className="controls">
              <button
                className="btn btn-primary"
                onClick={handleStartCall}
                disabled={isConnecting}
              >
                Start Learning Session
              </button>
            </div>

            {error && (
              <div className="status disconnected">
                <strong>Error:</strong> {error}
              </div>
            )}

            <div className="transcript-container">
              <h2>Ready to Learn</h2>
              <div className="about-content">
                <p>
                  AI-powered Islamic scholarship system.
                  Usuli is ready to teach you:
                </p>
                <ul>
                  <li>Hadith Terminology & Classifications</li>
                  <li>Chain of Narration (Isnad) Analysis</li>
                  <li>Narrator Criticism (Ilm al-Rijal)</li>
                  <li>Authentication Methodologies</li>
                  <li>Usool al-Hadith Deep Dives</li>
                </ul>
                <div className="cta">
                  ▸ CLICK START TO BEGIN VOICE SESSION
                </div>
              </div>
            </div>
          </>
        )}

        {isConnecting && (
          <div className="status connecting">
            Connecting to Sheikh Abdullah...
          </div>
        )}

        {isConnected && token && (
          <>
            <div className="controls">
              <button
                className="btn btn-danger"
                onClick={handleEndCall}
              >
                End Session
              </button>
            </div>

            <LiveKitRoom
              token={token}
              serverUrl={livekitUrl}
              connect={true}
              audio={true}
              video={false}
              onConnected={handleRoomConnected}
              onDisconnected={handleRoomDisconnected}
            >
              <VoiceAssistantUI />
              <RoomAudioRenderer />
            </LiveKitRoom>
          </>
        )}
      </div>
    </div>
  )
}

export default App
