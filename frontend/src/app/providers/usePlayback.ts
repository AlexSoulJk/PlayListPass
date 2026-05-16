import { useContext } from 'react'
import { PlaybackContext } from './playbackContext'

export const usePlayback = () => {
  const value = useContext(PlaybackContext)
  if (!value) {
    throw new Error('usePlayback must be used within PlaybackProvider')
  }
  return value
}
