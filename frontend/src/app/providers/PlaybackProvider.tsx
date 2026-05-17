import { useEffect, useMemo, useRef, useState, type PropsWithChildren } from 'react'
import { PlaybackContext, type PlayTrackOptions, type PlaybackTrack } from './playbackContext'

const DEFAULT_VOLUME = 0.75

const clampVolume = (value: number): number => {
  if (Number.isNaN(value)) {
    return DEFAULT_VOLUME
  }
  return Math.min(1, Math.max(0, value))
}

export function PlaybackProvider({ children }: PropsWithChildren) {
  const [currentTrack, setCurrentTrack] = useState<PlaybackTrack | null>(null)
  const [playbackQueue, setPlaybackQueue] = useState<PlaybackTrack[]>([])
  const [currentIndex, setCurrentIndex] = useState(-1)
  const [isPlaying, setIsPlaying] = useState(false)
  const [isHidden, setIsHidden] = useState(false)
  const [volume, setVolumeState] = useState(DEFAULT_VOLUME)
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const detachAudioListenersRef = useRef<(() => void) | null>(null)

  const detachAudioListeners = () => {
    if (!detachAudioListenersRef.current) {
      return
    }
    detachAudioListenersRef.current()
    detachAudioListenersRef.current = null
  }

  const releaseCurrentAudio = () => {
    detachAudioListeners()
    const currentAudio = audioRef.current
    if (!currentAudio) {
      return
    }
    currentAudio.pause()
    currentAudio.removeAttribute('src')
    currentAudio.load()
    audioRef.current = null
  }

  const bindAudioListeners = (audio: HTMLAudioElement) => {
    const handlePlay = () => setIsPlaying(true)
    const handlePause = () => setIsPlaying(false)
    const handleEnded = () => setIsPlaying(false)
    const handleError = () => setIsPlaying(false)

    audio.addEventListener('play', handlePlay)
    audio.addEventListener('pause', handlePause)
    audio.addEventListener('ended', handleEnded)
    audio.addEventListener('error', handleError)

    detachAudioListenersRef.current = () => {
      audio.removeEventListener('play', handlePlay)
      audio.removeEventListener('pause', handlePause)
      audio.removeEventListener('ended', handleEnded)
      audio.removeEventListener('error', handleError)
    }
  }

  const startPlayback = (track: PlaybackTrack, audio: HTMLAudioElement) => {
    audioRef.current = audio
    bindAudioListeners(audio)
    setCurrentTrack(track)
    setIsHidden(false)
    void audio.play().catch(() => {
      setIsPlaying(false)
    })
  }

  const playQueueTrackAtIndex = (index: number) => {
    if (index < 0 || index >= playbackQueue.length) {
      return
    }
    const track = playbackQueue[index]
    if (!track.audioUrl) {
      return
    }

    releaseCurrentAudio()
    const nextAudio = new Audio(track.audioUrl)
    nextAudio.preload = 'auto'
    nextAudio.currentTime = 0
    nextAudio.volume = volume
    setCurrentIndex(index)
    startPlayback(track, nextAudio)
  }

  const playTrack = (track: PlaybackTrack, options?: PlayTrackOptions) => {
    if (!track.audioUrl) {
      return
    }

    const nextQueue = options?.queue && options.queue.length > 0 ? options.queue : [track]
    const resolvedIndex = (() => {
      if (
        typeof options?.startIndex === 'number' &&
        options.startIndex >= 0 &&
        options.startIndex < nextQueue.length
      ) {
        return options.startIndex
      }
      const matchIndex = nextQueue.findIndex((item) => item.id === track.id)
      return matchIndex >= 0 ? matchIndex : 0
    })()
    const nextTrack = nextQueue[resolvedIndex]
    if (!nextTrack?.audioUrl) {
      return
    }

    const nextVolume = clampVolume(options?.volume ?? volume)
    if (nextVolume !== volume) {
      setVolumeState(nextVolume)
    }

    releaseCurrentAudio()

    const canReuseProvidedAudio =
      Boolean(options?.audio) &&
      track.id === nextTrack.id &&
      track.audioUrl === nextTrack.audioUrl

    const nextAudio = canReuseProvidedAudio ? (options?.audio as HTMLAudioElement) : new Audio(nextTrack.audioUrl)
    nextAudio.preload = 'auto'
    nextAudio.currentTime = 0
    nextAudio.volume = nextVolume
    setPlaybackQueue(nextQueue)
    setCurrentIndex(resolvedIndex)
    startPlayback(nextTrack, nextAudio)
  }

  const playPreviousTrack = () => {
    playQueueTrackAtIndex(currentIndex - 1)
  }

  const playNextTrack = () => {
    playQueueTrackAtIndex(currentIndex + 1)
  }

  const pauseTrack = () => {
    const currentAudio = audioRef.current
    if (!currentAudio) {
      return
    }
    currentAudio.pause()
  }

  const resumeTrack = () => {
    if (!currentTrack || !audioRef.current) {
      return
    }
    void audioRef.current.play().catch(() => {
      setIsPlaying(false)
    })
  }

  const stopTrack = () => {
    releaseCurrentAudio()
    setCurrentTrack(null)
    setPlaybackQueue([])
    setCurrentIndex(-1)
    setIsPlaying(false)
    setIsHidden(false)
  }

  const hidePlayer = () => {
    setIsHidden(true)
  }

  const setVolume = (nextVolume: number) => {
    const normalized = clampVolume(nextVolume)
    setVolumeState(normalized)
    if (audioRef.current) {
      audioRef.current.volume = normalized
    }
  }

  useEffect(() => {
    return () => {
      releaseCurrentAudio()
    }
  }, [])

  const value = useMemo(
    () => ({
      currentTrack,
      isPlaying,
      isHidden,
      volume,
      canPlayPrevious: currentIndex > 0,
      canPlayNext: currentIndex >= 0 && currentIndex < playbackQueue.length - 1,
      playTrack,
      playPreviousTrack,
      playNextTrack,
      pauseTrack,
      resumeTrack,
      stopTrack,
      hidePlayer,
      setVolume,
    }),
    [currentTrack, isPlaying, isHidden, volume, currentIndex, playbackQueue.length],
  )

  return <PlaybackContext.Provider value={value}>{children}</PlaybackContext.Provider>
}
