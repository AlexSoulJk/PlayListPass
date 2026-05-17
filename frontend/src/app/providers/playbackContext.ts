import { createContext } from 'react'

export type PlaybackTrack = {
  id: string
  title: string
  artist: string
  coverUrl?: string | null
  audioUrl: string
}

export type PlayTrackOptions = {
  audio?: HTMLAudioElement
  queue?: PlaybackTrack[]
  startIndex?: number
  volume?: number
}

export type PlaybackContextValue = {
  currentTrack: PlaybackTrack | null
  isPlaying: boolean
  isHidden: boolean
  volume: number
  canPlayPrevious: boolean
  canPlayNext: boolean
  playTrack: (track: PlaybackTrack, options?: PlayTrackOptions) => void
  playPreviousTrack: () => void
  playNextTrack: () => void
  pauseTrack: () => void
  resumeTrack: () => void
  stopTrack: () => void
  hidePlayer: () => void
  setVolume: (nextVolume: number) => void
}

export const PlaybackContext = createContext<PlaybackContextValue | null>(null)
