import { useMemo, useState, type PropsWithChildren } from 'react'
import { PlaybackContext, type PlaybackTrack } from './playbackContext'

export function PlaybackProvider({ children }: PropsWithChildren) {
  const [currentTrack, setCurrentTrack] = useState<PlaybackTrack | null>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [isHidden, setIsHidden] = useState(false)

  const playTrack = (track: PlaybackTrack) => {
    setCurrentTrack(track)
    setIsPlaying(true)
    setIsHidden(false)
  }

  const pauseTrack = () => {
    setIsPlaying(false)
  }

  const resumeTrack = () => {
    if (!currentTrack) {
      return
    }
    setIsPlaying(true)
  }

  const stopTrack = () => {
    setCurrentTrack(null)
    setIsPlaying(false)
    setIsHidden(false)
  }

  const hidePlayer = () => {
    setIsHidden(true)
  }

  const value = useMemo(
    () => ({
      currentTrack,
      isPlaying,
      isHidden,
      playTrack,
      pauseTrack,
      resumeTrack,
      stopTrack,
      hidePlayer,
    }),
    [currentTrack, isPlaying, isHidden],
  )

  return <PlaybackContext.Provider value={value}>{children}</PlaybackContext.Provider>
}
