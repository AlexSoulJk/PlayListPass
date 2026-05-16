import { usePlayback } from '../../../app/providers/usePlayback'
import styles from './GlobalPlayer.module.css'

export function GlobalPlayer() {
  const { currentTrack, isPlaying, hidePlayer, pauseTrack, resumeTrack } = usePlayback()

  if (!currentTrack) {
    return null
  }

  return (
    <section aria-label="Глобальный плеер" className={styles.root}>
      <button aria-label="Скрыть плеер" className={styles.hideButton} onClick={hidePlayer} type="button">
        ×
      </button>

      <div className={styles.track}>
        <div
          aria-hidden
          className={styles.cover}
          style={currentTrack.coverUrl ? { backgroundImage: `url(${currentTrack.coverUrl})` } : undefined}
        />
        <div className={styles.meta}>
          <p className={styles.title}>{currentTrack.title}</p>
          <p className={styles.artist}>{currentTrack.artist}</p>
        </div>
      </div>

      <div className={styles.controls}>
        {isPlaying ? (
          <button aria-label="Пауза" className={styles.controlButton} onClick={pauseTrack} type="button">
            ❚❚
          </button>
        ) : (
          <button aria-label="Воспроизвести" className={styles.controlButton} onClick={resumeTrack} type="button">
            ▶
          </button>
        )}
      </div>
    </section>
  )
}
