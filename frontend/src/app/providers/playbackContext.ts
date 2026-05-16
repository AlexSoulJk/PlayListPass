import { createContext } from 'react'

export type PlaybackTrack = {
  id: string
  title: string
  artist: string
  coverUrl?: string | null
}

export type PlaybackContextValue = {
  currentTrack: PlaybackTrack | null
  isPlaying: boolean
  isHidden: boolean
  playTrack: (track: PlaybackTrack) => void
  pauseTrack: () => void
  resumeTrack: () => void
  stopTrack: () => void
  hidePlayer: () => void
}

export const PlaybackContext = createContext<PlaybackContextValue | null>(null)
